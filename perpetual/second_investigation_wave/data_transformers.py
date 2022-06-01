import sys
sys.path.insert(0, "C:/workspace/data-science/libs")
from big_numbers import expand_to_18_decimals, expand_to_18_decimals_object, contract_18_decimals_to_float
import pandas as pd
import numpy as np

import pandas as pd
from tqdm import tqdm
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

def transform_18_decimals_to_float(df: pd.DataFrame, columns_to_transform: list):
    """transform chosen columns of the dataframe from 18 decimals format to floating
    point numbers

    Args:
        df (pd.DataFrame): dataframe for which data change is required
        columns_to_transform (list): columns that will be changed
    """
    for column in columns_to_transform:
        df[column] = df[column].apply(lambda x: contract_18_decimals_to_float(x))
    
    return df


def transform_amm_address_to_name(df: pd.DataFrame, column_with_address: str="amm"):
    """add a column that will transform amm address to the name of respective pool
    in the perpetual protocol system

    Args:
        df (pd.DataFrame): dataframe to which pool name replacement is required
        column_with_address (str, optional): name of column containing addresses
                                            if the pools. Defaults to "amm".
    """
    replacement_map = {'0x0f346e19f01471c02485df1758cfd3d624e399b4': 'BTC/USDC',
                      '0x8d22f1a9dce724d8c1b4c688d75f17a2fe2d32df': 'ETH/USDC',
                      '0xd41025350582674144102b74b8248550580bb869': 'YFI/USDC',
                      '0x6de775aabeeede8efdb1a257198d56a3ac18c2fd': 'DOT/USDC',
                      '0xb397389b61cbf3920d297b4ea1847996eb2ac8e8': 'SNX/USDC',
                      '0x80daf8abd5a6ba182033b6464e3e39a0155dcc10': 'LINK/USDC',
                      '0x16a7ecf2c27cb367df36d39e389e66b42000e0df': 'AAVE/USDC',
                      '0xf559668108ff57745d5e3077b0a7dd92ffc6300c': 'SUSHI/USDC',
                      '0x33fbaefb2dcc3b7e0b80afbb4377c2eb64af0a3a': 'COMP/USDC',
                      '0x922f28072babe6ea0c0c25ccd367fda0748a5ec7': 'REN/USDC',
                      '0xfcae57db10356fcf76b6476b21ac14c504a45128': 'PERP/USDC',
                      '0xeac6cee594edd353351babc145c624849bb70b11': 'UNI/USDC',
                      '0xab08ff2c726f2f333802630ee19f4146385cc343': 'CRV/USDC',
                      '0xb48f7accc03a3c64114170291f352b37eea26c0b': 'MKR/USDC',
                      '0x7b479a0a816ca33f8eb5a3312d1705a34d2d4c82': 'CREAM/USDC',
                      '0x187c938543f2bde09fe39034fe3ff797a3d35ca0': 'GRT/USDC',
                      '0x26789518695b56e16f14008c35dc1b281bd5fc0e': 'ALPHA/USDC',
                      '0xf9e30f08a738620bc2331f728de4dac7937888d3': 'unknown',
                      '0x838b322610bd99a449091d3bf3fba60d794909a9': 'FTT/USDC'}
    
    df['amm_name'] = df[column_with_address]
    df['amm_name'].replace(replacement_map, inplace=True)


# inner lambda function, do not use
def __tx_version_separate__(record):
    splitted_id = record['id'].split('-')
    if len(splitted_id) > 1:
        record['id'] = splitted_id[0]
        record['tx_change_version'] = splitted_id[1]
    
    return record


def transform_id_to_hash_and_change(df: pd.DataFrame):
    """separate transaction id in two parts: one with hash address of the transaction
    and another one representing ID of the change applied by the user to his/her
    current opened position

    Args:
        df (pd.DataFrame): dataframe where separation is required
    """
    df['tx_change_version'] = np.zeros(len(df))
    df = df.apply(lambda record: __tx_version_separate__(record), axis=1)
    return df
    
    
def __list_to_reserves_dictionary__(daily_reserve: list) -> dict:
    """transform one reserve update data array into dictionary
    Args:
        daily_reserve (list): one reserve update record in array format
    Returns:
        dict: dictionary of one reserve update record
    """
    # reserve information, daily volume info, date of reserve info taken
    reserve0 = daily_reserve['reserve0']
    reserve1 = daily_reserve['reserve1']
    reserveUSD = daily_reserve['reserveUSD']
    dailyVolumeToken0 = daily_reserve['dailyVolumeToken0']
    dailyVolumeToken1 = daily_reserve['dailyVolumeToken1']
    date = daily_reserve['date']
    
    return {
        'reserve0': reserve0, 'reserve1': reserve1,
        'reserveUSD': reserveUSD,
        'dailyVolumeToken0': dailyVolumeToken0,
        'dailyVolumeToken1': dailyVolumeToken1,
        'date': date
    }


def collect_uniswap_price_daily_df(contract_id: str):
    """function for collecting daily reserves data and then make a price dataframe

    Args:
        contract_id (str): hash address of the pool on Uniswap with respective token
    """
    
    """get information about reserves updates conform given contract ID from Uniswap V2
    Args:
        contract_id (str): hash-sum of contract reserves updates history of which it is required to get
    Returns:
        list: array of reserves updates, where each record is inner array
    """
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
                     'dailyVolumeToken0\ndailyVolumeToken1\n'
                     'dailyVolumeUSD\n'
                     'reserveUSD\nreserve0\nreserve1\n'
                 '}\n'
                '}\n'
            )
            response = client.execute(query)
            last_date = response['pairDayDatas'][-1]['date']
            daily_data.extend(response['pairDayDatas'])

        except Exception as e:
            print(e)
            
    daily_data_df = pd.DataFrame([__list_to_reserves_dictionary__(x) for x in daily_data])
    
    daily_data_df['reserve0'] = daily_data_df['reserve0'].astype('float')
    daily_data_df['reserve1'] = daily_data_df['reserve1'].astype('float')
    daily_data_df['reserveUSD'] = daily_data_df['reserveUSD'].astype('float')
    daily_data_df['dailyVolumeToken0'] = daily_data_df['dailyVolumeToken0'].astype('float')
    daily_data_df['dailyVolumeToken1'] = daily_data_df['dailyVolumeToken1'].astype('float')
    daily_data_df['date'] =  pd.to_datetime(daily_data_df['date'], unit='s')
    
    return daily_data_df
    