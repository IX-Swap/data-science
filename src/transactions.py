from typing import List
import weakref

import pandas as pd

from monte_carlo2 import Transaction
from enum import Enum
import dsw_oracle
from volatility_mitigation import VolatilityMitigatorCheckStatus
from big_numbers import expand_to_18_decimals


class TransactionStatus(Enum):
    PENDING = 0
    SUCCESS = 1
    BLOCKED_BY_VOLATILITY_MITIGATION = 2
    NOT_ENOUGH_RESERVES = 3
    EXCEEDED_MAX_SLIPPAGE = 4
    K_ERROR = 5
    CLIPPED = 6 # if cannot burn entire amount


class TransactionType(Enum):
    SWAP = 'SWAP'
    MINT = 'MINT'
    BURN = 'BURN'


class Transaction:
    def __init__(self, amm, id) -> None:
        self.amm = amm
        self.id = id

        self.block_timestamp = None
        self.block_number = None
        self.status = TransactionStatus.PENDING



class SwapTransaction(Transaction):
    instances = []

    def __init__(self, transaction: Transaction, amm, id) -> None:
        super().__init__(amm, id)

        self.timestamp = int(transaction.datetime_timestamp.timestamp())
        self.token_in = transaction.token_in
        self.token_out = transaction.token_out
        self.token_in_amount = transaction.token_in_amount
        self.token_out_amount = transaction.token_out_amount
        self.txd = transaction.txd
        self.sender = transaction.sender
        self.to = transaction.to

        (reserve_in, reserve_out) = self.get_reserves()
        self.amount_out_min = self.get_amount_out(self.token_in_amount, reserve_in, reserve_out) * (100 - transaction.slope) // 100
        self.gas_fee = expand_to_18_decimals(150)
        self.additional = None
        self.oracle_amount_out = None
        self.slice_factor = None
        self.slice_factor_curve = None
        self.out_amounts_diff = None
        self.system_fee = None
        self.mitigator_check_status = VolatilityMitigatorCheckStatus.NOT_REACHED
        self.type = TransactionType.SWAP

        self.__class__.instances.append(self)

    
    def get_amount_out(self, amount_in: int, reserve_in: int, reserve_out: int):
        amount_in_with_fee = amount_in * 990
        numerator = amount_in_with_fee * reserve_out
        denominator = reserve_in * 1000 + amount_in_with_fee
        amount_out = numerator // denominator

        return amount_out


    def get_reserves(self):
        if self.token_in == self.amm.X:
            reserve_in = self.amm.reserve_X
            reserve_out = self.amm.reserve_Y
        else:
            reserve_in = self.amm.reserve_Y
            reserve_out = self.amm.reserve_X

        return (reserve_in, reserve_out)


    def execute(self, block_timestamp, block_number):
        self.status = self.try_execute(block_timestamp, block_number)


    def try_execute(self, block_timestamp, block_number):
        self.block_timestamp = block_timestamp
        self.block_number = block_number

        reserve_in, reserve_out = self.get_reserves()
        amount_out = self.token_out_amount = self.get_amount_out(self.token_in_amount, reserve_in, reserve_out) # amount calculated based on current reserves (from amount_in - 1%)
        
        if amount_out >= reserve_out:
            return TransactionStatus.NOT_ENOUGH_RESERVES

        if amount_out < self.amount_out_min:
            return TransactionStatus.EXCEEDED_MAX_SLIPPAGE

        balance_in = reserve_in + self.token_in_amount
        balance_out = reserve_out - amount_out

        balance_in_adjusted = balance_in * 1000 - self.token_in_amount * 10
        balance_out_adjusted = balance_out * 1000 # todo: refactor

        if self.amm.k_last * 1000 * 1000 > balance_in_adjusted * balance_out_adjusted: # todo:remove one * 1000 from out
            return TransactionStatus.K_ERROR
    
        if self.token_in == self.amm.X:
            # in case in token0 is a SEC, take the 0.4% of token1 out and leave whole 1% of retained token0 fee in in the pool
            system_fee = amount_out * 4 // 1000
        else:
            # otherwise take the 40% out of 1% retained token0 fee leaving in the pool remaining 60% of the fee (0.6% in total)
            system_fee = self.token_in_amount * 4 // 1000

        # check if there are enough reserve to perform the swap
        if self.token_in == self.amm.X:
            if self.amm.reserve_Y <= amount_out + system_fee:
                return TransactionStatus.NOT_ENOUGH_RESERVES
        else:
            if self.amm.reserve_X <= amount_out or self.amm.reserve_Y + self.token_in_amount <= system_fee: # Note: second check is redundant
                return TransactionStatus.NOT_ENOUGH_RESERVES
            
        # compute the final out_reserve
        if self.token_in == self.amm.X:
            reserve_out_final = self.amm.reserve_Y - amount_out - system_fee
            assert reserve_out_final > 0, 'Invalid reserve_out_final Y'
        else:
            reserve_out_final = self.amm.reserve_X - amount_out 
            assert reserve_out_final > 0, 'Invalid reserve_out_final X'

        self.amm.update_pair(block_timestamp)

        # todo: move in mitigator class
        if self.amm.is_volatility_mitigator_on == False:
            self.mitigator_check_status = VolatilityMitigatorCheckStatus.MITIGATOR_OFF
            block_transaction = False
        else:
            block_transaction = self.amm.volatility_mitigator.mitigate(self.token_in, self.token_out, self.token_in_amount, amount_out, reserve_out_final, block_timestamp, self)
            dsw_oracle.update(block_timestamp) # before?

        if block_transaction:
            return TransactionStatus.BLOCKED_BY_VOLATILITY_MITIGATION


        # update reserves (perform the swap)
        if self.token_in == self.amm.X:
            self.amm.update_reserve_Y(-amount_out)
            self.amm.update_reserve_X(self.token_in_amount)
        else:
            self.amm.update_reserve_Y(self.token_in_amount)
            self.amm.update_reserve_X(-amount_out)
        
        self.amm.update_reserve_Y(-system_fee) 
        self.system_fee = system_fee
        
        return TransactionStatus.SUCCESS


    @staticmethod
    def to_list_header():
        return ['id', 'token_in', 'token_out', 'token_in_amount', 'token_out_amount_min', 'token_out_amount' , 'system_fee', 'mitigator_check_status', 'oracle_amount_out', 'out_amount_diff', 'slice_factor', 'slice_factor_curve', 'status', 'block_number', 'block_timestamp', 'transaction_timestamp', 'txd', 'sender', 'to']

    def to_list(self):
        return [self.id, self.token_in, self.token_out, self.token_in_amount, self.amount_out_min, self.token_out_amount, self.system_fee, self.mitigator_check_status.name, self.oracle_amount_out, self.out_amounts_diff, self.slice_factor, self.slice_factor_curve, self.status.name, self.block_number, self.block_timestamp, self.timestamp, self.txd, self.sender, self.to]

    @staticmethod
    def save_all(filename):
        transaction_history_list:List[SwapTransaction] = []
        # append all new records to the dataframe
        for transaction in SwapTransaction.instances:
            transaction_history_list.append(transaction.to_list())
                                                
        history_df = pd.DataFrame(transaction_history_list, columns=SwapTransaction.to_list_header())

        history_df.to_csv(filename, index=False)


