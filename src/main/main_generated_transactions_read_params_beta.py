import os, sys
sys.path.insert(0, os.getcwd()) 

import enum
import logging
from sre_constants import SUCCESS
import pandas as pd
import amm
import json
import os
import numpy as np
from datetime import date, datetime, timedelta
from trading_simulation import MonteCarloTransactionSimulator, PoissonGenerator, Transaction, WeibullGenerator
import blockchain
from big_numbers import contract_18_decimals_to_float, expand_to_18_decimals
from safe_math import q_decode_144
from transactions import SwapTransaction, TransactionStatus
from utils import normalize_csv, normalize_pool_state, save_dict


logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(name)s:%(message)s', datefmt="%m/%d/%Y %I:%M:%S %p")
logger = logging.getLogger(__name__)

EXPERIMENT_ID = 80
SIM_MESSAGE = 'test'

X_NAME = 'X'
Y_NAME = 'Y'

# todo: check ratio

class VMRejectionAlertBehaviour(enum.Enum):
    NONE = 0
    SINGLE_SMALLER_ALLOWED_SWAP = 1
    SEQUENCE_SMALLER_ALLOWED_SWAPS = 2


def main(): 
    OCCURENCES_PER_MIN = 1 / 30
    INITIAL_SEC_PRICE = 1

    WINDOW_SIZE = 24
    GRANULARITY = 24
    PRICE_TOLLERANCE_THRESHOLD = 98

    DIST_LOC = 0
    DEFAULT_SLIPPAGE = 50


    BASE_DIR = f'../data/simulated_transactions_grid_dist/experiment_{EXPERIMENT_ID}'
    os.makedirs(BASE_DIR)
    
    config = {
        'window_size': WINDOW_SIZE,
        'granularity': GRANULARITY,
        'price_tollerance_threshold': PRICE_TOLLERANCE_THRESHOLD,
        'slippage': DEFAULT_SLIPPAGE,
        'sim_message': SIM_MESSAGE
    }
    save_dict(f'{BASE_DIR}/config.json', config)

    logger.info("starting...")
    
    iteration = 0
    start_time = datetime.now()

    with open('../data_input/params_m2.json') as f:
        params_config = json.load(f)

    for params in params_config:
        a, b = params['reserve_range']

        if a > 50000:
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
            
            for subindex, vm in enumerate([(False, VMRejectionAlertBehaviour.NONE), (True, VMRejectionAlertBehaviour.NONE),
                                            (True, VMRejectionAlertBehaviour.SINGLE_SMALLER_ALLOWED_SWAP), (True, VMRejectionAlertBehaviour.SEQUENCE_SMALLER_ALLOWED_SWAPS)]):
                vm_mode, rejection_risk_action = vm
                os.makedirs(f'{BASE_DIR}/{iteration}/{subindex}')

                config = {
                    'freq_X': OCCURENCES_PER_MIN,
                    'freq_Y': OCCURENCES_PER_MIN,
                    'initial_reserve_usd': initial_reserves_usd,
                    'initial_sec_price': INITIAL_SEC_PRICE,
                    'scale': scale,
                    'shape': shape,
                    'vm': vm_mode,
                    'slippage': DEFAULT_SLIPPAGE,
                    'rejection_risk_action': rejection_risk_action.name
                }
                
                
                save_dict(f'{BASE_DIR}/{iteration}/{subindex}/config.txt', config)
                amm.reset(X_NAME, Y_NAME, initial_reserves_usd // INITIAL_SEC_PRICE , initial_reserves_usd, vm_mode, WINDOW_SIZE * 60 * 60, WINDOW_SIZE * 60 * 60// GRANULARITY, GRANULARITY) #todo: beautify

                cnt = 0
                swap_decrease_factor_numerator = 3
                swap_decrease_factor_denominator = 4

                swap_timestamp_shift = timedelta(seconds=0)

                for _, row in all_transactions.iterrows():
                    amm.reserve_X() / amm.reserve_Y()
                    
                    if row['datetime_timestamp'] - start_time <= timedelta(days=1):
                        amount = row['token_in_amount'] // 1000 
                    else:
                        amount = row['token_in_amount']

                    if vm == False or rejection_risk_action == VMRejectionAlertBehaviour.NONE:
                        amm.swap(cnt, Transaction(row['datetime_timestamp'], amount, row['token_in'], row['token_out']), DEFAULT_SLIPPAGE)
                        cnt += 1

                    elif rejection_risk_action == VMRejectionAlertBehaviour.SINGLE_SMALLER_ALLOWED_SWAP:
                        desired_swap_amount = amount

                        for attempt in range(0, 6):
                            if attempt == 5 or amm.verify_swap(cnt, Transaction(row['datetime_timestamp'], amount, row['token_in'], row['token_out']), DEFAULT_SLIPPAGE) == TransactionStatus.SUCCESS:
                                amm.swap(cnt, Transaction(row['datetime_timestamp'], amount, row['token_in'], row['token_out'],
                                                    sequence_swap_cnt=0, desired_token_in_amount=desired_swap_amount, attempt_cnt=attempt), DEFAULT_SLIPPAGE)

                                cnt += 1
                                break
                            amount = amount * swap_decrease_factor_numerator // swap_decrease_factor_denominator


                    elif rejection_risk_action == VMRejectionAlertBehaviour.SEQUENCE_SMALLER_ALLOWED_SWAPS:
                        desired_swap_amount = amount
                        swapped_amount = 0

                        max_swaps = 5
                        max_tries = 10
                        curr_swaps = 0

                        for attempt in range(0, max_tries):
                            if swapped_amount >= desired_swap_amount or curr_swaps >= max_swaps:
                                break
                                
                            if attempt == max_tries - 1 or amm.verify_swap(cnt, Transaction(row['datetime_timestamp']+swap_timestamp_shift, amount, row['token_in'], row['token_out']), DEFAULT_SLIPPAGE) == TransactionStatus.SUCCESS:
                                amm.swap(cnt, Transaction(row['datetime_timestamp']+swap_timestamp_shift, amount, row['token_in'], row['token_out'], 
                                                    sequence_swap_cnt=curr_swaps, desired_token_in_amount=desired_swap_amount, attempt_cnt=attempt), DEFAULT_SLIPPAGE)
                                
                                if swapped_amount < desired_swap_amount and curr_swaps + 1< max_swaps:
                                    swap_timestamp_shift += timedelta(seconds=16)

                                swapped_amount += amount
                                curr_swaps += 1
                                cnt += 1

                                amount = min(amount, desired_swap_amount - swapped_amount)
                            else:
                                amount = min(amount * swap_decrease_factor_numerator // swap_decrease_factor_denominator, desired_swap_amount - swapped_amount)


                SwapTransaction.save_all(f'{BASE_DIR}/{iteration}/{subindex}/swaps.csv')
                blockchain.reset_state()

                amm.export_pool_states_to_csv(f'{BASE_DIR}/{iteration}/{subindex}/pool_before_transaction.csv', 
                                                f'{BASE_DIR}/{iteration}/{subindex}/pool_after_transaction.csv')

                logger.info("Start normalizing...")
                normalize_csv(f'{BASE_DIR}/{iteration}/{subindex}/swaps.csv', ['token_in_amount', 'token_out_amount', 'token_out_amount_min', 'system_fee', 'oracle_amount_out', 'oracle_price', 'desired_token_in_amount'], f'{BASE_DIR}/{iteration}/{subindex}/swaps_normalized.csv')
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
    simulation_mins = 60*24

    current_iteration_timestamp = simulator.get_transactions(current_iteration_timestamp, simulation_mins)

    simulation_mins = 60*24*25
    simulator.frequency_generator.mean_occurencies = mean_occurencies_per_min

    current_iteration_timestamp = simulator.get_transactions(current_iteration_timestamp, simulation_mins)

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