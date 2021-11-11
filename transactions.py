from monte_carlo2 import Transaction
from enum import Enum
import dsw_oracle
from volatility_mitigation import VolatilityMitigatorCheckStatus
from big_numbers import expand_to_18_decimals


class SwapTransactionStatus(Enum):
    PENDING = 0
    SUCCESS = 1
    BLOCKED_BY_VOLATILITY_MITIGATION = 2
    NOT_ENOUGH_RESERVES = 3
    EXCEEDED_MAX_SLIPPAGE = 4
    K_ERROR = 5



class SwapTransaction:
    def __init__(self, transaction: Transaction, amm, id) -> None:
        self.amm = amm
        self.id = id

        self.timestamp = int(transaction.datetime_timestamp.timestamp())
        self.token_in = transaction.token_in
        self.token_out = transaction.token_out
        self.token_in_amount = transaction.token_in_amount
        self.token_out_amount = transaction.token_out_amount

        (reserve_in, reserve_out) = self.get_reserves()
        self.amount_out_min = self.get_amount_out(self.token_in_amount, reserve_in, reserve_out) * (100 - transaction.slope) // 100
        self.gas_fee = expand_to_18_decimals(150)
        self.status = SwapTransactionStatus.PENDING
        self.additional = None
        self.block_timestamp = None
        self.block_number = None
        self.oracle_amount_out = None
        self.slice_factor = None
        self.slice_factor_curve = None
        self.out_amounts_diff = None
        self.system_fee = None
        self.mitigator_check_status = VolatilityMitigatorCheckStatus.NOT_REACHED

    
    def to_list_headers(self):
        return ['TokenIn', 'TokenOut', 'TokenInAmount', 'TokenOutAmount', 'Timestamp', 'Gas Fee', 'Block Timestamp', 'Succeeded', 'Mitigated']

    def to_list(self):
        return [self.token_in, self.token_out, self.token_in_amount, self.token_out_amount, self.timestamp, self.gas_fee, self.block_timestamp, self.status]


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
            return SwapTransactionStatus.NOT_ENOUGH_RESERVES

        if amount_out < self.amount_out_min:
            return SwapTransactionStatus.EXCEEDED_MAX_SLIPPAGE

        balance_in = reserve_in + self.token_in_amount
        balance_out = reserve_out - amount_out

        balance_in_adjusted = balance_in * 1000 - self.token_in_amount * 10
        balance_out_adjusted = balance_out * 1000 # todo: refactor

        if self.amm.k_last * 1000 * 1000 > balance_in_adjusted * balance_out_adjusted: # todo:remove one * 1000 from out
            return SwapTransactionStatus.K_ERROR

        k_previous = self.amm.k_last
    
        if self.token_in == self.amm.X:
            # in case in token0 is a SEC, take the 0.4% of token1 out and leave whole 1% of retained token0 fee in in the pool
            system_fee = amount_out * 4 // 1000
        else:
            # otherwise take the 40% out of 1% retained token0 fee leaving in the pool remaining 60% of the fee (0.6% in total)
            system_fee = self.token_in_amount * 4 // 1000

        # check if there are enough reserve to perform the swap
        if self.token_in == self.amm.X:
            if self.amm.reserve_Y <= amount_out + system_fee:
                return SwapTransactionStatus.NOT_ENOUGH_RESERVES
        else:
            if self.amm.reserve_X <= amount_out or self.amm.reserve_Y + self.token_in_amount <= system_fee: # Note: second check is redundant
                return SwapTransactionStatus.NOT_ENOUGH_RESERVES
            
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
            dsw_oracle.update(block_timestamp) 

        if block_transaction:
            return SwapTransactionStatus.BLOCKED_BY_VOLATILITY_MITIGATION



        # update reserves (perform the swap)
        if self.token_in == self.amm.X:
            self.amm.update_reserve_Y(-amount_out)
            self.amm.update_reserve_X(self.token_in_amount)
        else:
            self.amm.update_reserve_Y(self.token_in_amount)
            self.amm.update_reserve_X(-amount_out)
        
      #  self.amm.update_reserve_Y(-system_fee) 
        self.system_fee = system_fee

        # todo: check
        reserve_in, reserve_out = self.get_reserves()

     #   if k_previous > reserve_in * reserve_out:
    #        print(k_previous, reserve_in, reserve_out)

        
        return SwapTransactionStatus.SUCCESS