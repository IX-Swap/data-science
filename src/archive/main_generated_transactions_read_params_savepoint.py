from distutils.command.config import config
import logging
from random import randrange
import itertools
import random
import pandas as pd
import amm
import json
import os
import numpy as np
from datetime import date, datetime, timedelta
from monte_carlo import CauchyGenerator, LognormalGenerator, MonteCarloTransactionSimulator, PoissonGenerator, Transaction, WeibullGenerator
import blockchain
from big_numbers import contract_18_decimals_to_float, expand_to_18_decimals
from safe_math import q_decode_144
import settings
from transactions import SwapTransaction
from utils import normalize_csv, normalize_pool_state, save_dict


logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(name)s:%(message)s', datefmt="%m/%d/%Y %I:%M:%S %p")
logger = logging.getLogger(__name__)

EXPERIMENT_ID = 76
SIM_MESSAGE = ''

X_NAME = 'X'
Y_NAME = 'Y'

# todo: check ratio

def main(): 
    OCCURENCES_PER_MIN = 1 / 30
    INITIAL_SEC_PRICE = 1

    WINDOW_SIZE = 24
    GRANULARITY = 24
    PRICE_TOLLERANCE_THRESHOLD = 98

    DIST_LOC = 0


    BASE_DIR = f'../data/simulated_transactions_grid_dist/experiment_{EXPERIMENT_ID}'
    os.makedirs(BASE_DIR)
    
    config = {
        'window_size': WINDOW_SIZE,
        'granularity': GRANULARITY,
        'price_tollerance_threshold': PRICE_TOLLERANCE_THRESHOLD
    }
    save_dict(f'{BASE_DIR}/config.json', config)

    logger.info("starting...")
    
    iteration = 0
    start_time = datetime.now()

    with open('params_m1.json') as f:
        params_config = json.load(f)

    for params in params_config:
        a, b = params['reserve_range']

        if a > 10000:
            break

        initial_reserves_usd = (a + b) // 2

        for shape, scale in zip(params['shape'], params['scale']):
            os.makedirs(f'{BASE_DIR}/{iteration}')
            transactions_history1_path = f'{BASE_DIR}/{iteration}/history1.csv'
            transactions_history2_path = f'{BASE_DIR}/{iteration}/history2.csv'

            simulate_transactions(start_time, OCCURENCES_PER_MIN, X_NAME, Y_NAME, transactions_history1_path, shape, DIST_LOC, scale)
            simulate_transactions(start_time, OCCURENCES_PER_MIN, Y_NAME, X_NAME, transactions_history2_path, shape, DIST_LOC, scale)

            transactions1_df = pd.read_csv(transactions_history1_path)
            transactions2_df = pd.read_csv(transactions_history2_path)
            all_transactions = combine_transactions(transactions1_df, transactions2_df)
            all_transactions['token_in_amount'] = all_transactions['token_in_amount'].apply(expand_to_18_decimals)
            start_time = all_transactions['datetime_timestamp'].min()
            
            for subindex, vm in enumerate([False, True]):
                os.makedirs(f'{BASE_DIR}/{iteration}/{subindex}')

                config = {
                    'freq_X': OCCURENCES_PER_MIN,
                    'freq_Y': OCCURENCES_PER_MIN,
                    'initial_reserve_usd': initial_reserves_usd,
                    'initial_sec_price': INITIAL_SEC_PRICE,
                    'scale': scale,
                    'shape': shape,
                    'vm': vm
                }
                
                
                save_dict(f'{BASE_DIR}/{iteration}/{subindex}/config.txt', config)
                amm.reset(X_NAME, Y_NAME, initial_reserves_usd // INITIAL_SEC_PRICE , initial_reserves_usd, vm, WINDOW_SIZE * 60 * 60, WINDOW_SIZE * 60 * 60// GRANULARITY, GRANULARITY) #todo: beautify

                cnt = 0
                for _, row in all_transactions.iterrows():
                    amm.reserve_X() / amm.reserve_Y()
                    
                    if row['datetime_timestamp'] - start_time <= timedelta(days=1):
                        amount = row['token_in_amount'] // 1000 
                    else:
                        amount = row['token_in_amount']

                    if vm == True and amm.verify_swap(cnt, Transaction(row['datetime_timestamp'], amount, row['token_in'], row['token_out'], row['slope'])):
                        amm.swap(cnt, Transaction(row['datetime_timestamp'], amount, row['token_in'], row['token_out'], row['slope']))
                    else:
                        retry = 1 #random.randint(0, 1)

                        if retry == 1:
                            for i in range(0, 5):
                                amount = amount * 3 // 4
                            
                                if amm.verify_swap(cnt, Transaction(row['datetime_timestamp'], amount, row['token_in'], row['token_out'], row['slope'])):
                                    amm.swap(cnt, Transaction(row['datetime_timestamp'], amount, row['token_in'], row['token_out'], row['slope']))
                                    
                                    break

                    cnt += 1

                SwapTransaction.save_all(f'{BASE_DIR}/{iteration}/{subindex}/swaps.csv')
                blockchain.reset_state()

                amm.export_pool_states_to_csv(f'{BASE_DIR}/{iteration}/{subindex}/pool_before_transaction.csv', 
                                                f'{BASE_DIR}/{iteration}/{subindex}/pool_after_transaction.csv')

                logger.info("Start normalizing...")
                normalize_csv(f'{BASE_DIR}/{iteration}/{subindex}/swaps.csv', ['token_in_amount', 'token_out_amount', 'token_out_amount_min', 'system_fee', 'oracle_amount_out', 'oracle_price'], f'{BASE_DIR}/{iteration}/{subindex}/swaps_normalized.csv')
                normalize_pool_state(f'{BASE_DIR}/{iteration}/{subindex}/pool_before_transaction.csv', f'{BASE_DIR}/{iteration}/{subindex}/pool_before_transaction_normalized.csv')
                normalize_pool_state(f'{BASE_DIR}/{iteration}/{subindex}/pool_after_transaction.csv', f'{BASE_DIR}/{iteration}/{subindex}/pool_after_transaction_normalized.csv')
                logger.info("Finished normalizing")

            iteration += 1


def simulate_transactions(start_time, mean_occurencies_per_min, token0, token1, transaction_history_filename, shape, loc, scale):
    simulator = MonteCarloTransactionSimulator(
        PoissonGenerator(cycle_size=60000, mean_occurencies=1/15),  # set frequency for initial 24 hours
        WeibullGenerator(shape=shape, loc=loc, scale=scale), token0, token1,
    )

    current_iteration_timestamp = start_time
    simulation_seconds_total = 60*24

    for _ in range(simulation_seconds_total):
        simulator.generate_transactions(current_iteration_timestamp)
        current_iteration_timestamp += timedelta(milliseconds=simulator.frequency_generator.cycle_size)

    simulation_seconds_total = 60*24*25
    simulator.frequency_generator.mean_occurencies = mean_occurencies_per_min

    for _ in range(simulation_seconds_total):
        simulator.generate_transactions(current_iteration_timestamp)
        current_iteration_timestamp += timedelta(milliseconds=simulator.frequency_generator.cycle_size)

    simulator.transaction_history_to_csv(transaction_history_filename)


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