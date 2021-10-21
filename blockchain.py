from typing import List

import pandas as pd
from settings import BLOCK_TIME
from transactions import SwapTransaction
import dsw_oracle

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

        self.pending_transactions.append(swap_transaction)

        if swap_transaction.timestamp >= self.curr_block_timestamp + self.avg_block_time:
            self.create_block()
    

    def create_block(self):
        self.block_transactions = self.pending_transactions 
        self.pending_transactions = []

        dsw_oracle.update(self.curr_block_timestamp) # todo: at the end?
        for swap_transaction in self.block_transactions:
            swap_transaction.block_timestamp = self.curr_block_timestamp
            swap_transaction.execute(self.curr_block_timestamp)
            self.transaction_history.append(swap_transaction)

        self.curr_block_timestamp += self.avg_block_time


    def transactions_to_csv(self):
        history_df = pd.DataFrame(columns=['id', 'X', 'Y', 'Timestamp', 'Value'])
        
        # append all new records to the dataframe
        for index in range(len(self.transaction_history)):
            new_row = {
                'id': self.transaction_history[index].id, 
                'X': self.first_currency, 
                'Y': self.second_currency, 
                'Timestamp': self.transaction_history[index].timestamp,
                'Value': self.transaction_history[index].value
            }
            transaction_history_dataframe = transaction_history_dataframe.append(new_row, ignore_index=True)
        
        # if there is such file -> append new records to it, otherwise create a new file from existing table
        try:
            with open(filename) as f:
                transaction_history_dataframe.to_csv(filename, mode='a', header=False, index=False)
        except IOError:
            transaction_history_dataframe.to_csv(filename, index=False)


_blockchain = BlockChain(BLOCK_TIME)
receive_transaction = _blockchain.receive_transaction