class BurnTransaction(Transaction):
    instances = []

    def __init__(self, X_amount, Y_amount, timestamp, amm, id) -> None:
        super().__init__(amm, id)

        self.timestamp = int(timestamp.timestamp())
        self.X_amount = X_amount
        self.Y_amount = Y_amount

        self.type = TransactionType.SWAP

        self.__class__.instances.append(self)

    
    def execute(self, block_timestamp, block_number):
        self.status = self.try_execute(block_timestamp, block_number)


    def try_execute(self, block_timestamp, block_number):
        if self.amm.reserve_X < self.X_amount or self.amm.reserve_Y < self.Y_amount:
            MIN_LIQUIDITY = 1000000
            self.X_amount = min(self.amm.reserve_X - MIN_LIQUIDITY, self.X_amount)
            self.Y_amount = min(self.amm.reserve_Y - MIN_LIQUIDITY, self.Y_amount)
            
            self.amm.update_reserve_X(-self.X_amount)
            self.amm.update_reserve_Y(-self.Y_amount)

            self.block_timestamp = block_timestamp
            self.block_number = block_number

            return TransactionStatus.CLIPPED

        self.amm.update_reserve_X(-self.X_amount)
        self.amm.update_reserve_Y(-self.Y_amount)

        self.block_timestamp = block_timestamp
        self.block_number = block_number

        return TransactionStatus.SUCCESS


    @staticmethod
    def to_list_header():
        return ['id', 'X_amount', 'Y_amount', 'timestamp', 'status', 'block_number', 'block_timestamp', 'transaction_timestamp']

    def to_list(self):
        return [self.id, self.X_amount, self.Y_amount, self.timestamp, self.status.name, self.block_number, self.block_timestamp, self.timestamp]


    @staticmethod
    def save_all(filename):
        transaction_history_list:List[BurnTransaction] = []
        for transaction in BurnTransaction.instances:
            transaction_history_list.append(transaction.to_list())
                                                
        history_df = pd.DataFrame(transaction_history_list, columns=BurnTransaction.to_list_header()) # todo: refactor (place inside parent class)

        history_df.to_csv(filename, index=False)
        

class MintTransaction(Transaction):
    instances = []

    def __init__(self, X_amount, Y_amount, timestamp, amm, id) -> None:
        super().__init__(amm, id)

        self.timestamp = int(timestamp.timestamp())
        self.X_amount = X_amount
        self.Y_amount = Y_amount
        self.type = TransactionType.MINT
    
        self.__class__.instances.append(self)

    def execute(self, block_timestamp, block_number):
        self.status = self.try_execute(block_timestamp, block_number)

    def try_execute(self, block_timestamp, block_number):
        self.amm.update_reserve_X(self.X_amount)
        self.amm.update_reserve_Y(self.Y_amount)

        self.block_timestamp = block_timestamp
        self.block_number = block_number
        
        return TransactionStatus.SUCCESS

    @staticmethod
    def to_list_header():
        return ['id', 'X_amount', 'Y_amount', 'timestamp', 'status', 'block_number', 'block_timestamp', 'transaction_timestamp']

    def to_list(self):
        return [self.id, self.X_amount, self.Y_amount, self.timestamp, self.status.name, self.block_number, self.block_timestamp, self.timestamp]


    @staticmethod
    def save_all(filename):
        transaction_history_list:List[MintTransaction] = []
        print("mints: ", len( MintTransaction.instances))
        # append all new records to the dataframe
        for transaction in MintTransaction.instances:
            transaction_history_list.append(transaction.to_list())
                                                
        history_df = pd.DataFrame(transaction_history_list, columns=MintTransaction.to_list_header())

        history_df.to_csv(filename, index=False)