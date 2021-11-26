import logging
from random import randrange
import itertools
import pandas as pd
import amm
import os
import numpy as np
import blockchain
from big_numbers import contract_18_decimals_to_float, expand_to_18_decimals, expand_to_18_decimals_object
from safe_math import q_decode_144
import settings
from transactions import BurnTransaction, MintTransaction, SwapTransaction
from monte_carlo2 import Transaction 
from tqdm import tqdm

# RUNS SIMULATION FOR POOL WITH AND WITHOUT VOLATILITY MITIGATOR


logging.basicConfig(level=logging.WARN, format='%(asctime)s:%(name)s:%(message)s', datefmt="%m/%d/%Y %I:%M:%S %p")
logger = logging.getLogger(__name__)

EXPERIMENT_ID = 50
X_NAME = 'WBTC'
Y_NAME = 'DAI'
X_INDEX = '0'
Y_INDEX = '1'

def main(): 
    swaps_path = f'data/pair_history/{X_NAME}_{Y_NAME}/{X_NAME.lower()}_{Y_NAME.lower()}_swaps.pkl'
    mints_path = f'data/pair_history/{X_NAME}_{Y_NAME}/{X_NAME.lower()}_{Y_NAME.lower()}_mints.pkl'
    burns_path = f'data/pair_history/{X_NAME}_{Y_NAME}/{X_NAME.lower()}_{Y_NAME.lower()}_burns.pkl'

    swaps_df = pd.read_pickle(swaps_path)
    mints_df = pd.read_pickle(mints_path)
    burns_df = pd.read_pickle(burns_path)

    swaps_df['type'] = 'SWAP'
    mints_df['type'] = 'MINT'
    burns_df['type'] = 'BURN'

    burns_df = burns_df[~burns_df.isnull().any(axis=1)] # todo: print number of missing

    swaps_df, mints_df, burns_df = expand_all_transactions_history(swaps_df, mints_df, burns_df)
    transactions_df = pd.concat([swaps_df, mints_df, burns_df])

    transactions_df.sort_values('timestamp', inplace=True)

    base_experiment_path = f'data/real_transactions/experiment_{EXPERIMENT_ID}'
    os.makedirs(base_experiment_path)
    
    with open(f'{base_experiment_path}/config.txt', 'w') as f:
        f.write(base_experiment_path)

    iteration = 0
    window_size = 24
    granularity = 24

    

    for vm in [False, True]:
        os.makedirs(f'{base_experiment_path}/{iteration}')

        amm.reset(X_NAME, Y_NAME, int(0), int(0), vm, window_size * 60 * 60, window_size * 60 * 60// granularity, granularity) #todo: beautify

        cnt = 0 
        
        for index, row in tqdm(transactions_df.iterrows()):
            blockchain.update(row['timestamp'].second)

            if row['type'] == 'SWAP':
                amm.swap(cnt, Transaction(row['timestamp'], int(row['amount_in']), row['token_in'], row['token_out'], 100, row['txd']))
            elif row['type'] == 'MINT':
                amm.mint(int(row[f'amount{X_INDEX}']), int(row[f'amount{Y_INDEX}']), row['timestamp'], cnt)
            elif row['type'] == 'BURN':
                amm.burn(int(row[f'amount{X_INDEX}']), int(row[f'amount{Y_INDEX}']), row['timestamp'], cnt)

            cnt += 1


        SwapTransaction.save_all(f'{base_experiment_path}/{iteration}/swaps.csv')
        MintTransaction.save_all(f'{base_experiment_path}/{iteration}/mints.csv')
        BurnTransaction.save_all(f'{base_experiment_path}/{iteration}/burns.csv')
        blockchain.reset_state()
        
        amm.export_pool_states_to_csv(f'{base_experiment_path}/{iteration}/pool_before_transaction.csv', 
                                        f'{base_experiment_path}/{iteration}/pool_after_transaction.csv')

        logger.info("Start normalizing...")
        normalize_csv(f'{base_experiment_path}/{iteration}/swaps.csv', ['token_in_amount', 'token_out_amount', 'token_out_amount_min', 'system_fee', 'oracle_amount_out'], f'{base_experiment_path}/{iteration}/swaps_normalized.csv')
        normalize_csv(f'{base_experiment_path}/{iteration}/mints.csv', ['X_amount', 'Y_amount'], f'{base_experiment_path}/{iteration}/mints_normalized.csv')
        normalize_csv(f'{base_experiment_path}/{iteration}/burns.csv', ['X_amount', 'Y_amount'], f'{base_experiment_path}/{iteration}/burns_normalized.csv')

        normalize_pool_state(f'{base_experiment_path}/{iteration}/pool_before_transaction.csv', f'{base_experiment_path}/{iteration}/pool_before_transaction_normalized.csv')
        normalize_pool_state(f'{base_experiment_path}/{iteration}/pool_after_transaction.csv', f'{base_experiment_path}/{iteration}/pool_after_transaction_normalized.csv')
        logging.info("Finished normalizing")

        iteration += 1


def expand_all_transactions_history(swaps_df, mints_df, burns_df):
    swaps_df['amount_in'] = swaps_df['amount_in'].apply(expand_to_18_decimals_object)
    swaps_df['amount_out'] = swaps_df['amount_out'].apply(expand_to_18_decimals_object)

    mints_df[f'amount{X_INDEX}'] = mints_df[f'amount{X_INDEX}'].apply(expand_to_18_decimals_object)
    mints_df[f'amount{Y_INDEX}'] = mints_df[f'amount{Y_INDEX}'].apply(expand_to_18_decimals_object)

    burns_df[f'amount{X_INDEX}'] = burns_df[f'amount{X_INDEX}'].apply(expand_to_18_decimals_object)
    burns_df[f'amount{Y_INDEX}'] = burns_df[f'amount{Y_INDEX}'].apply(expand_to_18_decimals_object)

    return swaps_df, mints_df, burns_df



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

    pool_state_df.to_csv(normalized_filename, index=False)


if __name__ == '__main__':
    main()