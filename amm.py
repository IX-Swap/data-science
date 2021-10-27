import pandas as pd

import logging
from volatility_mitigation import VolatilityMitigator
from transactions import SwapTransaction
import blockchain
from settings import PRICE_TOLLERANCE_THRESHOLD

logger = logging.getLogger(__name__)


class AMM:
    def __init__(self, X: str, Y: str, reserve_X: float, reserve_Y: float, is_volatility_mitigator_on: bool) -> None:
        self.volatility_mitigator = VolatilityMitigator(PRICE_TOLLERANCE_THRESHOLD)
        self.X = X
        self.Y = Y
        self.reserve_X = reserve_X
        self.reserve_Y = reserve_Y
        self.price_X_cumulative_last = 0
        self.price_Y_cumulative_last = 0
        self.k_last = reserve_X * reserve_Y # todo: update k_last in execute transaction
        self.is_volatility_mitigator_on = is_volatility_mitigator_on
        self.start_time = None
        self.block_timestamp_last = None 

        self.pool_before_swap_list = []
        self.pool_after_swap_list = []

    
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
            
            self.price_X_cumulative_last += self.reserve_Y / self.reserve_X * time_elapsed 
            self.price_Y_cumulative_last += self.reserve_X / self.reserve_Y * time_elapsed

         #   print(time_elapsed)

            self.block_timestamp_last = current_block_timestamp # TODO: ?
        
        return self.price_X_cumulative_last, self.price_Y_cumulative_last


    def swap(self, id, transaction):
        swap_transaction = SwapTransaction(transaction, self, id)
        
        blockchain.receive_transaction(swap_transaction)

    def save_pool_state(self, before_swap: bool, transaction_id: int):
        if before_swap:
            list = self.pool_before_swap_list
        else:
            list = self.pool_after_swap_list

        list.append([transaction_id, self.reserve_X, self.reserve_Y, self.k_last, self.price_X_cumulative_last, self.price_Y_cumulative_last, self.is_volatility_mitigator_on])



    def export_pool_states_to_csv(self):
        before_df = pd.DataFrame(self.pool_before_swap_list, columns=['transaction_id', 'reserve_X', 'reserve_Y', 'k', 'price_X_cumulative', 
                                                                        'price_Y_cumulative', 'is_volatility_mitigator_on'])

        after_df = pd.DataFrame(self.pool_after_swap_list, columns=['transaction_id', 'reserve_X', 'reserve_Y', 'k', 'price_X_cumulative', 
                                                                        'price_Y_cumulative', 'is_volatility_mitigator_on'])

        before_df.to_csv('data/before_pool.csv', index=False)
        after_df.to_csv('data/after_pool.csv', index=False)


    def update_reserve_X(self, delta: float):
        if self.reserve_X + delta < 0:
            raise Exception(f"Cannot update reserve X, reserve_X = {self.reserve_X}, delta = {delta}")

       # logger.error(f"Update reserve X {self.reserve_X}, delta={delta}")
        self.reserve_X += delta
        self.k_last = self.reserve_X * self.reserve_Y


    def update_reserve_Y(self, delta: float):
        if self.reserve_Y + delta < 0:
            raise Exception(f"Cannot update reserve Y, reserve_Y = {self.reserve_Y}, delta = {delta}")

        self.reserve_Y += delta
        self.k_last = self.reserve_X * self.reserve_Y


    def update_pair(self, block_timestamp):
        # true only on first function call
        if self.block_timestamp_last == None:
            self.block_timestamp_last = block_timestamp
            self.start_time = block_timestamp

        time_elapsed = block_timestamp - self.block_timestamp_last

        if time_elapsed > 0:
            self.price_X_cumulative_last += self.reserve_Y / self.reserve_X * time_elapsed
            self.price_Y_cumulative_last += self.reserve_X / self.reserve_Y * time_elapsed
           # print(self.reserve_X, self.reserve_Y)
           # print(self.reserve_X / self.reserve_Y)

        self.block_timestamp_last = block_timestamp # TODO: maybe remove blocktimestamplast assign in get method
 

_amm = AMM("X", "Y", 800000, 800000, True)


current_cumulative_prices = _amm.current_cumulative_prices
swap = _amm.swap
X = _amm.get_X
Y = _amm.get_Y
reserve_X = _amm.get_reserve_X
reserve_Y = _amm.get_reserve_Y
save_pool_state = _amm.save_pool_state
export_pool_states_to_csv = _amm.export_pool_states_to_csv


