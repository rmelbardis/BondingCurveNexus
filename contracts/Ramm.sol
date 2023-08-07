// SPDX-License-Identifier: GPL-3.0-only

pragma solidity ^0.8.18;

import "./CapitalPool.sol";
import "./NXM.sol";

contract Ramm {

  struct Pool {
    uint nxm;
    uint liqSpeed;
    uint ratchetSpeed;
  }

  Pool public a;
  Pool public b;

  uint public eth;
  uint public targetLiquidity;
  uint public lastSwapTimestamp;
  uint public budget;
  uint public aggressiveLiqSpeed;

  NXM public nxm;
  CapitalPool public capitalPool;

  uint public constant LIQ_SPEED_PERIOD = 1 days;
  uint public constant RATCHET_PERIOD = 1 days;
  uint public constant RATCHET_DENOMINATOR = 10_000;
  uint public constant BUFFER_ZONE = 1_000 ether;
  uint public constant PRICE_BUFFER = 100;
  uint public constant PRICE_BUFFER_DENOMINATOR = 10_000;

  constructor (NXM _nxm, CapitalPool _capitalPool) {
    // middle price: 0.02 ether
    // bv          : 0.0214 ether
    // RM: changing these to reflect likely opening params for transition from BC for internal price
    uint price_a = 0.03566 ether;
    uint price_b = 0.01418 ether;

    eth = 10000 ether;
    targetLiquidity = 10000 ether;
    lastSwapTimestamp = block.timestamp;

    budget = 0 ether;
    aggressiveLiqSpeed = 1000 ether;

    a.nxm = eth * 1 ether / price_a;
    a.liqSpeed = 400 ether;
    a.ratchetSpeed = 400;

    b.nxm = eth * 1 ether / price_b;
    b.liqSpeed = 400 ether;
    b.ratchetSpeed = 400;

    nxm = _nxm;
    capitalPool = _capitalPool;
  }

  function min(uint x, uint y) internal pure returns (uint) {
    return x < y ? x : y;
  }

  function swap(uint nxmIn) external payable {

    require(msg.value == 0 || nxmIn == 0, "ONE_INPUT_ONLY");
    require(msg.value > 0 || nxmIn > 0, "ONE_INPUT_REQUIRED");

    msg.value > 0
      ? swapEthForNxm(msg.value, msg.sender)
      : swapNxmForEth(nxmIn, msg.sender);
  }

  function swapEthForNxm(uint ethIn, address to) internal returns (uint nxmOut) {
    (uint eth_new, uint nxm_a, uint nxm_b, uint new_budget) = getReserves();
    uint k = eth_new * nxm_a;
    eth = eth_new + ethIn;

    // edge case: bellow goes over bv due to eth-dai price changing
    a.nxm = k / eth;
    b.nxm = nxm_b * eth / eth_new;
    budget = new_budget;
    lastSwapTimestamp = block.timestamp;
    nxmOut = nxm_a - a.nxm;

    // transfer assets
    uint cap_before = capitalPool.getPoolValueInEth();
    uint sup_before = nxm.totalSupply();
    uint bv_before = 1e18 * cap_before / sup_before;

    (bool ok,) = address(capitalPool).call{value: msg.value}("");
    require(ok, "CAPITAL_POOL_TRANSFER_FAILED");
    nxm.mint(to, nxmOut);


    uint cap_after = capitalPool.getPoolValueInEth();
    uint sup_after = nxm.totalSupply();
    uint bv_after = 1e18 * cap_after / sup_after;

    return nxmOut;
  }

  function getReserves() public view returns (uint eth_new, uint nxm_a, uint nxm_b, uint new_budget) {
    uint capital = capitalPool.getPoolValueInEth();
    uint supply = nxm.totalSupply();

    // uint mcr = capitalPool.mcr();
    // TODO: check for capital > mcr + buffer
    // oracle

    eth_new = eth;
    new_budget = budget;
    uint elapsed = block.timestamp - lastSwapTimestamp;

    if (eth_new < targetLiquidity) {
      // inject liquidity
      uint timeLeftOnBudget = budget * LIQ_SPEED_PERIOD / aggressiveLiqSpeed;
      uint maxInjectedAmount = targetLiquidity - eth_new;
      uint injectedAmount;

      if (elapsed <= timeLeftOnBudget) {

        injectedAmount = min(
          elapsed * aggressiveLiqSpeed / LIQ_SPEED_PERIOD,
          maxInjectedAmount
        );

        new_budget -= injectedAmount;

      } else {

        uint injectedAmountOnBudget = timeLeftOnBudget * aggressiveLiqSpeed / LIQ_SPEED_PERIOD;
        new_budget = maxInjectedAmount < injectedAmountOnBudget ? new_budget - maxInjectedAmount : 0;

        uint injectedAmountWoBudget = (elapsed - timeLeftOnBudget) * b.liqSpeed / LIQ_SPEED_PERIOD;
        injectedAmount = min(maxInjectedAmount, injectedAmountOnBudget + injectedAmountWoBudget);
      }

      eth_new += injectedAmount;

    } else {
      // extract liquidity
      uint extractedAmount = min(
        elapsed * a.liqSpeed / LIQ_SPEED_PERIOD,
        eth_new - targetLiquidity // diff to target
      );

      eth_new -= extractedAmount;
    }

    // pi = eth / nxm
    // pf = eth_new / nxm_new
    // pf = eth_new /(nxm * eth_new / eth)
    // nxm_new = nxm * eth_new / eth
    nxm_a = a.nxm * eth_new / eth;
    nxm_b = b.nxm * eth_new / eth;

    // apply ratchet above
    {
      // if cap*n*(1+r) > e*sup
      // if cap*n + cap*n*r > e*sup
      //   set n(new) = n(BV)
      // else
      //   set n(new) = n(R)
      uint r = elapsed * a.ratchetSpeed;
      uint bufferedCapitalA = capital * (PRICE_BUFFER_DENOMINATOR + PRICE_BUFFER) / PRICE_BUFFER_DENOMINATOR;

      if (bufferedCapitalA * nxm_a + capital * nxm_a * r / RATCHET_PERIOD / RATCHET_DENOMINATOR > eth_new * supply) {
        // use bv
        nxm_a = eth_new * supply / bufferedCapitalA;
      } else {
        // use ratchet
        uint nr_denom_addend = r * capital * nxm_a / supply / RATCHET_PERIOD / RATCHET_DENOMINATOR;
        nxm_a = eth_new * nxm_a / (eth_new - nr_denom_addend);
      }
    }

    // apply ratchet below
    {
      // check if we should be using the ratchet or the book value price using:
      // Nbv > Nr <=>
      // ... <=>
      // cap * n < e * sup + r * cap * n
      uint bufferedCapitalB = capital * (PRICE_BUFFER_DENOMINATOR - PRICE_BUFFER) / PRICE_BUFFER_DENOMINATOR;

      if (
        bufferedCapitalB * nxm_b < eth_new * supply + nxm_b * capital * elapsed * b.ratchetSpeed / RATCHET_PERIOD / RATCHET_DENOMINATOR
      ) {
        nxm_b = eth_new * supply / bufferedCapitalB;
      } else {
        uint nr_denom_addend = nxm_b * elapsed * b.ratchetSpeed * capital / supply / RATCHET_PERIOD / RATCHET_DENOMINATOR;
        nxm_b = eth_new * nxm_b / (eth_new + nr_denom_addend);
      }
    }


    return (eth_new, nxm_a, nxm_b, new_budget);
  }

  function swapNxmForEth(uint nxmIn, address to) internal returns (uint ethOut) {

    (uint eth_new, uint nxm_a, uint nxm_b, uint new_budget) = getReserves();


    uint k = eth_new * nxm_b;
    b.nxm = nxm_b  + nxmIn;
    a.nxm = nxm_b  + nxmIn;

    eth = k / b.nxm;

    a.nxm = nxm_a * eth / eth_new;
    budget = new_budget;
    lastSwapTimestamp = block.timestamp;
    ethOut = eth_new - eth;

    uint cap_before = capitalPool.getPoolValueInEth();
    uint sup_before = nxm.totalSupply();
    uint bv_before = 1e18 * cap_before / sup_before;


    nxm.burn(msg.sender, nxmIn);
    capitalPool.sendEth(payable(to), ethOut);

    uint mcr = capitalPool.mcr();
    uint cap_after = capitalPool.getPoolValueInEth();
    uint sup_after = nxm.totalSupply();
    uint bv_after = 1e18 * cap_after / sup_after;

    if (cap_after < mcr + BUFFER_ZONE) {
      revert("NO_SWAPS_IN_BUFFER_ZONE");
    }



    return ethOut;
  }

  function getSpotPriceA() external view returns (uint /*ethPerNxm*/) {
    (uint eth_new, uint nxm_a, /*uint nxm_b*/, /*uint new_budget*/) = getReserves();
    return 1 ether * eth_new / nxm_a;
  }

  function getSpotPriceB() external view returns (uint /*ethPerNxm*/) {
    (uint eth_new, /*uint nxm_a*/, uint nxm_b, /*uint new_budget*/) = getReserves();
    return 1 ether * eth_new / nxm_b;
  }

  function getSpotPrices() external view returns (uint /*ethPerNxm*/, uint) {
    (uint eth_new, uint nxm_a, uint nxm_b, /*uint new_budget*/) = getReserves();
    return (1 ether * eth_new / nxm_a, 1 ether * eth_new / nxm_b);
  }
}
