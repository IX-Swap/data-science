import pandas as pd
from tqdm import tqdm
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport


def get_pool_v2_reserves_history(contract_id: str) -> list:
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
        'reserve0': reserve0,
        'reserve1': reserve1,
        'reserveUSD': reserveUSD,
        'dailyVolumeToken0': dailyVolumeToken0,
        'dailyVolumeToken1': dailyVolumeToken1,
        'date': date
    }


def get_pool_v2_history(contract_id: str, range_limit: int=100) -> list:
    """get transaction history for given contract id
    Args:
        contract_id (str): hash-sum of required contract
        range_limit (int, optional): how many data fragments required (one fragment has 1000 records). Defaults to 100.
    Returns:
        list: list of transactions history, where each transaction is an inner array
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
                'sender\n'
                'to\n'
                '}\n'
            '}\n')

            # get current response, extract from it last timestamp, extend swaps history with
            # current response
            response = client.execute(query)
            last_timestamp = response['swaps'][-1]['transaction']['timestamp']
            all_swaps.extend(response['swaps'])

        except Exception as e:
            print(e)

    return all_swaps


def list_to_transaction_dictionary(transaction: list) -> dict:
    """transform transaction data present in array form into dictionary
    Args:
        transaction (list): one transaction data in array format
    Returns:
        dict: dictionary of one transaction record data
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
    sender = transaction['sender']
    to = transaction['to']
    timestamp = transaction['transaction']['timestamp']
    txd = transaction['transaction']['id']
    
    return {
        'token_in': token_in,
        'token_out': token_out,
        'amount_in': amount_in,
        'amount_out': amount_out,
        'amount_usd': amount_usd,
        'timestamp': timestamp,
        'sender': sender,
        'to': to,
        'txd': txd
    }
    

def get_pool_v2_mints(contract_id: str, range_limit: int) -> list:
    sample_transport = RequestsHTTPTransport(url = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2',
                                            verify=True, retries=3)

    client = Client(transport=sample_transport)
    all_mints = []
    last_timestamp = 0

    for skip in tqdm(range(0, range_limit)):
        try:
            query = gql(
                'query {\n'
                'mints(first: 1000, \n'
                'where: { '
                    f'pair: "{contract_id}", \n'
                    f'timestamp_gt: {last_timestamp}\n'
                '}, \n'
                'orderBy: timestamp, \n'
                'orderDirection: asc\n'
                ') {\n'
                'transaction {\n'
                    'id\n'
                    'timestamp\n'
                '}\n'
                'to\n'
                'liquidity\n'
                'amount0\n'
                'amount1\n'
                'amountUSD\n'
                '}\n'
                '}\n'
            )

            response = client.execute(query)
            last_timestamp = response['mints'][-1]['transaction']['timestamp']
            all_mints.extend(response['mints'])

        except Exception as e:
            print(e)
            
    return all_mints
            
            
def list_to_mints_dictionary(mint: list) -> dict:
    """transform mint record in form of array into dictionary

    Args:
        mint (list): mint record in form of array

    Returns:
        dict: dictionary representing mint record
    """
    amount0 = mint['amount0']
    amount1 = mint['amount1']
    amountUSD = mint['amountUSD']
    liquidity = mint['liquidity']
    timestamp = mint['transaction']['timestamp']
    
    return {
        'amount0': amount0,
        'amount1': amount1,
        'amountUSD': amountUSD,
        'liquidity': liquidity,
        'timestamp': timestamp,
    }


