import pandas as pd
from tqdm import tqdm
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

PERPETUAL_GRAPH_ADDRESS = 'https://api.thegraph.com/subgraphs/name/perpetual-protocol/perp-position-subgraph'

#   ----------------------------------- POSITION RELATED DATA -------------------------------------------------
def get_positions(range_limit: int=20000) -> list:
    transport = RequestsHTTPTransport(url = PERPETUAL_GRAPH_ADDRESS,
                                            verify=True, retries=3)
    client = Client(transport=transport)
    data = []
    last_date = 0
    
    for skip in tqdm(range(0, range_limit)):
        try:
            query = gql(
                'query{\n'
                    'positions(first: 1000, orderBy: timestamp, orderDirection: asc,\n'
                        'where: {\n'
                            f'timestamp_gt: {last_date}\n'
                        '}\n'
                    ') {\n'
                        'id\n'
                        'trader\nmargin\nopenNotional\n'
                        'tradingVolume\nleverage\n'
                        'realizedPnl\nunrealizedPnl\nfundingPayment\n'
                        'fee\nbadDebt\nliquidationPenalty\n'
                        'totalPnlAmount\nblockNumber\ntimestamp\n'
                        'ammPositions {\n'
                            'amm\nmargin\nopenNotional\n'
                            'tradingVolume\nleverage\nentryPrice\n'
                            'realizedPnl\nunrealizedPnl\nfundingPayment\n'
                            'fee\nbadDebt\nliquidationPenalty\n'
                            'totalPnlAmount\nblockNumber\ntimestamp\n'
                        '}\n'
                    '}\n'
                '}\n'
            )
            
            response = client.execute(query)
            last_date = response['positions'][-1]['timestamp']
            data.extend(response['positions'])
        
        except Exception as e:
            print(e)
            return data
        
    return data


def position_list_to_dict(position_list: list) -> pd.DataFrame:
    id = position_list['id']
    trader = position_list['trader']
    margin = position_list['margin']
    open_notional = position_list['openNotional']
    trading_volume = position_list['tradingVolume']
    leverage = position_list['leverage']
    realized_pnl = position_list['realizedPnl']
    unrealized_pnl = position_list['unrealizedPnl']
    funding_payment = position_list['fundingPayment']
    fee = position_list['fee']
    bad_debt = position_list['badDebt']
    liquidation_penalty = position_list['liquidationPenalty']
    total_pnl_amount = position_list['totalPnlAmount']
    block_number = position_list['blockNumber']
    timestamp = position_list['timestamp']
    
    return {
        'id': id, 'trader': trader, 'margin': margin, 'open_notional': open_notional,
        'trading_volume': trading_volume, 'leverage': leverage, 'realized_pnl': realized_pnl,
        'unrealized_pnl': unrealized_pnl, 'funding_payment': funding_payment, 'fee': fee,
        'bad_debt': bad_debt, 'liquidation_penalty': liquidation_penalty, 
        'total_pnl_amount': total_pnl_amount, 'block_number': block_number, 'timestamp': timestamp
    }
    
    
def positions_to_df(positions_history: list) -> pd.DataFrame:
    positions_history_transformed = [position_list_to_dict(position) for position in positions_history]
    positions_df = pd.DataFrame(positions_history_transformed)
    positions_df['timestamp'] = pd.to_datetime(positions_df['timestamp'], unit='s')
    return positions_df

    
def extract_amm_positions_to_df(positions_list_of_lists: list) -> pd.DataFrame:
    amm_positions_dicts = []
    for position_list in positions_list_of_lists:
        id = position_list['id']
        amm_positions = position_list['ammPositions']
        
        for amm_position in amm_positions:
            amm_amm = amm_position['amm']
            amm_margin = amm_position['margin']
            amm_open_notional = amm_position['openNotional']
            amm_trading_volume = amm_position['tradingVolume']
            amm_leverage = amm_position['leverage']
            amm_entry_price = amm_position['entryPrice']
            amm_realized_pnl = amm_position['realizedPnl']
            amm_unrealized_pnl = amm_position['unrealizedPnl']
            amm_funding_payment = amm_position['fundingPayment']
            amm_fee = amm_position['fee']
            amm_bad_debt = amm_position['badDebt']
            amm_liquidation_penalty = amm_position['liquidationPenalty']
            amm_total_pnl_amount = amm_position['totalPnlAmount']
            amm_block_number = amm_position['blockNumber']
            amm_timestamp = amm_position['timestamp']
            
            amm_position_record = {
                'id': id, 'amm': amm_amm, 'margin': amm_margin, 'open_notional': amm_open_notional,
                'trading_volume': amm_trading_volume, 'leverage': amm_leverage, 'entry_price': amm_entry_price,
                'realized_pnl': amm_realized_pnl, 'unrealized_pnl': amm_unrealized_pnl, 'funding_payment': amm_funding_payment,
                'fee': amm_fee, 'bad_debt': amm_bad_debt, 'liquidation_penalty': amm_liquidation_penalty,
                'total_pnl_amount': amm_total_pnl_amount, 'block_number': amm_block_number, 'timestamp': amm_timestamp
            }
            amm_positions_dicts.append(amm_position_record)
                 
    amm_positions_df = pd.DataFrame(amm_positions_dicts)
    amm_positions_df['timestamp'] = pd.to_datetime(amm_positions_df['timestamp'], unit='s')
    
    return amm_positions_df


