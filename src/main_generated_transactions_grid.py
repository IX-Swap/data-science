import logging
from random import randrange
import itertools
import pandas as pd
import amm
import os
import numpy as np
from datetime import datetime, timedelta
from monte_carlo_dc import CauchyGenerator, MonteCarloTransactionSimulator, PoissonGenerator, Transaction
import blockchain
from big_numbers import contract_18_decimals_to_float, expand_to_18_decimals
from safe_math import q_decode_144
import settings

# old main, required update (using main_historic_transactions.py)

logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(name)s:%(message)s', datefmt="%m/%d/%Y %I:%M:%S %p")
logger = logging.getLogger(__name__)

EXPERIMENT_ID = 38
X_NAME = 'HKMT'
Y_NAME = 'USDT'

def main(): 
    occurences_per_min_list = [10]
    initial_reserves_usd_list = [1000, 10000, 100000]
    ratios_sec_usd_list = [1]
    cauchy_scale_list = [5000, 10000, 15000]
    volatility_mitigator_list = [False, True]
    price_tollerance_threshold_list = [98]
    window_size_list = [24]
    granularity_list = [24] #todo: update period

    

    grid = itertools.product(occurences_per_min_list, initial_reserves_usd_list, ratios_sec_usd_list, cauchy_scale_list, price_tollerance_threshold_list, window_size_list, granularity_list, volatility_mitigator_list)

    os.makedirs(f'data/experiment_{EXPERIMENT_ID}')
    
    with open(f'data/experiment_{EXPERIMENT_ID}/config.txt', 'w') as f:
        f.write('\noccurences_per_min_list: ' + str(occurences_per_min_list))
        f.write('\ninitial_reserves_usd_list: ' + str(initial_reserves_usd_list))
        f.write('\nratios_sec_usd_list: ' + str(ratios_sec_usd_list))
        f.write('\ncauchy_scale_list: ' + str(cauchy_scale_list))
        f.write('\nvolatility_mitigator_list: ' + str(volatility_mitigator_list))
        f.write('\nprice_tollerance_threshold_list: ' + str(price_tollerance_threshold_list))
        f.write('\nwindow_size_list: ' + str(window_size_list))
        f.write('\ngranularity_list: ' + str(granularity_list))


    start_time = datetime.now()
    iteration = 0
    print("starting...")
    for mean_occurencies_per_min, initial_reserves_usd, ratios_sec_usd, cauchy_scale, price_tollerance_threshold, window_size, granularity, vm in grid:
        settings.PRICE_TOLLERANCE_THRESHOLD = price_tollerance_threshold

        os.makedirs(f'data/experiment_{EXPERIMENT_ID}/{iteration}')
        save_config(f'data/experiment_{EXPERIMENT_ID}/{iteration}/config.txt', mean_occurencies_per_min, initial_reserves_usd, ratios_sec_usd, cauchy_scale, price_tollerance_threshold, window_size, granularity, vm)

        transactions_history1_path = f'data/experiment_{EXPERIMENT_ID}/{iteration}/history1.csv'
        transactions_history2_path = f'data/experiment_{EXPERIMENT_ID}/{iteration}/history2.csv'

        simulate_transactions(start_time, mean_occurencies_per_min, X_NAME, Y_NAME, transactions_history1_path, cauchy_scale, 1)
        simulate_transactions(start_time, mean_occurencies_per_min, Y_NAME, X_NAME, transactions_history2_path, cauchy_scale, 1)

        transactions1_df = pd.read_csv(transactions_history1_path)
        transactions2_df = pd.read_csv(transactions_history2_path)

        all_transactions = combine_transactions(transactions1_df, transactions2_df)
        all_transactions['token_in_amount'] = all_transactions['token_in_amount'].apply(expand_to_18_decimals)

        cnt = 0
        amm.reset(X_NAME, Y_NAME, initial_reserves_usd / ratios_sec_usd, initial_reserves_usd, vm)

        start_time = all_transactions['datetime_timestamp'].min()



        for _, row in all_transactions.iterrows():
            amm.reserve_X() / amm.reserve_Y()
            
            if row['datetime_timestamp'] - start_time <= timedelta(days=1):
                amount = row['token_in_amount'] // 50
            else:
                amount = row['token_in_amount']
                
            amm.swap(cnt, Transaction(row['datetime_timestamp'], amount, row['token_in'], row['token_out'], row['slope']))
            cnt += 1

        blockchain.transaction_to_csv(f'data/experiment_{EXPERIMENT_ID}/{iteration}/blockchain.csv', True)
        amm.export_pool_states_to_csv(f'data/experiment_{EXPERIMENT_ID}/{iteration}/pool_before_transaction.csv', 
                                        f'data/experiment_{EXPERIMENT_ID}/{iteration}/pool_after_transaction.csv')

        logger.info("Start normalizing...")
        normalize_blockchain(f'data/experiment_{EXPERIMENT_ID}/{iteration}/blockchain.csv', f'data/experiment_{EXPERIMENT_ID}/{iteration}/blockchain_normalized.csv')
        normalize_pool_state(f'data/experiment_{EXPERIMENT_ID}/{iteration}/pool_before_transaction.csv', f'data/experiment_{EXPERIMENT_ID}/{iteration}/pool_before_transaction_normalized.csv')
        normalize_pool_state(f'data/experiment_{EXPERIMENT_ID}/{iteration}/pool_after_transaction.csv', f'data/experiment_{EXPERIMENT_ID}/{iteration}/pool_after_transaction_normalized.csv')
        logging.info("Finished normalizing")

        iteration += 1

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

def save_config(filename, mean_occurencies_per_min, initial_reserves_usd, ratios_sec_usd, cauchy_scale, price_tollerance_threshold, window_size, granularity, vm):
    with open(filename, 'w') as f:
        f.write("mean_occ_per_min: " + str(mean_occurencies_per_min))
        f.write("\ninitial_reserve_usd: " + str(initial_reserves_usd))
        f.write("\nratio_sec_usd: " + str(ratios_sec_usd))
        f.write("\ncauchy_scale: " + str(cauchy_scale))
        f.write("\nprice_tolerance_threshold: " + str(settings.PRICE_TOLLERANCE_THRESHOLD))
        f.write("\nwindow_size: " + str(window_size))
        f.write("\ngranularity: " + str(granularity)) #todo: read from settings
        f.write("\nvolatility_mitigator: " + str(vm)) #todo: read from settings




def simulate_transactions(start_time, mean_occurencies_per_min, token0, token1, transaction_history_filename, cauchy_scale, token_in_ratio):
    simulator = MonteCarloTransactionSimulator(
        PoissonGenerator(cycle_size=60000, mean_occurencies=mean_occurencies_per_min), 
        CauchyGenerator(loc=0, scale=cauchy_scale, limit=3000000), token0, token1,
    )

    start_time = datetime.now()

    current_iteration_timestamp = start_time

    # total_number_transactions = 50000
    # simulation_seconds_total = int((total_number_transactions + 24*60*mean_occurencies_per_min) / mean_occurencies_per_min) 
    simulation_seconds_total = 60*24*7

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