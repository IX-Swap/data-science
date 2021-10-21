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
        self.block_timestamp_last = None 

    
    def get_X(self):
        return self.X

    def get_Y(self):
        return self.Y

    def get_reserve_X(self):
        return self.reserve_X

    def get_reserve_Y(self):
        return self.reserve_Y

    
    def current_cumulative_prices(self, current_block_timestamp: int):
        # true only on first function call
        if self.block_timestamp_last == None:
            self.block_timestamp_last = current_block_timestamp

        if self.block_timestamp_last != current_block_timestamp:
            time_elapsed = current_block_timestamp - self.block_timestamp_last
            
            self.price_X_cumulative_last += self.reserve_Y / self.reserve_X * time_elapsed 
            self.price_Y_cumulative_last += self.reserve_X / self.reserve_Y * time_elapsed
        
        return self.price_X_cumulative_last, self.price_Y_cumulative_last


    def create_swap(self, timestamp, amount):
        if amount > 0:
            token_in = self.X
            token_out = self.Y
        else:
            token_in = self.Y
            token_out = self.X
            
        swap_transaction = SwapTransaction(token_in, token_out, abs(amount), timestamp, self)
        blockchain.receive_transaction(swap_transaction)


    def update_reserve_X(self, delta: float):
        if self.reserve_X + delta < 0:
            raise Exception(f"Cannot update reserve X, reserve_X = {self.reserve_X}, delta = {delta}")

        self.reserve_X += delta
        self.k_last = self.reserve_X * self.reserve_Y


    def update_reserve_Y(self, delta: float):
        if self.reserve_Y + delta < 0:
            raise Exception(f"Cannot update reserve Y, reserve_Y = {self.reserve_Y}, delta = {delta}")

        self.reserve_Y += delta
        self.k_last = self.reserve_X * self.reserve_Y
 

_amm = AMM("TSLA", "USDT", 10000, 10000)


current_cumulative_prices = _amm.current_cumulative_prices
create_swap = _amm.create_swap
X = _amm.get_X
Y = _amm.get_Y
reserve_X = _amm.get_reserve_X
reserve_Y = _amm.get_reserve_Y



