import pandas as pd
from big_numbers import contract_18_decimals_to_float, expand_to_18_decimals
from safe_math import q_decode_144
import json

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


def get_reserve_range_index(stablecoin_reserve):
 #   print('get_Reserve_index', stablecoin_reserve)
    assert stablecoin_reserve >= 0, 'Invalid reserve value'

    if stablecoin_reserve <= 1000:
        return 0
    
    if stablecoin_reserve <= 10000:
        return 1

    if stablecoin_reserve <= 50000:
        return 2

    if stablecoin_reserve <= 100000:
        return 3

    if stablecoin_reserve <= 200000:
        return 4

    if stablecoin_reserve <= 500000:
        return 5

    if stablecoin_reserve <= 1000000:
        return 6

    if stablecoin_reserve <= 10000000:
        return 7

    if stablecoin_reserve <= 1000000000:
        return 8

    raise Exception("Invalid reserve value")

def save_dict(path, dict):
    with open(path, 'w') as f:
        json.dump(dict, f)