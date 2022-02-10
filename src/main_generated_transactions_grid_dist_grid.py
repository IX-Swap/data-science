import logging
import itertools
import pandas as pd
import amm
import os
import numpy as np
from datetime import datetime, timedelta
from monte_carlo import  MonteCarloTransactionSimulator, PoissonGenerator, Transaction, WeibullGenerator
import blockchain
from big_numbers import contract_18_decimals_to_float, expand_to_18_decimals
from safe_math import q_decode_144
import settings
from transactions import SwapTransaction



logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(name)s:%(message)s', datefmt="%m/%d/%Y %I:%M:%S %p")
logger = logging.getLogger(__name__)

EXPERIMENT_ID = 5

X_NAME = 'X'
Y_NAME = 'Y'

# todo: check ratio

def main(): 
    OCCURENCES_PER_MIN = 1
   # INITIAL_RESERVES_USD = 10000
    INITIAL_SEC_PRICE = 1

    WINDOW_SIZE = 24
    GRANULARITY = 24
    PRICE_TOLLERANCE_THRESHOLD = 98

    DIST_LOC = 0
    initial_reserves_usd = [30000]
    scale_list = [75, 600, 1300, 1600]
    shape_list = [0.7, 1.1, 1.35, 1.65]
    # initial_reserves_usd = [350000]
    # scale_list = [500, 3500, 6300, 7500]
    # shape_list = [0.75, 1.1, 1.3, 1.4, 1.5]
    # scale_list = [160, 2000, 4200, 5000]
    # shape_list = [0.7, 1.2, 1.7, 1.9]
    #scale_list =  [75, 600, 1300, 1600]
    #shape_list =  [0.7, 1.1, 1.35, 1.65]
    # scale_list = [400, 2500, 4000, 5000]
    # shape_list = [0.8, 1.05, 1.2, 1.35]

    grid_dist_params = itertools.product(scale_list, shape_list, initial_reserves_usd)

    BASE_DIR = f'../data/simulated_transactions_grid_dist_grid/experiment_{EXPERIMENT_ID}'
    os.makedirs(BASE_DIR)
    
    with open(f'{BASE_DIR}/config.txt', 'w') as f:
        f.write('\window_size: ' + str(WINDOW_SIZE))
        f.write('\ngranularity: ' + str(GRANULARITY))
        f.write('\nprice_tollerance_threshold: ' + str(PRICE_TOLLERANCE_THRESHOLD))

        f.write('\ninitial_reserves_usd: ' + str(initial_reserves_usd))
        f.write('\nscale_list: ' + str(scale_list))
        f.write('\nshape_list: ' + str(shape_list))

    logger.info("starting...")
    
    start_time = datetime.now()
    iteration = 0

    for scale, shape, initial_reserves_usd in grid_dist_params:
        print('iteration', iteration)
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

        subindex0 = 0

        for slippage in [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]:
            for subindex, vm in enumerate([False, True]):
                os.makedirs(f'{BASE_DIR}/{iteration}/{subindex0}/{subindex}')
                save_config(f'{BASE_DIR}/{iteration}/{subindex0}/{subindex}/config.txt', OCCURENCES_PER_MIN, initial_reserves_usd, INITIAL_SEC_PRICE, scale, shape, PRICE_TOLLERANCE_THRESHOLD, WINDOW_SIZE, GRANULARITY, vm, slippage)

                amm.reset(X_NAME, Y_NAME, initial_reserves_usd // INITIAL_SEC_PRICE , initial_reserves_usd, vm, WINDOW_SIZE * 60 * 60, WINDOW_SIZE * 60 * 60// GRANULARITY, GRANULARITY) #todo: beautify

                cnt = 0
                for _, row in all_transactions.iterrows():
                    amm.reserve_X() / amm.reserve_Y()
                    
                    if row['datetime_timestamp'] - start_time <= timedelta(days=1):
                        amount = row['token_in_amount'] // 1000 
                    else:
                        amount = row['token_in_amount']
                        
                    amm.swap(cnt, Transaction(row['datetime_timestamp'], amount, row['token_in'], row['token_out'], slippage))
                    cnt += 1

                SwapTransaction.save_all(f'{BASE_DIR}/{iteration}/{subindex0}/{subindex}/swaps.csv')
                blockchain.reset_state()

                amm.export_pool_states_to_csv(f'{BASE_DIR}/{iteration}/{subindex0}/{subindex}/pool_before_transaction.csv', 
                                                f'{BASE_DIR}/{iteration}/{subindex0}/{subindex}/pool_after_transaction.csv')

                logger.info("Start normalizing...")
                normalize_csv(f'{BASE_DIR}/{iteration}/{subindex0}/{subindex}/swaps.csv', ['token_in_amount', 'token_out_amount', 'token_out_amount_min', 'system_fee', 'oracle_amount_out', 'oracle_price'], f'{BASE_DIR}/{iteration}/{subindex0}/{subindex}/swaps_normalized.csv')
                normalize_pool_state(f'{BASE_DIR}/{iteration}/{subindex0}/{subindex}/pool_before_transaction.csv', f'{BASE_DIR}/{iteration}/{subindex0}/{subindex}/pool_before_transaction_normalized.csv')
                normalize_pool_state(f'{BASE_DIR}/{iteration}/{subindex0}/{subindex}/pool_after_transaction.csv', f'{BASE_DIR}/{iteration}/{subindex0}/{subindex}/pool_after_transaction_normalized.csv')
                logging.info("Finished normalizing")

            subindex0 += 1

        iteration += 1
        print("INCREASE iteration", iteration)

def normalize_csv(filename, cols_to_normalize, normalized_filename):
    df = pd.read_csv(filename)

    for col in cols_to_normalize:
        df[col] = df[col].apply(contract_18_decimals_to_float)
    
    df.to_csv(normalized_filename, index=False)





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

def save_config(filename, mean_occurencies_per_min, initial_reserves_usd, ratios_sec_usd, scale, shape, price_tollerance_threshold, window_size, granularity, vm, slippage):
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
        f.write("\nslippage: " + str(slippage))




def simulate_transactions(start_time, mean_occurencies_per_min, token0, token1, transaction_history_filename, shape, loc, scale):
    simulator = MonteCarloTransactionSimulator(
        PoissonGenerator(cycle_size=60000, mean_occurencies=mean_occurencies_per_min), 
        WeibullGenerator(shape=shape, loc=loc, scale=scale), token0, token1,
    )

    start_time = datetime.now()

    current_iteration_timestamp = start_time

    # total_number_transactions = 50000
    # simulation_seconds_total = int((total_number_transactions + 24*60*mean_occurencies_per_min) / mean_occurencies_per_min) 
    simulation_seconds_total = 60*24*2

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