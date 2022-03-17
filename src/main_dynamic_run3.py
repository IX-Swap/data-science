import json
import logging
import random
import shutil
import numpy as np
import pandas as pd
import scipy
import amm
import os
from datetime import datetime, timedelta
from monte_carlo2 import  MonteCarloTransactionSimulator, PoissonGenerator, WeibullGenerator
from monte_carlo import Transaction
import blockchain
from big_numbers import contract_18_decimals_to_float, expand_to_18_decimals
from transactions import SwapTransaction, TransactionStatus
from utils import get_reserve_range_index, get_reserve_range_index2, normalize_csv, normalize_pool_state, parse_dynamic_config, save_dict


logging.basicConfig(level=logging.ERROR, format='%(asctime)s:%(name)s:%(message)s', datefmt="%m/%d/%Y %I:%M:%S %p")
logger = logging.getLogger(__name__)


EXPERIMENT_ID = 78
X_NAME = 'X'
Y_NAME = 'Y'

# todo: check ratio  
#   
def main(): 
    logger.info("starting...")

    INITIAL_RESERVES_USD = 75000
    INITIAL_SEC_PRICE = 1

    WINDOW_SIZE = 24
    GRANULARITY = 24
    PRICE_TOLLERANCE_THRESHOLD = 98
    DEFAULT_SLIPPAGE = 100

    BASE_DIR = f'../data/dynamic_simulations/experiment_{EXPERIMENT_ID}'
    os.makedirs(BASE_DIR)

    config = {
        'window_size': WINDOW_SIZE,
        'granularity': GRANULARITY,
        'price_tollerance_threshold': PRICE_TOLLERANCE_THRESHOLD,
        'initial_reserve_usd': INITIAL_RESERVES_USD
    }

    save_dict(f'{BASE_DIR}/config.json', config)

    with open('params_m2.json') as f:
        reserve_range_params_list = json.loads(f.read())

    with open('actions.txt') as f:
        s = f.read()

    shutil.copy('actions.txt', BASE_DIR)
    
    start_time = datetime.now()
    iteration = 0

    for x in [75000]:#[500, 5500, 30000, 75000, 150000, 350000, 750000, 5500000, 505000000]:
        INITIAL_RESERVES_USD = x #todo: refactor
        for i in range(len(reserve_range_params_list[0]['shape'])):
            scale_list = []
            shape_list = []

            for reserve_range_params in reserve_range_params_list:
                scale = reserve_range_params['scale'][i]
                shape = reserve_range_params['shape'][i]

                scale_list.append(scale)
                shape_list.append(shape)

            os.makedirs(f'{BASE_DIR}/{iteration}')

        #    transactions_history_path = f'{BASE_DIR}/{iteration}/transaction_history.csv'
            
            transactions = simulate_transactions(start_time)
            
            for subindex, vm in enumerate([True]):
                os.makedirs(f'{BASE_DIR}/{iteration}/{subindex}')
                amm.reset(X_NAME, Y_NAME, INITIAL_RESERVES_USD // INITIAL_SEC_PRICE , INITIAL_RESERVES_USD, vm, WINDOW_SIZE * 60 * 60, WINDOW_SIZE * 60 * 60// GRANULARITY, GRANULARITY) #todo: beautify

                reserve_X, reserve_Y = contract_18_decimals_to_float(amm.reserve_X()), contract_18_decimals_to_float(amm.reserve_Y()) # todo: convert to float
                
                reserve_range_index_ = get_reserve_range_index(reserve_Y)
                shape_ = shape_list[reserve_range_index_]
                scale_ = scale_list[reserve_range_index_]
                config['volatility_mitigator'] = vm
                config['shape'] = shape_
                config['scale'] = scale_
                config['initial_reserve_usd'] = INITIAL_RESERVES_USD

                save_dict(f'{BASE_DIR}/{iteration}/{subindex}/config.json', config)

                cnt = 0
                swap_decrease_factor_numerator = 3
                swap_decrease_factor_denominator = 4

                for timestamp, cummulative_freq, scale_deviation, token_in, token_out in transactions:
                    reserve_X, reserve_Y = contract_18_decimals_to_float(amm.reserve_X()), contract_18_decimals_to_float(amm.reserve_Y()) # todo: convert to float
                    
                    reserve_range_index = get_reserve_range_index2(reserve_Y)
                    shape = shape_list[reserve_range_index]
                    scale = scale_list[reserve_range_index] * scale_deviation

                    amount_in = scipy.stats.weibull_min.ppf(cummulative_freq, shape_, loc=0, scale=scale_ * scale_deviation)## c freq
                    amount_in = expand_to_18_decimals(amount_in)

                    if timestamp - start_time <= timedelta(days=1):
                        amount_in = amount_in // 1000 
                
                   # amm.swap(cnt, Transaction(timestamp, amount_in, token_in, tokenxz_out, 100))
                    desired_swap_amount = amount_in
                    amm.swap(cnt, Transaction(timestamp, amount_in, token_in, token_out,
                                        sequence_swap_cnt=0, desired_token_in_amount=desired_swap_amount), DEFAULT_SLIPPAGE)
                    last_timestamp = timestamp
                    cnt += 1
                    # for attempt in range(0, 6):
                    #     if attempt == 5 or amm.verify_swap(cnt, Transaction(timestamp, amount_in, token_in, token_out), DEFAULT_SLIPPAGE) == TransactionStatus.SUCCESS:
                    #         amm.swap(cnt, Transaction(timestamp, amount_in, token_in, token_out,
                    #                             sequence_swap_cnt=0, desired_token_in_amount=desired_swap_amount, attempt_cnt=attempt), DEFAULT_SLIPPAGE)

                    #         cnt += 1
                    #         break
                    #     amount_in = amount_in * swap_decrease_factor_numerator // swap_decrease_factor_denominator


                    # rand = random.randint(1, 300)
                    #if timestamp - start_time > timedelta(days=1): #and rand == 1:
                        # last_timestamp = timestamp
                        # # todo: update reserves
                        # side = random.randint(0, 1)
                        # slice = random.randint(25, 35)

                        # if side == 0:
                        #     amount_in = amm.reserve_X() * slice // 100

                        #     amm.swap(cnt, Transaction(last_timestamp, amount_in, X_NAME, Y_NAME, 100))
                        # else:
                        #     amount_in = amm.reserve_Y() * slice // 100

                        #     amm.swap(cnt, Transaction(last_timestamp, amount_in, Y_NAME, X_NAME, 100))
                        # cnt += 1
                        # last_timestamp = timestamp
                

                for i in range(1446):
                    low = 0
                    high = expand_to_18_decimals('10000000000')
                    blockchain.update(int(last_timestamp.timestamp())+15) # ???

                    while low <= high:
                        mid = (low + high) // 2

                        transaction = SwapTransaction(Transaction(last_timestamp, mid, X_NAME, Y_NAME, 100), DEFAULT_SLIPPAGE, amm._amm, cnt)
                        transaction.block_timestamp = int(last_timestamp.timestamp()) + 15
                        SwapTransaction.instances = SwapTransaction.instances[:-1]

                        is_ok = (transaction.check_execute_status(transaction.block_timestamp) == TransactionStatus.SUCCESS)
                    #    print(contract_18_decimals_to_float(mid), is_ok)

                        if is_ok:
                            low = mid + 1
                            assert (transaction.check_execute_status(transaction.block_timestamp) == TransactionStatus.SUCCESS), 'Error'
                        else:
                            high = mid - 1

                    if low > expand_to_18_decimals('10000000000') or low-1==0:
                        print("Unable to find amount in range, error")

                        if i>5:
                            last_timestamp += timedelta(seconds=60)
                        else:
                            last_timestamp += timedelta(seconds=60)
                        continue
                        #break

                    amm.swap(cnt, Transaction(last_timestamp, low-1, X_NAME, Y_NAME, 100), DEFAULT_SLIPPAGE)
                    # print('Swap size:', contract_18_decimals_to_float(low - 1), last_timestamp)
                    if i>5:
                        last_timestamp += timedelta(seconds=60)
                    else:
                        last_timestamp += timedelta(seconds=60)
                    cnt += 1

                SwapTransaction.save_all(f'{BASE_DIR}/{iteration}/{subindex}/swaps.csv')
                blockchain.reset_state()

                amm.export_pool_states_to_csv(f'{BASE_DIR}/{iteration}/{subindex}/pool_before_transaction.csv', 
                                                f'{BASE_DIR}/{iteration}/{subindex}/pool_after_transaction.csv')

                logger.info("Start normalizing...")
                normalize_csv(f'{BASE_DIR}/{iteration}/{subindex}/swaps.csv', ['token_in_amount', 'token_out_amount', 'token_out_amount_min', 'system_fee', 'oracle_amount_out', 'oracle_price'], f'{BASE_DIR}/{iteration}/{subindex}/swaps_normalized.csv')
                normalize_pool_state(f'{BASE_DIR}/{iteration}/{subindex}/pool_before_transaction.csv', f'{BASE_DIR}/{iteration}/{subindex}/pool_before_transaction_normalized.csv')
                normalize_pool_state(f'{BASE_DIR}/{iteration}/{subindex}/pool_after_transaction.csv', f'{BASE_DIR}/{iteration}/{subindex}/pool_after_transaction_normalized.csv')
                logging.info("Finished normalizing")


            iteration += 1


def get_timestamps(start_time, periods, freq):
    time_between_events = []
    time_elapsed = 0

    while (True):
        values = scipy.stats.expon.rvs(size=1000, scale=1/freq)

        for i in range(len(values)):
            time_elapsed += values[i]

            if (time_elapsed + values[i] > periods):
                timestamps = [start_time]
                
                for x in time_between_events:
                    timestamps.append(timestamps[-1] + timedelta(hours=x))
                    
                return timestamps

            time_between_events.append(values[i])
          #  print(time_elapsed)


def get_transactions(start_time, periods, freq): # periouds - hours
    timestamps = get_timestamps(start_time, periods, freq)
    cumulative_values = np.random.uniform(0, 1, len(timestamps))
    
    return cumulative_values, timestamps


def simulate_transactions(start_time):
    params, actions = parse_dynamic_config('actions.txt')

    timestamps = {
        X_NAME: [],
        Y_NAME: []
    }

    cummulative_frequencies = {
        X_NAME: [],
        Y_NAME: []
    }

    scale_deviations = {
        X_NAME: 1,
        Y_NAME: 1
    }

    freq_deviations = {
        X_NAME: 0,
        Y_NAME: 0
    }

    scale_deviations_list = {
        X_NAME: [],
        Y_NAME: []
    }
    
    for action in actions:
        if action[0] == 'PASS':
            cycles = action[1] # todo: rename, same unit

            X_freq = params[X_NAME]['freq'] + freq_deviations[X_NAME]
            Y_freq = params[Y_NAME]['freq'] + freq_deviations[Y_NAME]
            hours = cycles / 60

            print( X_freq*60)
            print('!\n\n\n\n\n\n')

            X_cummulative_frequencies, X_timestamps = get_transactions(start_time, hours, X_freq*60)
            Y_cummulative_frequencies, Y_timestamps = get_transactions(start_time, hours, Y_freq*60)

            print(f"hours: {hours:.2f}, X_freq: {X_freq:.2f},  X_count: {len(X_cummulative_frequencies)}, Y_count: {len(Y_cummulative_frequencies)}")
          #  print(X_timestamps[:10])

            timestamps[X_NAME].extend(X_timestamps)
            timestamps[Y_NAME].extend(Y_timestamps)

            cummulative_frequencies[X_NAME].extend(X_cummulative_frequencies)
            cummulative_frequencies[Y_NAME].extend(Y_cummulative_frequencies)

            scale_deviations_list[X_NAME].extend([scale_deviations[X_NAME]] * len(X_timestamps))
            scale_deviations_list[Y_NAME].extend([scale_deviations[Y_NAME]] * len(Y_timestamps))

            start_time += timedelta(minutes=cycles)
        elif action[0] == 'INC' or action[1] == 'DEC':
            token, param, value = action[1], action[2], action[3]

            if action[0] == 'DEC':
                value = -value

            if param == 'scale':
                scale_deviations[token] *= (1 + value/100)
            else:
                freq_deviations[token] += value
        elif action[0] == 'NORMALIZE':
            token, param = action[1], action[2]

            if param == 'scale':
                scale_deviations[token] = 1
            else:
                freq_deviations[token] = 0

    X_transactions = list(zip(timestamps[X_NAME], cummulative_frequencies[X_NAME], scale_deviations_list[X_NAME], [X_NAME] * len(timestamps[X_NAME]), [Y_NAME] * len(timestamps[X_NAME])))
    Y_transactions = list(zip(timestamps[Y_NAME], cummulative_frequencies[Y_NAME], scale_deviations_list[Y_NAME], [Y_NAME] * len(timestamps[Y_NAME]), [X_NAME] * len(timestamps[Y_NAME])))

    all_transactions = X_transactions + Y_transactions
    all_transactions = sorted(all_transactions, key=lambda x: x[0])

    return all_transactions


if __name__ == '__main__':
    main()