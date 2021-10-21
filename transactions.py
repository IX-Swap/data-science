
class SwapTransaction:
    def __init__(self, token_in: str, token_out: str, token_in_amount: float, timestamp: int, amm) -> None:
        self.timestamp = timestamp
        self.token_in = token_in
        self.token_out = token_out
        self.token_in_amount = token_in_amount
        self.token_out_amount = None
        self.mitigated = False
        self.amm = amm
        self.gas_fee = 150 
        self.succeeded = None
        self.block_timestamp = None

    
    def to_list_headers(self):
        return ['TokenIn', 'TokenOut', 'TokenInAmount', 'TokenOutAmount', 'Timestamp', 'Gas Fee', 'Block Timestamp', 'Succeeded', 'Mitigated']

    def to_list(self):
        return [self.token_in, self.token_out, self.token_in_amount, self.token_out_amount, self.timestamp, self.gas_fee, self.block_timestamp, self.succeeded, self.mitigated]


    def get_amount_out(self, amount_in: float, reserve_in: float, reserve_out: float):
        amount_in_with_fee = amount_in * 990
        numerator = amount_in_with_fee * reserve_out
        denominator = reserve_in * 1000 + amount_in_with_fee
        amount_out = numerator / denominator

        return amount_out


    def get_reserves(self):
        if self.token_in == self.amm.X:
            reserve_in = self.amm.reserve_X
            reserve_out = self.amm.reserve_Y
        else:
            reserve_in = self.amm.reserve_Y
            reserve_out = self.amm.reserve_X

        return (reserve_in, reserve_out)


    def execute(self, block_timestamp):
        self.succeeded = self.try_execute(block_timestamp)

    def try_execute(self, block_timestamp):
        self.block_timestamp = block_timestamp

        reserve_in, reserve_out = self.get_reserves()
        amount_out = self.token_out_amount = self.get_amount_out(self.token_in_amount, reserve_in, reserve_out) # amount calculated based on current reserves (from amount_in - 1%)
        # print(self.token_in_amount, amount_out)

        if self.token_in == self.amm.X:
            # in case in token0 is a SEC, take the 0.4% of token1 out and leave whole 1% of retained token0 fee in in the pool
            system_fee = amount_out * 4 / 1000
        else:
            # otherwise take the 40% out of 1% retained token0 fee leaving in the pool remaining 60% of the fee (0.6% in total)
            system_fee = self.token_in_amount * 4 / 1000

        # check if there are enough reserve to perform the swap
        if self.token_in == self.amm.X:
            if self.amm.reserve_Y <= amount_out + system_fee:
                return False
        else:
            if self.amm.reserve_X <= amount_out or self.amm.reserve_Y + self.token_in_amount <= system_fee:
                return False
            
        # compute the final out_reserve
        if self.token_in == self.amm.X:
            reserve_out_final = self.amm.reserve_Y - amount_out - system_fee
            assert reserve_out_final >= 0, 'Invalid reserve_out_final'
        else:
            reserve_out_final = self.amm.reserve_X - amount_out - system_fee
            assert reserve_out_final >= 0, 'Invalid reserve_out_final'

        block_transaction = self.amm.is_volatility_mitigator_on and self.amm.volatility_mitigator.mitigate(self.token_in, self.token_out, self.token_in_amount, amount_out, reserve_out_final, block_timestamp)
        self.mitigated = block_transaction

        if not block_transaction:
            # update reserves (perform the swap)
            if self.token_in == self.amm.X:
                self.amm.update_reserve_Y(-amount_out)
                self.amm.update_reserve_X(self.token_in_amount)
            else:
                self.amm.update_reserve_Y(self.token_in_amount)
                self.amm.update_reserve_X(-amount_out)
            
            self.amm.update_reserve_Y(-system_fee) 
        
        return not block_transaction