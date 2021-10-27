from typing import List

import pandas as pd
from settings import BLOCK_TIME
from transactions import SwapTransaction
import amm

class BlockChain:
    def __init__(self, avg_block_time: int) -> None:
        self.avg_block_time = avg_block_time
        self.curr_block_number = 0
        self.curr_block_timestamp = None
        self.transaction_history:List[SwapTransaction] = []
        self.pending_transactions:List[SwapTransaction] = []


    def receive_transaction(self, swap_transaction: SwapTransaction):
        # true only on first function call
        if self.curr_block_timestamp is None:
            self.curr_block_timestamp = swap_transaction.timestamp

        while swap_transaction.timestamp > self.curr_block_timestamp:
            self.create_block()

        self.pending_transactions.append(swap_transaction)


    def create_block(self):
        self.block_transactions = self.pending_transactions 
        self.pending_transactions = []

        for swap_transaction in self.block_transactions:
            swap_transaction.block_timestamp = self.curr_block_timestamp
            amm.save_pool_state(True, swap_transaction.id)
            swap_transaction.execute(self.curr_block_timestamp, self.curr_block_number)
            amm.save_pool_state(False, swap_transaction.id)
            self.transaction_history.append(swap_transaction)

        self.curr_block_timestamp += self.avg_block_time
        self.curr_block_number += 1


    def transactions_to_csv(self):
        transaction_history_list = []

        # append all new records to the dataframe
        for transaction in self.transaction_history:
            transaction_history_list.append([transaction.id, transaction.token_in, transaction.token_out, transaction.token_in_amount, transaction.amount_out_min, transaction.token_out_amount, transaction.system_fee, transaction.mitigator_check_status.name , transaction.oracle_amount_out, transaction.out_amounts_diff, transaction.slice_factor, transaction.slice_factor_curve,
                                                transaction.status.name, transaction.block_number, transaction.block_timestamp, transaction.timestamp])
                                                
        history_df = pd.DataFrame(transaction_history_list, columns=['id', 'token_in', 'token_out', 'token_in_amount', 'token_out_amount_min', 'token_out_amount' , 'system_fee', 'mitigator_check_status', 'oracle_amount_out', 'out_amount_diff', 'slice_factor', 'slice_factor_curve', 'status', 'block_number', 'block_timestamp', 'transaction_timestamp',  ])

        history_df.to_csv('data/amm.csv', index=False)


_blockchain = BlockChain(BLOCK_TIME)
receive_transaction = _blockchain.receive_transaction
transaction_to_csv = _blockchain.transactions_to_csv