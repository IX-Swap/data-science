import logging
from random import randrange
import itertools
import pandas as pd
import amm
import os
import numpy as np
from datetime import datetime, timedelta
from monte_carlo2 import CauchyGenerator, MonteCarloTransactionSimulator, PoissonGenerator, Transaction
import blockchain

logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(name)s:%(message)s', datefmt="%m/%d/%Y %I:%M:%S %p")
logger = logging.getLogger(__name__)

EXPERIMENT_ID = 3
X_NAME = 'X'
Y_NAME = 'Y'

def main(): 
    # occurences_per_min = [10, 1, 0.01]
    # initial_reserves_usd = [1000, 10000, 100000]
    # ratios_sec_usd = [1, 10, 100]

    occurences_per_min = [10]
    initial_reserves_usd = [10000]
    ratios_sec_usd = [10]

    grid = itertools.product(occurences_per_min, initial_reserves_usd, ratios_sec_usd)

    os.makedirs(f'data/experiment_{EXPERIMENT_ID}')

    start_time = datetime.now()
    iteration = 0
    for mean_occurencies_per_min, initial_reserves_usd, ratios_sec_usd in grid:
        os.makedirs(f'data/experiment_{EXPERIMENT_ID}/{iteration}')

        transactions_history1_path = f'data/experiment_{EXPERIMENT_ID}/{iteration}/history1.csv'
        transactions_history2_path = f'data/experiment_{EXPERIMENT_ID}/{iteration}/history2.csv'

        simulate_transactions(start_time, mean_occurencies_per_min, X_NAME, Y_NAME, transactions_history1_path, 1000, ratios_sec_usd)
        simulate_transactions(start_time, mean_occurencies_per_min, Y_NAME, X_NAME, transactions_history2_path, 1000, 1)

        transactions1_df = pd.read_csv(transactions_history1_path)
        transactions2_df = pd.read_csv(transactions_history2_path)

        all_transactions = combine_transactions(transactions1_df, transactions2_df)

        cnt = 0
        amm.reset(X_NAME, Y_NAME, initial_reserves_usd / ratios_sec_usd, initial_reserves_usd, True)

        for _, row in all_transactions.iterrows():
            amm.swap(cnt, Transaction(row['datetime_timestamp'], row['token_in_amount'], row['token_in'], row['token_out'], row['slope']))
            cnt += 1

        blockchain.transaction_to_csv(f'data/experiment_{EXPERIMENT_ID}/{iteration}/blockchain.csv', True)
        amm.export_pool_states_to_csv(f'data/experiment_{EXPERIMENT_ID}/{iteration}/pool_before_transaction.csv', 
                                        f'data/experiment_{EXPERIMENT_ID}/{iteration}/pool_after_transaction.csv')

        iteration += 1

def simulate_transactions(start_time, mean_occurencies_per_min, token0, token1, transaction_history_filename, cauchy_scale, token_in_ratio):
    simulator = MonteCarloTransactionSimulator(
        PoissonGenerator(cycle_size=60000, mean_occurencies=mean_occurencies_per_min), 
        CauchyGenerator(loc=0, scale=cauchy_scale), token0, token1,
    )

    start_time = datetime.now()

    current_iteration_timestamp = start_time
    for _ in range(60*24*6):
        simulator.generate_transactions(current_iteration_timestamp)
        current_iteration_timestamp += timedelta(milliseconds=simulator.frequency_generator.cycle_size)

    simulator.transaction_history_to_csv(transaction_history_filename, token_in_ratio)


def combine_transactions(transactions1_df, transactions2_df):
    transactions1_max_time_df = pd.to_datetime(transactions1_df['datetime_timestamp']).max()
    transactions2_max_time_df = pd.to_datetime(transactions2_df['datetime_timestamp']).max()
    min_end_time = min(transactions1_max_time_df, transactions2_max_time_df)

    print("Min end time: ", min_end_time)

    all_transactions = pd.concat([transactions1_df, transactions2_df])
    all_transactions['datetime_timestamp'] = pd.to_datetime(all_transactions['datetime_timestamp'])
    all_transactions = all_transactions[all_transactions['datetime_timestamp'] <= min_end_time]
    
    all_transactions['datetime_timestamp'] = pd.to_datetime(all_transactions['datetime_timestamp'])
    all_transactions.sort_values(by='datetime_timestamp', inplace=True)

    return all_transactions


if __name__ == '__main__':
    main()