#   ----------------------------------- POSITION CHANGES RELATED DATA -------------------------------------------------
def get_position_changed_events(range_limit: int=20000):
    transport = RequestsHTTPTransport(url = PERPETUAL_GRAPH_ADDRESS,
                                            verify=True, retries=3)
    client = Client(transport=transport)
    data = []
    last_date = 0
    
    for skip in tqdm(range(0, range_limit)):
        try:
            query = gql(
                'query{\n'
                    'positionChangedEvents(first: 1000, orderBy: timestamp, orderDirection: asc,\n'
                        'where: {\n'
                            f'timestamp_gt: {last_date}\n'
                        '}\n'
                    ') {\n'
                        'id\n'
                        'trader\namm\nmargin\npositionNotional\n'
                        'exchangedPositionSize\nfee\npositionSizeAfter\n'
                        'realizedPnl\nunrealizedPnlAfter\nbadDebt\n'
                        'liquidationPenalty\nspotPrice\nfundingPayment\n'
                        'blockNumber\ntimestamp\n'
                    '}\n'
                '}\n'
            )
            
            response = client.execute(query)
            last_date = response['positionChangedEvents'][-1]['timestamp']
            data.extend(response['positionChangedEvents'])

        except Exception as e:
            print(e)
            return data
            
    return data


def position_changed_event_list_to_dict(position_changed_events_list: list) -> dict:
    """transform one reserve update data array into dictionary

    Args:
        daily_reserve (list): one reserve update record in array format

    Returns:
        dict: dictionary of one reserve update record
    """
    # reserve information, daily volume info, date of taken info, token names and volume with reserves
    id = position_changed_events_list['id']
    trader = position_changed_events_list['trader']
    amm = position_changed_events_list['amm']
    margin = position_changed_events_list['margin']
    position_notional = position_changed_events_list['positionNotional']
    exchanged_position_size = position_changed_events_list['exchangedPositionSize']
    fee = position_changed_events_list['fee']
    position_size_after = position_changed_events_list['positionSizeAfter']
    realized_pnl = position_changed_events_list['realizedPnl']
    unrealized_pnl_after = position_changed_events_list['unrealizedPnlAfter']
    bad_debt = position_changed_events_list['badDebt']
    liquidation_penalty = position_changed_events_list['liquidationPenalty']
    spot_price = position_changed_events_list['spotPrice']
    funding_payment = position_changed_events_list['fundingPayment']
    block_number = position_changed_events_list['blockNumber']
    timestamp = position_changed_events_list['timestamp']
    
    return {
        'id': id, 'trader': trader, 'amm': amm, 'margin': margin,
        'position_notional': position_notional, 
        'exchanged_position_size': exchanged_position_size,
        'fee': fee, 'position_size_after': position_size_after,
        'realized_pnl': realized_pnl, 
        'unrealized_pnl_after': unrealized_pnl_after,
        'bad_debt': bad_debt, 'liquidation_penalty': liquidation_penalty,
        'spot_price': spot_price, 'funding_payment': funding_payment,
        'block_number': block_number, 'timestamp': timestamp
    }


def position_changed_events_to_df(position_changes_history: list) -> pd.DataFrame:
    """transform array of arrays representing transaction history into pandas dataframe

    Args:
        pool_history (list): array of arrays representing transaction history

    Returns:
        pd.DataFrame: pandas dataframe of transaction history
    """
    # transform transactions list of lists into list of dictionaries
    position_changed_events_transformed = [position_changed_event_list_to_dict(position_changed_event) for position_changed_event in position_changes_history]

    # make a dataframe from list of dictionaries and fix data type for specific columns
    position_changes_df = pd.DataFrame(position_changed_events_transformed)
    position_changes_df.timestamp = pd.to_datetime(position_changes_df.timestamp, unit='s')

    return position_changes_df


