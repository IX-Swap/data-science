import os, sys
sys.path.insert(0, os.getcwd()) 

import logging
import pandas as pd
import amm
import os
from datetime import datetime, timedelta
from trading_simulation import MonteCarloTransactionSimulator, PoissonGenerator, Transaction, WeibullGenerator
import blockchain
from big_numbers import contract_18_decimals_to_float, expand_to_18_decimals
from safe_math import q_decode_144
import settings
from transactions import SwapTransaction

# old main, required update (using main_historic_transactions.py)

logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(name)s:%(message)s', datefmt="%m/%d/%Y %I:%M:%S %p")
logger = logging.getLogger(__name__)

EXPERIMENT_ID = 36

X_NAME = 'X'
Y_NAME = 'Y'

# todo: check ratio

# go together: scale/limit
def main(): 
    OCCURENCES_PER_MIN = 1 / 30
    INITIAL_RESERVES_USD = 30000
    INITIAL_SEC_PRICE = 1

    WINDOW_SIZE = 24
    GRANULARITY = 24
    PRICE_TOLLERANCE_THRESHOLD = 98

    DEFAULT_SLIPPAGE = 100

    BASE_DIR = f'../data/simulated_transactions/experiment_{EXPERIMENT_ID}'
    os.makedirs(BASE_DIR)
    
    with open(f'{BASE_DIR}/config.txt', 'w') as f:
        f.write('\noccurences_per_min: ' + str(OCCURENCES_PER_MIN))
        f.write('\ninitial_reserves_usd: ' + str(INITIAL_RESERVES_USD))
        f.write('\ninitial_sec_price: ' + str(INITIAL_SEC_PRICE))
        f.write('\nwindow_size: ' + str(WINDOW_SIZE))
        f.write('\ngranularity: ' + str(GRANULARITY))
        f.write('\nprice_tollerance_threshold: ' + str(PRICE_TOLLERANCE_THRESHOLD))


    start_time = datetime.now()
    iteration = 0
    print("starting...")

    transactions_history1_path = f'{BASE_DIR}/history1.csv'
    transactions_history2_path = f'{BASE_DIR}/history2.csv'
    
    loc = 0
    shape = 0.9
    scale = 1000

    simulate_transactions(start_time, OCCURENCES_PER_MIN , X_NAME, Y_NAME, transactions_history1_path, shape, loc, scale)
    simulate_transactions(start_time, OCCURENCES_PER_MIN, Y_NAME, X_NAME, transactions_history2_path, shape, loc, scale)

    transactions1_df = pd.read_csv(transactions_history1_path)
    transactions2_df = pd.read_csv(transactions_history2_path)
    all_transactions = combine_transactions(transactions1_df, transactions2_df)
    all_transactions['token_in_amount'] = all_transactions['token_in_amount'].apply(expand_to_18_decimals)
    start_time = all_transactions['datetime_timestamp'].min()


    for vm in [False, True]:
        os.makedirs(f'{BASE_DIR}/{iteration}')
        #save_config(f'{BASE_DIR}/{iteration}/config.txt', OCCURENCES_PER_MIN, INITIAL_RESERVES_USD, INITIAL_SEC_PRICE, CAUCHY_SCALE_X, CAUCHY_SCALE_Y, CAUCHY_MAX_LIMIT_X, CAUCHY_MAX_LIMIT_Y, PRICE_TOLLERANCE_THRESHOLD, WINDOW_SIZE, GRANULARITY, vm)

        amm.reset(X_NAME, Y_NAME, INITIAL_RESERVES_USD // INITIAL_SEC_PRICE , INITIAL_RESERVES_USD, vm, WINDOW_SIZE * 60 * 60, WINDOW_SIZE * 60 * 60// GRANULARITY, GRANULARITY) #todo: beautify

        cnt = 0
        for _, row in all_transactions.iterrows():
            amm.reserve_X() / amm.reserve_Y()
            
            if row['datetime_timestamp'] - start_time <= timedelta(days=1):
                amount = row['token_in_amount'] // 1000 
            else:
                amount = row['token_in_amount']
                
            amm.swap(cnt, Transaction(row['datetime_timestamp'], amount, row['token_in'], row['token_out']), DEFAULT_SLIPPAGE)
            cnt += 1

        SwapTransaction.save_all(f'{BASE_DIR}/{iteration}/swaps.csv')
        blockchain.reset_state()

        amm.export_pool_states_to_csv(f'{BASE_DIR}/{iteration}/pool_before_transaction.csv', 
                                        f'{BASE_DIR}/{iteration}/pool_after_transaction.csv')

        logger.info("Start normalizing...")
        normalize_csv(f'{BASE_DIR}/{iteration}/swaps.csv', ['token_in_amount', 'token_out_amount', 'token_out_amount_min', 'system_fee', 'oracle_amount_out'], f'{BASE_DIR}/{iteration}/swaps_normalized.csv')
        normalize_pool_state(f'{BASE_DIR}/{iteration}/pool_before_transaction.csv', f'{BASE_DIR}/{iteration}/pool_before_transaction_normalized.csv')
        normalize_pool_state(f'{BASE_DIR}/{iteration}/pool_after_transaction.csv', f'{BASE_DIR}/{iteration}/pool_after_transaction_normalized.csv')
        logging.info("Finished normalizing")

        iteration += 1

def normalize_csv(filename, cols_to_normalize, normalized_filename):
    df = pd.read_csv(filename)

    for col in cols_to_normalize:
        df[col] = df[col].apply(contract_18_decimals_to_float)
    
    df.to_csv(normalized_filename, index=False)

# todo: separate into func, cols - parameters
def normalize_blockchain(blockchain_filename, normalized_filename):
    blockchain_df = pd.read_csv(blockchain_filename)

    # todo: deal with none
    blockchain_df['token_in_amount'] = blockchain_df['token_in_amount'].apply(contract_18_decimals_to_float)
    blockchain_df['token_out_amount'] = blockchain_df['token_out_amount'].apply(contract_18_decimals_to_float)
    blockchain_df['token_out_amount_min'] = blockchain_df['token_out_amount_min'].apply(contract_18_decimals_to_float)
    blockchain_df['system_fee'] = blockchain_df['system_fee'].apply(contract_18_decimals_to_float)
    blockchain_df['oracle_amount_out'] = blockchain_df['oracle_amount_out'].apply(contract_18_decimals_to_float)

    blockchain_df.to_csv(normalized_filename)



def normalize_pool_state(pool_state_filename, normalized_filename):
    pool_state_df = pd.read_csv(pool_state_filename)

    # todo: try optimizing
    pool_state_df['reserve_X'] = pool_state_df['reserve_X'].apply(contract_18_decimals_to_float)
    pool_state_df['reserve_Y'] = pool_state_df['reserve_Y'].apply(contract_18_decimals_to_float)
    pool_state_df['k'] = pool_state_df['k'].apply(contract_18_decimals_to_float)
    pool_state_df['k'] = pool_state_df['k'].apply(contract_18_decimals_to_float) # second time!!!
    pool_state_df['price_X_cumulative'] = pool_state_df['price_X_cumulative'].apply(int).apply(q_decode_144)
    pool_state_df['price_Y_cumulative'] = pool_state_df['price_Y_cumulative'].apply(int).apply(q_decode_144)

    pool_state_df.to_csv(normalized_filename)

def save_config(filename, mean_occurencies_per_min, initial_reserves_usd, ratios_sec_usd, cauchy_scale_x, cauchy_scale_y, cauchy_max_limit_x, cauchy_max_limit_y, price_tollerance_threshold, window_size, granularity, vm):
    with open(filename, 'w') as f:
        f.write("mean_occ_per_min: " + str(mean_occurencies_per_min))
        f.write("\ninitial_reserve_usd: " + str(initial_reserves_usd))
        f.write("\nratio_sec_usd: " + str(ratios_sec_usd))
        f.write("\ncauchy_scale_x: " + str(cauchy_scale_x))
        f.write("\ncauchy_scale_y: " + str(cauchy_scale_y))
        f.write("\ncauchy_max_limit_x: " + str(cauchy_max_limit_x))
        f.write("\ncauchy_max_limit_y: " + str(cauchy_max_limit_y))
        f.write("\nprice_tolerance_threshold: " + str(settings.PRICE_TOLLERANCE_THRESHOLD))
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
    simulation_seconds_total = 60*24*50

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