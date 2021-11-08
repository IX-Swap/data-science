import pandas as pd
import plotly.express as px
import seaborn as sns
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
import sys
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport


def get_pool_v2_reserves_history(contract_id: str) -> list:
    sample_transport = RequestsHTTPTransport(url = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2',
                                            verify=True, retries=3)
    
    client = Client(transport=sample_transport)
    
    daily_data = []
    last_date = 0

    for skip in tqdm(range(0, 2)):
        try:
            contract_id = contract_id
            query = gql(
                'query{\n'
                 'pairDayDatas(first: 1000, orderBy: date, orderDirection: asc,\n'
                   'where: {\n'
                     f'pairAddress: "{contract_id}",\n'
                     f'date_gt: {last_date}\n'
                   '}\n'
                 ') {\n'
                     'date\n'
                     'dailyVolumeToken0\n'
                     'dailyVolumeToken1\n'
                     'dailyVolumeUSD\n'
                     'reserveUSD\n'
                     'reserve0\n'
                     'reserve1\n'
                 '}\n'
                '}\n'
            )

            response = client.execute(query)
            last_date = response['pairDayDatas'][-1]['date']
            daily_data.extend(response['pairDayDatas'])

        except Exception as e:
            print(e)
            
    return daily_data


def list_to_reserves_dictionary(daily_reserve: list) -> dict:
    """
    transform daily reserve information list into daily reserve information dictionary
    """
    # reserve information
    reserve0 = daily_reserve['reserve0']
    reserve1 = daily_reserve['reserve1']
    reserveUSD = daily_reserve['reserveUSD']
    
    # daily volume info
    dailyVolumeToken0 = daily_reserve['dailyVolumeToken0']
    dailyVolumeToken1 = daily_reserve['dailyVolumeToken1']
    
    # date of reserve info taken
    date = daily_reserve['date']
    
    return {
        'reserve0': reserve0,
        'reserve1': reserve1,
        'reserveUSD': reserveUSD,
        'dailyVolumeToken0': dailyVolumeToken0,
        'dailyVolumeToken1': dailyVolumeToken1,
        'date': date
    }


def get_pool_v2_history(contract_id: str, range_limit: int=100) -> list:
    """
    function performs api call to the Uniswap v2 and gets history of required contract
    considering timestamps
    """
    sample_transport = RequestsHTTPTransport(url = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2',
                                            verify=True, retries=3)

    all_swaps = []
    last_timestamp = 0

    client = Client(transport=sample_transport)

    for skip in tqdm(range(0, range_limit)):
        try:
            query = gql(
            'query {\n'
                f'swaps(first: 1000, where: {{ pair: "{contract_id}", timestamp_gt: {last_timestamp} }} orderBy: timestamp, orderDirection: asc) {{\n'
                'transaction {\n'
                    'id\n'
                    'timestamp\n'
                '}\n'
                'id\n'
                'pair {\n'
                    'token0 {\n'
                    'id\n'
                    'symbol\n'
                    '}\n'
                    'token1 {\n'
                    'id\n'
                    'symbol\n'
                    '}\n'
                '}\n'
                'amount0In\n'
                'amount0Out\n'
                'amount1In\n'
                'amount1Out\n'
                'amountUSD\n'
                'to\n'
                '}\n'
            '}\n')

            # get current response and extract from it last timestamp
            response = client.execute(query)
            last_timestamp = response['swaps'][-1]['transaction']['timestamp']

            # extend swaps history with current response
            all_swaps.extend(response['swaps'])

        except Exception as e:
            print(e)

    return all_swaps


def list_to_transaction_dictionary(transaction: list) -> dict:
    """
    transform list of transaction info into dictionary of transaction info
    """
    if transaction['amount0In'] != '0':
        token_in = transaction['pair']['token0']['symbol']
        token_out = transaction['pair']['token1']['symbol']
        amount_in = transaction['amount0In']
        amount_out = transaction['amount1Out']
    else:
        token_in = transaction['pair']['token1']['symbol']
        token_out = transaction['pair']['token0']['symbol']
        amount_in = transaction['amount1In']
        amount_out = transaction['amount0Out']
        
    amount_usd = transaction['amountUSD']
    timestamp = transaction['transaction']['timestamp']
    
    return {
        'token_in': token_in,
        'token_out': token_out,
        'amount_in': amount_in,
        'amount_out': amount_out,
        'amount_usd': amount_usd,
        'timestamp': timestamp
    }


def pool_history_to_df(pool_history: list) -> pd.DataFrame:
    """
    transform list-like pool history into pandas dataframe
    """
    # transform transactions list of lists into list of dictionaries
    all_swaps_transformed = [list_to_transaction_dictionary(swap) for swap in pool_history]

    # make a dataframe from list of dictionaries and fix data type for specific columns
    swaps_df = pd.DataFrame(all_swaps_transformed)
    swaps_df.timestamp = pd.to_datetime(swaps_df.timestamp, unit='s')
    swaps_df['amount_in'] = swaps_df['amount_in'].astype('float')
    swaps_df['amount_out'] = swaps_df['amount_out'].astype('float')
    swaps_df['amount_usd'] = swaps_df['amount_usd'].astype('float')

    return swaps_df


def pool_reserves_to_df(reserves_list: list) -> pd.DataFrame:
    """
    transform list-like reserves history into pandas dataframe
    """
    
    # transform list of dictionaries into df
    daily_data_df = pd.DataFrame([list_to_reserves_dictionary(x) for x in reserves_list])
    
    daily_data_df['reserve0'] = daily_data_df['reserve0'].astype('float')
    daily_data_df['reserve1'] = daily_data_df['reserve1'].astype('float')
    daily_data_df['reserveUSD'] = daily_data_df['reserveUSD'].astype('float')
    daily_data_df['dailyVolumeToken0'] = daily_data_df['dailyVolumeToken0'].astype('float')
    daily_data_df['dailyVolumeToken1'] = daily_data_df['dailyVolumeToken1'].astype('float')
    daily_data_df['date'] =  pd.to_datetime(daily_data_df['date'], unit='s')
    
    return daily_data_df