def get_pool_v2_burns(contract_id: str, range_limit: int) -> list:
    """get information about burns conform specified contract id

    Args:
        contract_id (str): contract id for which is required to find burns
        range_limit (int): how many fragments it is required to get (fragment contains 1000 records)

    Returns:
        list: array of arrays representing pool burns data
    """
    sample_transport = RequestsHTTPTransport(url = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2',
                                            verify=True, retries=3)

    client = Client(transport=sample_transport)
    all_burns = []
    last_timestamp = 0

    for skip in tqdm(range(0, range_limit)):
        try:
            query = gql(
                'query {\n'
                'burns(first: 1000, \n'
                'where: { '
                    f'pair: "{contract_id}", \n'
                    f'timestamp_gt: {last_timestamp}\n'
                '}, \n'
                'orderBy: timestamp, \n'
                'orderDirection: asc\n'
                ') {\n'
                'transaction {\n'
                    'id\n'
                    'timestamp\n'
                '}\n'
                'to\n'
                'liquidity\n'
                'amount0\n'
                'amount1\n'
                'amountUSD\n'
                '}\n'
                '}\n'
            )

            response = client.execute(query)
            last_timestamp = response['burns'][-1]['transaction']['timestamp']
            all_burns.extend(response['burns'])

        except Exception as e:
            print(e)
            
    return all_burns


def pool_history_to_df(pool_history: list) -> pd.DataFrame:
    """transform array of arrays representing transaction history into pandas dataframe

    Args:
        pool_history (list): array of arrays representing transaction history

    Returns:
        pd.DataFrame: pandas dataframe of transaction history
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
    """transform array of arrays representing reserves data into pandas dataframe

    Args:
        reserves_list (list): array of arrays representing reserve updates data

    Returns:
        pd.DataFrame: pandas dataframe of reserves updates
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


def pool_mints_to_df(mints_list: list) -> pd.DataFrame:
    """transform array of arrays representing mints into pandas dataframe

    Args:
        reserves_list (list): array of arrays representing mints

    Returns:
        pd.DataFrame: pandas dataframe of mints
    """
    # transform list of dictionaries into df
    all_mints_df = pd.DataFrame([list_to_mints_dictionary(mint) for mint in mints_list])
    
    all_mints_df['amount0'] = all_mints_df.amount0.astype('float')
    all_mints_df['amount1'] = all_mints_df.amount1.astype('float')
    all_mints_df['amountUSD'] = all_mints_df.amountUSD.astype('float')
    all_mints_df['liquidity'] = all_mints_df.liquidity.astype('float')
    all_mints_df['timestamp'] = pd.to_datetime(all_mints_df['timestamp'], unit='s')
    
    return all_mints_df


def pool_burns_to_df(burns_list: list) -> pd.DataFrame:
    """transform array of arrays representing burns into pandas dataframe

    Args:
        reserves_list (list): array of arrays representing burns

    Returns:
        pd.DataFrame: pandas dataframe of burns
    """
    # transform list of dictionaries into df
    # !!! IMPORTANT: for burns the same list to dictionary transformer can be used as for mints
    all_burns_df = pd.DataFrame([list_to_mints_dictionary(burn) for burn in burns_list])
    
    all_burns_df['amount0'] = all_burns_df.amount0.astype('float')
    all_burns_df['amount1'] = all_burns_df.amount1.astype('float')
    all_burns_df['amountUSD'] = all_burns_df.amountUSD.astype('float')
    all_burns_df['liquidity'] = all_burns_df.liquidity.astype('float')
    all_burns_df['timestamp'] = pd.to_datetime(all_burns_df['timestamp'], unit='s')
    
    return all_burns_df


def filter_swaps(all_swaps):
    """Filter swaps to exclude "flash" ones

    Args:
        all_swaps: swaps history

    Returns:
        pair of simple swaps and "flash" ones
    """
    direct_swaps = list(filter(lambda x: ((x['amount0In'] != '0') ^ (x['amount1In'] !='0')) & 
                               ((x['amount0Out'] != '0') ^ (x['amount1Out'] != '0')) & 
                               (not ((x['amount0In'] == '0') & (x['amount0Out'] == '0')))  &  
                               (not ((x['amount1In'] == '0') & (x['amount1Out'] == '0'))), all_swaps))
    other_swaps = list(filter(lambda x: not (((x['amount0In'] != '0') ^ (x['amount1In'] !='0')) & 
                                             ((x['amount0Out'] != '0') ^ (x['amount1Out'] != '0')) & 
                                             (not ((x['amount0In'] == '0') & (x['amount0Out'] == '0'))) & 
                                             (not ((x['amount1In'] == '0') & (x['amount1Out'] == '0')))), all_swaps))
    
    return direct_swaps, other_swaps