import logging
from random import randrange
import pandas as pd
import amm
import numpy as np
from datetime import datetime, timedelta
from monte_carlo2 import MonteCarloTransactionSimulator, NormalGenerator, PoissonGenerator, Transaction
import blockchain

logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(name)s:%(message)s', datefmt="%m/%d/%Y %I:%M:%S %p")
logger = logging.getLogger(__name__)


def main(): 
    simulator1 = MonteCarloTransactionSimulator(
        PoissonGenerator(cycle_size=60000, mean_occurencies=5), 
        NormalGenerator(mu=0, sigma=10000, lower_bound=0, upper_bound=np.inf), 'X', 'Y'
    )

    start_time = datetime.now()

    current_iteration_timestamp = start_time
    for index in range(60*24*6):
        simulator1.generate_transactions(current_iteration_timestamp)
        current_iteration_timestamp += timedelta(milliseconds=randrange(simulator1.frequency_generator.cycle_size))

   # transactions = simulator.get_history()
    simulator1.transaction_history_to_csv('data/history1.csv')


    simulator2 = MonteCarloTransactionSimulator(
            PoissonGenerator(cycle_size=60000, mean_occurencies=5), 
            NormalGenerator(mu=0, sigma=10000, lower_bound=0, upper_bound=np.inf), 'Y', 'X'
        )

    current_iteration_timestamp = start_time
    for index in range(60*24*6):
        simulator2.generate_transactions(current_iteration_timestamp)
        current_iteration_timestamp += timedelta(milliseconds=randrange(simulator2.frequency_generator.cycle_size))

    simulator2.transaction_history_to_csv('data/history2.csv')

    transactions1_df = pd.read_csv('data/history1.csv')
    transactions2_df = pd.read_csv('data/history2.csv')

    transactions1_max_time_df = pd.to_datetime(transactions1_df['datetime_timestamp']).max()
    transactions2_max_time_df = pd.to_datetime(transactions2_df['datetime_timestamp']).max()
    min_end_time = min(transactions1_max_time_df, transactions2_max_time_df)
    print(min_end_time)
    print(transactions1_max_time_df, transactions2_max_time_df)

    all_transactions = pd.concat([transactions1_df, transactions2_df])
    all_transactions['datetime_timestamp'] = pd.to_datetime(all_transactions['datetime_timestamp'])
    all_transactions = all_transactions[all_transactions['datetime_timestamp'] <= min_end_time]
    
    all_transactions['datetime_timestamp'] = pd.to_datetime(all_transactions['datetime_timestamp'])
    all_transactions.sort_values(by='datetime_timestamp', inplace=True)

    cnt = 0

    for _, row in all_transactions.iterrows():
        amm.swap(cnt, Transaction(row['datetime_timestamp'], row['token_in_amount'], row['token_in'], row['token_out'], row['slope']))
        
        cnt += 1

    blockchain.transaction_to_csv()
    amm.export_pool_states_to_csv()

if __name__ == '__main__':
    main()