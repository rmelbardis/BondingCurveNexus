#-------------------------------------------------------------#
# Define dictionary of fixed system parameters for simulation #
#-------------------------------------------------------------#


# NEXUSTRACKER VALUES TODAY - UPDATES REQUIRED REGULARLY #
# TODO: pull these in automatically
nxm_supply_now = 6_789_404
act_cover_now = 242_684
cap_pool_now = 153_417

# SYSTEM PARAMETERS - CURRENT FIXED BUT MAY BE SUBJECT TO CHANGE #
capital_factor = 4.8

# NEW TOKENOMIC PARAMETERS #
# when MCR% < 1, duration in days for bond with extra interest
entry_bond_length = 30

# minimum duration in days before users can get funds out
minimum_exit_period = 14

# number of days after reaching 100% book value that option can be used
option_exit_period = 30
# cost of option if not exercised
option_cost = 0.1

# when MCR% <=1, durations in days
# to 100% book value for withdrawing ETH for NXM
#
# base value - minimum duration to 100% book value
base_exit_days = 60
# maximum days linked to MCR%
mcrp_max_days = 153
# maximum days linked to relative size of exit queue
queue_max_days = 153
