import pandas as pd

import logging
from volatility_mitigation import VolatilityMitigator
from transactions import BurnTransaction, MintTransaction, SwapTransaction
import blockchain
from settings import PRICE_TOLLERANCE_THRESHOLD
from big_numbers import expand_to_18_decimals
from safe_math import q_div, q_encode
import dsw_oracle

logger = logging.getLogger(__name__)


class AMM:
    def __init__(self, X: str, Y: str, reserve_X: int, reserve_Y: int, is_volatility_mitigator_on: bool) -> None:
        self.volatility_mitigator = VolatilityMitigator(PRICE_TOLLERANCE_THRESHOLD)
        self.X = X
        self.Y = Y
        self.reserve_X = expand_to_18_decimals(reserve_X)
        self.reserve_Y = expand_to_18_decimals(reserve_Y)
        self.price_X_cumulative_last = int(0)
        self.price_Y_cumulative_last = int(0)
        self.k_last = reserve_X * reserve_Y # todo: update k_last in execute transaction
        self.is_volatility_mitigator_on = is_volatility_mitigator_on
        self.start_time = None
        self.block_timestamp_last = None 

        self.pool_before_swap_list = []
        self.pool_after_swap_list = []

       # self.save_config() todo: uncomment and verify

    
    def reset(self, X, Y, reserve0_X, reserve0_Y, is_volatility_mitigator_on, window_size, period_size, granularity):
        self.X = X
        self.Y = Y
        self.reserve_X = expand_to_18_decimals(reserve0_X)
        self.reserve_Y = expand_to_18_decimals(reserve0_Y)
        self.price_X_cumulative_last = int(0)
        self.price_Y_cumulative_last = int(0)
        self.k_last = self.reserve_X * self.reserve_Y
        self.is_volatility_mitigator_on = is_volatility_mitigator_on
        self.start_time = None
        self.block_timestamp_last = None

        self.pool_before_swap_list = []
        self.pool_after_swap_list = []

        dsw_oracle.reset(window_size, period_size, granularity)

       # self.save_config()


    
    def get_X(self):
        return self.X

    def get_Y(self):
        return self.Y

    def get_reserve_X(self):
        return self.reserve_X

    def get_reserve_Y(self):
        return self.reserve_Y

    
    def current_cumulative_prices(self, current_block_timestamp: int):
        if self.block_timestamp_last != current_block_timestamp:
            time_elapsed = current_block_timestamp - self.block_timestamp_last
            
            self.price_X_cumulative_last += q_div(q_encode(self.reserve_Y), self.reserve_X) * time_elapsed
            self.price_Y_cumulative_last += q_div(q_encode(self.reserve_X), self.reserve_Y) * time_elapsed

            self.block_timestamp_last = current_block_timestamp # TODO: ?
        
        return self.price_X_cumulative_last, self.price_Y_cumulative_last


    def swap(self, id, transaction):
        swap_transaction = SwapTransaction(transaction, self, id)
        
        blockchain.receive_transaction(swap_transaction)

    
    def mint(self, amount_X, amount_Y, timestamp, id):
        mint_transaction = MintTransaction(amount_X, amount_Y, timestamp, self, id)

        blockchain.receive_transaction(mint_transaction)


    def burn(self, amount_X, amount_Y, timestamp, id):
        burn_transaction = BurnTransaction(amount_X, amount_Y, timestamp, self, id)

        blockchain.receive_transaction(burn_transaction)


    def save_pool_state(self, before_swap: bool, transaction_id: int):
        if before_swap:
            list = self.pool_before_swap_list
        else:
            list = self.pool_after_swap_list

        list.append([transaction_id, self.reserve_X, self.reserve_Y, self.k_last, self.price_X_cumulative_last, self.price_Y_cumulative_last, self.is_volatility_mitigator_on])



    def export_pool_states_to_csv(self, filename_before, filename_after):
        before_df = pd.DataFrame(self.pool_before_swap_list, columns=['transaction_id', 'reserve_X', 'reserve_Y', 'k', 'price_X_cumulative', 
                                                                        'price_Y_cumulative', 'is_volatility_mitigator_on'])

        after_df = pd.DataFrame(self.pool_after_swap_list, columns=['transaction_id', 'reserve_X', 'reserve_Y', 'k', 'price_X_cumulative', 
                                                                        'price_Y_cumulative', 'is_volatility_mitigator_on'])

        before_df.to_csv(filename_before, index=False)
        after_df.to_csv(filename_after, index=False)



    def update_reserve_X(self, delta: int):
        if self.reserve_X + delta < 0:
            raise Exception(f"Cannot update reserve X, reserve_X = {self.reserve_X}, delta = {delta}")

        self.reserve_X += delta
        self.k_last = self.reserve_X * self.reserve_Y


    def update_reserve_Y(self, delta: int):
        if self.reserve_Y + delta < 0:
            raise Exception(f"Cannot update reserve Y, reserve_Y = {self.reserve_Y}, delta = {delta}")

        self.reserve_Y += delta
        self.k_last = self.reserve_X * self.reserve_Y


    def update_pair(self, block_timestamp): # todo: remove duplicate code (from current_acc_prices)
        # true only on first function call
        if self.block_timestamp_last == None:
            self.block_timestamp_last = block_timestamp
            self.start_time = block_timestamp

        time_elapsed = block_timestamp - self.block_timestamp_last

        if time_elapsed > 0:
            self.price_X_cumulative_last += q_div(q_encode(self.reserve_Y), self.reserve_X) * time_elapsed
            self.price_Y_cumulative_last += q_div(q_encode(self.reserve_X), self.reserve_Y) * time_elapsed

        self.block_timestamp_last = block_timestamp # TODO: maybe remove blocktimestamplast assign in get method


    def save_config(self, filename):
        with open(filename, 'w') as f:
            f.write(f"X = `{self.X}`\n")
            f.write(f"Y = `{self.Y}`\n")
            f.write(f"reserve_X = `{self.reserve_X}`\n")
            f.write(f"reserve_Y = `{self.reserve_Y}`\n")
            f.write(f"is_volatility_mitigator_on = `{self.is_volatility_mitigator_on}`")
 

_amm = AMM("X", "Y", 800000, 800000, True)


current_cumulative_prices = _amm.current_cumulative_prices
swap = _amm.swap
X = _amm.get_X
Y = _amm.get_Y
reserve_X = _amm.get_reserve_X
reserve_Y = _amm.get_reserve_Y
save_pool_state = _amm.save_pool_state
export_pool_states_to_csv = _amm.export_pool_states_to_csv
reset = _amm.reset
mint = _amm.mint
burn = _amm.burn
