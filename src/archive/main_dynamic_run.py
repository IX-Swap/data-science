import json
import logging
import re
import numpy as np
import pandas as pd
import amm
import os
from datetime import datetime, timedelta
from monte_carlo2 import  MonteCarloTransactionSimulator, PoissonGenerator, Transaction, WeibullGenerator
import blockchain
from big_numbers import contract_18_decimals_to_float, expand_to_18_decimals
from transactions import SwapTransaction
from utils import get_reserve_range_index, normalize_csv, normalize_pool_state, save_dict


logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(name)s:%(message)s', datefmt="%m/%d/%Y %I:%M:%S %p")
logger = logging.getLogger(__name__)


EXPERIMENT_ID = 47
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

    BASE_DIR = f'../data/dynamic_simulations/experiment_{EXPERIMENT_ID}'
    os.makedirs(BASE_DIR)

    config = {
        'window_size': WINDOW_SIZE,
        'granularity': GRANULARITY,
        'price_tollerance_threshold': PRICE_TOLLERANCE_THRESHOLD,
        'initial_reserves_usd': INITIAL_RESERVES_USD
    }

    save_dict(f'{BASE_DIR}/config.json', config)

    with open('params.json') as f:
        reserve_range_params_list = json.loads(f.read())

    start_time = datetime.now()
    iteration = 0

    for i in range(7, 8):#range(len(reserve_range_params_list[0]['shape'])):
        scale_list = []
        shape_list = []

        for reserve_range_params in reserve_range_params_list:
            scale = reserve_range_params['scale'][i]
            shape = reserve_range_params['shape'][i]

            scale_list.append(scale)
            shape_list.append(shape)

        for subindex, vm in enumerate([False, True]):
            os.makedirs(f'{BASE_DIR}/{iteration}/{subindex}')
            amm.reset(X_NAME, Y_NAME, INITIAL_RESERVES_USD // INITIAL_SEC_PRICE , INITIAL_RESERVES_USD, vm, WINDOW_SIZE * 60 * 60, WINDOW_SIZE * 60 * 60// GRANULARITY, GRANULARITY) #todo: beautify

            config['volatility_mitigator'] = vm
            save_dict(f'{BASE_DIR}/{iteration}/{subindex}/config.json', config)

            cnt = 0
            for transaction in simulate_transactions(start_time, INITIAL_RESERVES_USD, INITIAL_SEC_PRICE, scale_list, shape_list, f'{BASE_DIR}/{iteration}/{subindex}/transaction_history.csv'):
               # print(cnt, transaction.name)
                assert cnt == transaction.name, f'CNT / transaction.index mismatch, cnt = {cnt}, transaction.index = {transaction.index}'
                if transaction['datetime_timestamp'] - start_time <= timedelta(days=1):
                    amount = transaction['token_in_amount'] // 1000 
                else:
                    amount = transaction['token_in_amount']
                    
                amm.swap(cnt, Transaction(transaction['datetime_timestamp'], amount, transaction['token_in'], transaction['token_out'], transaction['slope']))
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

def simulate_transactions(current_iteration_timestamp, initial_reserve, initial_sec_price, scale_list, shape_list, transaction_history_path):
    cycle_size = 60000 # 60 000ms = 60s = 1min

    params, actions = parse_dynamic_config('actions.txt')
    params_deviations = {
        'X': {
            'shape': 0,
            'freq': 0,
            'scale': [], # percentage deviations
        },
        'Y': {
            'shape': 0,
            'freq': 0,
            'scale': [],
        },
    }

    reserve_range_index = get_reserve_range_index(initial_reserve)

    X_scale = scale_list[reserve_range_index] 
    Y_scale = scale_list[reserve_range_index]

    params['Y']['shape'] = params['X']['shape'] = shape_list[reserve_range_index]
    params['X']['scale'] = X_scale
    params['Y']['scale'] = Y_scale

    x_swaps_simulator = MonteCarloTransactionSimulator(
        PoissonGenerator(cycle_size=cycle_size, mean_occurencies=params['X']['freq']), 
        WeibullGenerator(shape=params['X']['shape'], loc=0, scale=params['X']['scale']), 'X', 'Y',
    )

    y_swaps_simulator = MonteCarloTransactionSimulator(
        PoissonGenerator(cycle_size=cycle_size, mean_occurencies=params['Y']['freq']), 
        WeibullGenerator(shape=params['Y']['shape'], loc=0, scale=params['Y']['scale']), 'Y', 'X',
    )

    all_swaps = pd.DataFrame(columns=[
        'datetime_timestamp', 'token_in', 'token_in_amount', 'token_out', 'token_out_amount', 'slope'
    ])

    prices = []
    prev_reserve_range_index = 3
    price_scale = 1

    for action in actions:
        if action[0] == 'PASS':
            #todo: set simulator params
            cycles = action[1]

            # adjust params to current reserves
            # todo: implement big number arithmetics

            for _ in range(cycles):
                reserve_X, reserve_Y = contract_18_decimals_to_float(amm.reserve_X()), contract_18_decimals_to_float(amm.reserve_Y()) # todo: convert to float

                reserve_range_index = get_reserve_range_index(reserve_Y)

                shape = shape_list[reserve_range_index]
                scale = scale_list[reserve_range_index]
                #print(reserve_Y, reserve_range_index, shape)
                
                X_scale = scale_list[reserve_range_index] 
                Y_scale = scale_list[reserve_range_index]

                params['Y']['shape'] = params['X']['shape'] = shape
                params['Y']['scale'] = params['X']['scale'] = scale

                for deviation in params_deviations['X']['scale']:
                    X_scale = X_scale * (1-deviation)

                for deviation in params_deviations['Y']['scale']:
                    Y_scale = Y_scale * (1-deviation)
    
                x_swaps_simulator.frequency_generator.mean_occurencies = params['X']['freq'] + params_deviations['X']['freq']
                x_swaps_simulator.token_in_generator.shape = params['X']['shape'] + params_deviations['X']['shape']
                x_swaps_simulator.token_in_generator.scale = X_scale

                y_swaps_simulator.frequency_generator.mean_occurencies = params['Y']['freq'] + params_deviations['Y']['freq']
                y_swaps_simulator.token_in_generator.shape = params['Y']['shape'] + params_deviations['Y']['shape']
                y_swaps_simulator.token_in_generator.scale = Y_scale
                
                x_swaps_simulator.generate_transactions(current_iteration_timestamp)
                y_swaps_simulator.generate_transactions(current_iteration_timestamp)

                current_iteration_timestamp += timedelta(milliseconds=cycle_size)

                x_swaps_df = x_swaps_simulator.get_dataframe()
                y_swaps_df = y_swaps_simulator.get_dataframe()

                x_swaps_simulator.clear_transaction_history()
                y_swaps_simulator.clear_transaction_history()

                cycle_swaps = pd.concat([x_swaps_df, y_swaps_df], ignore_index=True,) # todo:check axis
                cycle_swaps.sort_values('datetime_timestamp', inplace=True)
                cycle_swaps.index = np.arange(len(all_swaps), len(all_swaps) + len(cycle_swaps))
                cycle_swaps['token_in_amount'] = cycle_swaps['token_in_amount'].apply(expand_to_18_decimals)
                all_swaps = pd.concat([all_swaps, cycle_swaps])

               # print('cycle swaps:', len(cycle_swaps), 'number cycles:',   )
                #print(cycle_swaps.datetime_timestamp.min(), cycle_swaps.datetime_timestamp.max())

                #print(current_iteration_timestamp)


                for index, swap in cycle_swaps.iterrows():
                    yield swap

        elif action[0] == 'INC' or action[1] == 'DEC':
            token, param, value = action[1], action[2], action[3]

            if param == 'scale':
                params_deviations[token][param].append(value)
            else:
                params_deviations[token][param] += value
        elif action[0] == 'NORMALIZE':
            token, param = action[1], action[2]

            if param == 'scale':
                params_deviations[token][param] = []
            else:
                params_deviations[token][param] = 0

    all_swaps['token_in_amount'] = all_swaps['token_in_amount'].apply(contract_18_decimals_to_float)
    all_swaps.to_csv(transaction_history_path)


def parse_dynamic_config(filename):
    initial_params = {
        'X': {
            'freq': None
        },
        'Y': {
            'freq': None
        }
    }

    actions = []

    with open(filename, 'r') as f:
        lines = f.readlines()

        tokens0 = lines[0].split()
        tokens1 = lines[1].split()

        assert tokens0[0] == 'ASSIGN'
        assert tokens0[1] == 'X'
        assert tokens0[2] == 'freq'

        assert tokens1[0] == 'ASSIGN'
        assert tokens1[1] == 'Y'
        assert tokens1[2] == 'freq'

        hourly_freq_X = tokens0[3]
        hourly_freq_Y = tokens1[3]

        initial_params['X']['freq'] = float(hourly_freq_X) / 60 
        initial_params['Y']['freq'] = float(hourly_freq_Y) / 60

        for line in lines[2:]:
            tokens = line.split()

            command = tokens[0]

            if command == 'PASS':
                interval, unit = re.findall(r'[A-Za-z]+|\d+', tokens[1])
                interval = float(interval)

                assert unit == 'h'

                actions.append((command, int(interval*60))) # convert to minutes

            elif command == 'INC' or command == 'DEC':
                token = tokens[1]
                param = tokens[2]
                value = float(tokens[3]) / 60 # convert to min frequency

                actions.append((command, token, param, value))
            elif command == 'NORMALIZE':
                token, param = tokens[1], tokens[2]

                actions.append((command, token, param))

    print("Initial params:\n", initial_params)
    print("Actions:\n", actions)

    return initial_params, actions



if __name__ == '__main__':
    main()