#   ------------------------------  LIQUIDATIONS RELATED DATA   ------------------------------------------------
def get_position_liquidated_events(range_limit: int=20000):
    transport = RequestsHTTPTransport(url = PERPETUAL_GRAPH_ADDRESS,
                                            verify=True, retries=3)
    client = Client(transport=transport)
    data = []
    last_date = 0
    
    for skip in tqdm(range(0, range_limit)):
        try:
            query = gql(
                'query{\n'
                    'positionLiquidatedEvents(first: 1000, orderBy: timestamp, orderDirection: asc,\n'
                        'where: {\n'
                            f'timestamp_gt: {last_date}\n'
                        '}\n'
                    ') {\n'
                        'id\n'
                        'trader\namm\npositionNotional\n'
                        'positionSize\nliquidationFee\n'
                        'liquidator\nbadDebt\nblockNumber\ntimestamp\n'
                    '}\n'
                '}\n'
            )
            
            response = client.execute(query)
            last_date = response['positionLiquidatedEvents'][-1]['timestamp']
            data.extend(response['positionLiquidatedEvents'])

        except Exception as e:
            print(e)
            return data
            
    return data


def liquidation_event_list_to_dict(liquidation_event_list: list) -> dict:
    id = liquidation_event_list['id']
    trader = liquidation_event_list['trader']
    amm = liquidation_event_list['amm']
    position_notional = liquidation_event_list['positionNotional']
    position_size = liquidation_event_list['positionSize']
    liquidation_fee = liquidation_event_list['liquidationFee']
    liquidator = liquidation_event_list['liquidator']
    badDebt = liquidation_event_list['badDebt']
    block_number = liquidation_event_list['blockNumber']
    timestamp = liquidation_event_list['timestamp']
    
    return{
        'id': id, 'trader': trader, 'amm': amm, 'position_notional': position_notional,
        'position_size': position_size, 'liquidation_fee': liquidation_fee,
        'liquidator': liquidator, 'badDebt': badDebt, 'block_number': block_number,
        'timestamp': timestamp
    }
    

def liquidation_events_to_df(liquidation_events_history) -> pd.DataFrame:
    # transform transactions list of lists into list of dictionaries
    liquidation_events_transformed = [liquidation_event_list_to_dict(liquidation_event) for liquidation_event in liquidation_events_history]

    # make a dataframe from list of dictionaries and fix data type for specific columns
    liquidations_df = pd.DataFrame(liquidation_events_transformed)
    liquidations_df.timestamp = pd.to_datetime(liquidations_df.timestamp, unit='s')

    return liquidations_df
    

#   ------------------------------- TRADERS RELATED DATA    ------------------------------------------------



#   ------------------------------------    AMM RELATED DATA    -------------------------------------------

def get_amms():
    """returns all active AMMs on the Perpetual network

    Returns:
        list: list of AMM data with each record present as dict
    """
    transport = RequestsHTTPTransport(url = PERPETUAL_GRAPH_ADDRESS,
                                            verify=True, retries=3)
    client = Client(transport=transport)
    data = []
    
    try:
        query = gql(
            'query{\n'
                'amms{\n'
                    'id\npositionBalance\n'
                    'openInterestSize\nopenInterestNotional\n'
                    'quoteAssetReserve\nbaseAssetReserve\n'
                    'tradingVolume\nblockNumber\ntimestamp'
                '}\n'
            '}\n'
        )
        
        response = client.execute(query)
        data.extend(response['amms'])
        
    except Exception as e:
        print(e)
        return data
    
    return data


def amm_list_to_dict(amms_list: list) -> dict:
    """transform one reserve update data array into dictionary

    Args:
        daily_reserve (list): one reserve update record in array format

    Returns:
        dict: dictionary of one reserve update record
    """
    # reserve information, daily volume info, date of taken info, token names and volume with reserves
    id = amms_list['id']
    position_balance = amms_list['positionBalance']
    open_interest_size = amms_list['openInterestSize']
    open_interest_notional = amms_list['openInterestNotional']
    trading_volume = amms_list['tradingVolume']
    quote_asset_reserve = amms_list['quoteAssetReserve']
    base_asset_reserve = amms_list['baseAssetReserve']
    block_number = amms_list['blockNumber']
    timestamp = amms_list['timestamp']
    
    return {
        'id': id,
        'position_balance': position_balance, 
        'open_interest_size': open_interest_size,
        'open_interest_notional': open_interest_notional,
        'trading_volume': trading_volume,
        'quote_asset_reserve': quote_asset_reserve, 
        'base_asset_reserve': base_asset_reserve,
        'block_number': block_number, 'timestamp': timestamp
    }
    

def amms_to_df(amms_history: list) -> pd.DataFrame:
    amms_transformed = [amm_list_to_dict(amm) for amm in amms_history]
    amms_df = pd.DataFrame(amms_transformed)
    return amms_df