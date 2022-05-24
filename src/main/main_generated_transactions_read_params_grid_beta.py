import os, sys
sys.path.insert(0, os.getcwd()) 

import logging
import pandas as pd
import json
import os
from datetime import datetime, timedelta

import amm
import blockchain
from trading_simulation import MonteCarloTransactionSimulator, PoissonGenerator, Transaction, WeibullGenerator
from big_numbers import expand_to_18_decimals
from transactions import SwapTransaction
from utils import normalize_csv, normalize_pool_state, save_dict

# old main, required update (using main_historic_transactions.py)

logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(name)s:%(message)s', datefmt="%m/%d/%Y %I:%M:%S %p")
logger = logging.getLogger(__name__)

EXPERIMENT_ID = 76
SIM_MESSAGE = 'freq/slippage list grid 75000'

X_NAME = 'X'
Y_NAME = 'Y'

# todo: check ratio

def main(): 
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
        'price_tollerance_threshold': PRICE_TOLLERANCE_THRESHOLD,
        'sim_message': SIM_MESSAGE
    }

    save_dict(f'{BASE_DIR}/config.json', config)
    config.clear()

    logger.info("starting...")
    
    iteration = 0
    start_time = datetime.now()

    with open('params_m2.json') as f:
        params_config = json.load(f)
    print(params_config)
        
    
    for freq in [0.5, 1, 2, 5]:
        for slippage in [1, 5, 10, 15, 20, 25, 30]:
            for params in params_config:
                a, b = params['reserve_range']
                if a != 50000 and b != 100000:
                    continue
                print(a, b)

                initial_reserves_usd = (a + b) // 2

                for shape, scale in zip(params['shape'], params['scale']):
                    os.makedirs(f'{BASE_DIR}/{iteration}')
                    transactions_history1_path = f'{BASE_DIR}/{iteration}/history1.csv'
                    transactions_history2_path = f'{BASE_DIR}/{iteration}/history2.csv'

                    simulate_transactions(start_time, freq, X_NAME, Y_NAME, transactions_history1_path, shape, DIST_LOC, scale)
                    simulate_transactions(start_time, freq, Y_NAME, X_NAME, transactions_history2_path, shape, DIST_LOC, scale)

                    transactions1_df = pd.read_csv(transactions_history1_path)
                    transactions2_df = pd.read_csv(transactions_history2_path)
                    all_transactions = combine_transactions(transactions1_df, transactions2_df)
                    all_transactions['token_in_amount'] = all_transactions['token_in_amount'].apply(expand_to_18_decimals)
                    start_time = all_transactions['datetime_timestamp'].min()
                    
                    for subindex, vm in enumerate([False, True]):
                        os.makedirs(f'{BASE_DIR}/{iteration}/{subindex}')

                        config = {
                            'freq': freq,
                            'initial_reserve_usd': initial_reserves_usd,
                            'initial_sec_price': INITIAL_SEC_PRICE,
                            'scale': scale,
                            'shape': shape,
                            'vm': vm,
                            'slippage': slippage,
                        }
                        
                        save_dict(f'{BASE_DIR}/{iteration}/{subindex}/config.json', config)
                        amm.reset(X_NAME, Y_NAME, initial_reserves_usd // INITIAL_SEC_PRICE , initial_reserves_usd, vm, WINDOW_SIZE * 60 * 60, WINDOW_SIZE * 60 * 60// GRANULARITY, GRANULARITY) #todo: beautify

                        cnt = 0
                        for _, row in all_transactions.iterrows():
                            amm.reserve_X() / amm.reserve_Y()
                            
                            if row['datetime_timestamp'] - start_time <= timedelta(days=1):
                                amount = row['token_in_amount'] // 1000 
                            else:
                                amount = row['token_in_amount']
                                
                            amm.swap(cnt, Transaction(row['datetime_timestamp'], amount, row['token_in'], row['token_out'], slippage,))
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



def save_config(filename, mean_occurencies_per_min, initial_reserves_usd, ratios_sec_usd, scale, shape, price_tollerance_threshold, window_size, granularity, vm):
    with open(filename, 'w') as f:
        f.write("mean_occ_per_min: " + str(mean_occurencies_per_min))
        f.write("\ninitial_reserve_usd: " + str(initial_reserves_usd))
        f.write("\nratio_sec_usd: " + str(ratios_sec_usd))
        f.write("\nscale: " + str(scale))
        f.write("\nshape: " + str(shape))
        f.write("\nprice_tolerance_threshold: " + str(price_tollerance_threshold))
        f.write("\nwindow_size: " + str(window_size))
        f.write("\ngranularity: " + str(granularity)) #todo: read from settings
        f.write("\nvolatility_mitigator: " + str(vm)) #todo: read from settings




def simulate_transactions(start_time, mean_occurencies_per_min, token0, token1, transaction_history_filename, shape, loc, scale):
    simulator = MonteCarloTransactionSimulator(
        PoissonGenerator(cycle_size=60000, mean_occurencies=mean_occurencies_per_min), 
        WeibullGenerator(shape=shape, loc=loc, scale=scale), token0, token1,
    )

    start_time = datetime.now()

    current_iteration_timestamp = start_time

    # total_number_transactions = 50000
    # simulation_seconds_total = int((total_number_transactions + 24*60*mean_occurencies_per_min) / mean_occurencies_per_min) 
    simulator.frequency_generator.mean_occurencies = 1/15
    simulation_seconds_total = 60*24

    for _ in range(simulation_seconds_total):
        simulator.generate_transactions(current_iteration_timestamp)
        current_iteration_timestamp += timedelta(milliseconds=simulator.frequency_generator.cycle_size)

    total_number_transactions = 3000
    simulator.frequency_generator.mean_occurencies = mean_occurencies_per_min
    simulation_cycles = int((total_number_transactions) / mean_occurencies_per_min) 
    print(simulation_cycles)

    for _ in range(simulation_cycles):
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