FROM ubuntu:jammy

RUN apt-get update && apt-get install -y curl git
RUN curl -sqL https://foundry.paradigm.xyz | bash && $HOME/.foundry/bin/foundryup

ENTRYPOINT $HOME/.foundry/bin/anvil --host 0.0.0.0
