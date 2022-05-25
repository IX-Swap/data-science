from typing import List

import pandas as pd
from settings import BLOCK_TIME
from transactions import BurnTransaction, MintTransaction, SwapTransaction, Transaction
import amm

class BlockChain:
    def __init__(self, avg_block_time: int) -> None:
        self.avg_block_time = avg_block_time
        self.curr_block_number = 0
        self.curr_block_timestamp = None
        
        self.pending_transactions:List[Transaction] = []


    def receive_transaction(self, swap_transaction: Transaction):
        # true only on first function call
        if self.curr_block_timestamp is None:
            self.curr_block_timestamp = swap_transaction.timestamp

        while swap_transaction.timestamp > self.curr_block_timestamp: # todo: replace with blockchain.update call outside
            self.create_block()

        self.pending_transactions.append(swap_transaction)
        

    def update(self, next_transaction_timestamp: int):
        if self.curr_block_timestamp is None:
            return

        while next_transaction_timestamp > self.curr_block_timestamp:
            self.create_block()


    def force_finish(self):
        self.create_block()


    def create_block(self):
        self.block_transactions = self.pending_transactions 
        self.pending_transactions = []
        
        for transaction in self.block_transactions:
            transaction.block_timestamp = self.curr_block_timestamp
            amm.save_pool_state(True, transaction.id)
            transaction.execute(self.curr_block_timestamp, self.curr_block_number)
            amm.save_pool_state(False, transaction.id)

        self.curr_block_timestamp += self.avg_block_time
        self.curr_block_number += 1



    def reset_state(self):
        self.curr_block_number = 0
        self.curr_block_timestamp = None
        self.transaction_history = []
        self.pending_transactions = []

        SwapTransaction.instances = []
        MintTransaction.instances = []
        BurnTransaction.instances = []


_blockchain = BlockChain(BLOCK_TIME)
receive_transaction = _blockchain.receive_transaction
update = _blockchain.update
reset_state = _blockchain.reset_state
force_finish = _blockchain.force_finish