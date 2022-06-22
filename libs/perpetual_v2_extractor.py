from email.quoprimime import quote
from numpy import block
import pandas as pd
from tqdm import tqdm
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

PERPETUAL_V2_GRAPH_ADDRESS = 'https://api.thegraph.com/subgraphs/name/perpetual-protocol/perpetual-v2-optimism'


#   -------------------------------         markets section ----------------------------------------------------
def get_markets() -> list:
    """get list of markets (each record as list of attributes)

    Returns:
        list: list of lists with markets info
    """
    transport = RequestsHTTPTransport(url = PERPETUAL_V2_GRAPH_ADDRESS, verify=True, retries=3)
    client = Client(transport=transport)
    data = []
    
    for skip in tqdm(range(0, 1)):
        try:
            query = gql(
                "query{\n"
                    "markets(orderBy: blockNumberAdded, orderDirection: asc) {\n"
                        "baseToken\n"
                        "quoteToken\n"
                        "pool\n"
                        "feeRatio\n"
                        "tradingVolume\n"
                        "tradingFee\n"
                        "blockNumber\n"
                        "timestamp\n"
                        "blockNumberAdded\n"
                        "timestampAdded\n"
                    "}\n"
                "}\n"
            )
            response = client.execute(query)
            data.extend(response['markets'])
        except Exception as e:
            print(e)
            return data
    return data


def markets_list_to_dict(markets_list: list) -> dict:
    """transform market record from list to dictionary

    Args:
        markets_list (list): market record in list form

    Returns:
        dict: market record as dictionary
    """
    base_token = markets_list["baseToken"]
    quote_token = markets_list["quoteToken"]
    pool = markets_list["pool"]
    fee_ratio = markets_list["feeRatio"]
    trading_volume = markets_list["tradingVolume"]
    trading_fee = markets_list["tradingFee"]
    block_number = markets_list["blockNumber"]
    timestamp = markets_list["timestamp"]
    block_number_added = markets_list["blockNumberAdded"]
    timestamp_added = markets_list["timestampAdded"]
    
    return {
        "base_token": base_token, "quote_token": quote_token, "pool": pool,
        "fee_ratio": fee_ratio, "trading_volume": trading_volume, "trading_fee": trading_fee,
        "block_number": block_number, "timestamp": timestamp, "block_number_added": block_number_added,
        "timestamp_added": timestamp_added
    }


def markets_list_to_df(markets_list: list) -> pd.DataFrame:
    """transform markets list to dataframe

    Args:
        markets_list (list): list of markets

    Returns:
        pd.DataFrame: dataframe of markets
    """
    markets_transformed = [markets_list_to_dict(market) for market in markets_list]
    markets_df = pd.DataFrame(markets_transformed)
    markets_df["time"] = pd.to_datetime(markets_df["timestamp"], unit='s')
    return markets_df
#   ============================================================================================================


#   -----------------------------------     position closes section     ---------------------------------------
def get_position_closes(range_limit: int=20000) -> list:
    """get funding payments as list of lists

    Args:
        range_limit (int): how many calls to make. Defaults to 20000

    Returns:
        list: list of funding payments as lists
    """
    transport = RequestsHTTPTransport(url = PERPETUAL_V2_GRAPH_ADDRESS, verify=True, retries=3)
    client = Client(transport=transport)
    data = []
    last_date = 0
    
    for skip in tqdm(range(0, range_limit)):
        try:
            query = gql(
                'query{\n'
                    'positionCloseds(first: 1000, orderBy: timestamp, orderDirection: asc,\n'
                        'where: {\n'
                            f'timestamp_gt: {last_date}\n'
                        '}\n'
                    ') {\n'
                        'id\ntxHash\ntrader\nbaseToken\closedPositionSize\n'
                        'closedPositionNotional\nopenNotionalBeforeClose\nrealizedPnl\n'
                        'closedPrice\nblockNumberLogIndex\nblockNumber\ntimestamp\n'
                    '}\n'
                '}\n'
            )
            response = client.execute(query)
            last_date = response['positionCloseds'][-1]['timestamp']
            data.extend(response['positionCloseds'])
        except Exception as e:
            print(e)
            return data
    return data


def position_closed_list_to_dict(position_close: list):
    id = position_close["id"]
    tx_hash = position_close["txHash"]
    trader = position_close["trader"]
    base_token = position_close["baseToken"]
    closed_position_size = position_close["closedPositionSize"]
    closed_position_notional = position_close["closedPositionNotional"]
    open_notional_before_close = position_close["openNotionalBeforeClose"]
    realized_pnl = position_close["realizedPnl"]
    closed_price = position_close["closedPrice"]
    block_number_log_index = position_close["blockNumberLogIndex"]
    block_number = position_close["blockNumber"]
    timestamp = position_close["timestamp"]
    
    return {
        "id": id, "tx_hash": tx_hash, "trader": trader, "base_token": base_token,
        "closed_position_size": closed_position_size, "closed_position_notional": closed_position_notional,
        "open_notional_before_close": open_notional_before_close, "realized_pnl": realized_pnl,
        "closed_price": closed_price, "block_number_log_index": block_number_log_index,
        "block_number": block_number, "timestamp": timestamp
    }


def position_closes_list_to_df(position_closes_list: list):
    position_closes_transformed = [position_closed_list_to_dict(position) for position in position_closes_list]
    position_closes_df = pd.DataFrame(position_closes_transformed)
    position_closes_df["time"] = pd.to_datetime(position_closes_df["timestamp"], unit='s')
    return position_closes_df

#   ===========================================================================================================

#   -----------------------------------     position section    ------------------------------------------------
def get_positions(range_limit: int=20000) -> list:
    """get list of positions as lists

    Args:
        range_limit (int, optional): how many ranges to request. Defaults to 20000.

    Returns:
        list: list of positions as lists
    """
    transport = RequestsHTTPTransport(url = PERPETUAL_V2_GRAPH_ADDRESS, verify=True, retries=3)
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
                        'trader\nbaseToken\npositionSize\n'
                        'openNotional\nentryPrice\n'
                        'tradingVolume\nrealizedPnl\nfundingPayment\n'
                        'tradingFee\nliquidationFee\nblockNumber\n'
                        'timestamp\n'
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


def positions_list_to_dict(position_list: list) -> dict:
    """transform position record from list to dictionary

    Args:
        position_list (list): position record as list

    Returns:
        dict: position record as dictionary
    """
    id = position_list["id"]
    trader = position_list["trader"]
    base_token = position_list["baseToken"]
    position_size = position_list["positionSize"]
    open_notional = position_list["openNotional"]
    entry_price = position_list["entryPrice"]
    trading_volume = position_list["tradingVolume"]
    realized_pnl = position_list["realizedPnl"]
    funding_payment = position_list["fundingPayment"]
    trading_fee = position_list["tradingFee"]
    liquidation_fee = position_list["liquidationFee"]
    block_number = position_list["blockNumber"]
    timestamp = position_list["timestamp"]
    
    return {
        "id": id, "trader": trader, "base_token": base_token, "position_size": position_size,
        "open_notional": open_notional, "entry_price": entry_price, "trading_volume": trading_volume,
        "realized_pnl": realized_pnl, "funding_payment": funding_payment, "trading_fee": trading_fee,
        "liquidation_fee": liquidation_fee, "block_number": block_number, "timestamp": timestamp
    }
    
    
def positions_list_to_df(positions_list: list) -> pd.DataFrame:
    """transform positions as lists to dataframe of positions

    Args:
        positions_list (list): positions as list

    Returns:
        pd.DataFrame: dataframe of positions
    """
    positions_transformed = [positions_list_to_dict(position) for position in positions_list]
    positions_df = pd.DataFrame(positions_transformed)
    positions_df["time"] = pd.to_datetime(positions_df["timestamp"], unit='s')
    return positions_df
#   ============================================================================================================


#   -----------------------------------     position changes section    ----------------------------------------
def get_position_changes(range_limit: int=20000) -> list:
    """get position changes as list of lists

    Args:
        range_limit (int, optional): how many requests to make. Defaults to 20000.

    Returns:
        list: positions as lists of lists
    """
    transport = RequestsHTTPTransport(url = PERPETUAL_V2_GRAPH_ADDRESS, verify=True, retries=3)
    client = Client(transport=transport)
    data = []
    last_date = 0
    
    for skip in tqdm(range(0, range_limit)):
        try:
            query = gql(
                'query{\n'
                    'positionChangeds(first: 1000, orderBy: timestamp, orderDirection: asc,\n'
                        'where: {\n'
                            f'timestamp_gt: {last_date}\n'
                        '}\n'
                    ') {\n'
                        'id\n'
                        'txHash\ntrader\nbaseToken\n'
                        'exchangedPositionSize\nexchangedPositionNotional\n'
                        'fee\nopenNotional\nrealizedPnl\n'
                        'positionSizeAfter\nswappedPrice\nentryPriceAfter\n'
                        'marketPriceAfter\nfromFunctionSignature\nblockNumberLogIndex\n'
                        'blockNumber\ntimestamp\n'
                    '}\n'
                '}\n'
            )
            response = client.execute(query)
            last_date = response['positionChangeds'][-1]['timestamp']
            data.extend(response['positionChangeds'])
        except Exception as e:
            print(e)
            return data
    return data


def position_changes_list_to_dict(position_changes_list: list) -> dict:
    """transform position change record as list into dictionary

    Args:
        position_changes_list (list): position change as list

    Returns:
        dict: position change as dictionary
    """
    id = position_changes_list["id"]
    tx_hash = position_changes_list["txHash"]
    trader = position_changes_list["trader"]
    base_token = position_changes_list["baseToken"]
    exchanged_position_size = position_changes_list["exchangedPositionSize"]
    exchanged_position_notional = position_changes_list["exchangedPositionNotional"]
    fee = position_changes_list["fee"]
    open_notional = position_changes_list["openNotional"]
    realized_pnl = position_changes_list["realizedPnl"]
    position_size_after = position_changes_list["positionSizeAfter"]
    swapped_price = position_changes_list["swappedPrice"]
    entry_price_after = position_changes_list["entryPriceAfter"]
    market_price_after = position_changes_list["marketPriceAfter"]
    from_function_signature = position_changes_list["fromFunctionSignature"]
    block_number_log_index = position_changes_list["blockNumberLogIndex"]
    block_number = position_changes_list["blockNumber"]
    timestamp = position_changes_list["timestamp"]
    
    return {
        "id": id, "tx_hash": tx_hash, "trader": trader, "base_token": base_token,
        "exchanged_position_size": exchanged_position_size, 
        "exchanged_position_notional": exchanged_position_notional,
        "fee": fee, "open_notional": open_notional, "realized_pnl": realized_pnl, 
        "position_size_after": position_size_after,
        "swapped_price": swapped_price, "entry_price_after": entry_price_after, 
        "market_price_after": market_price_after,
        "from_function_signature": from_function_signature, 
        "block_number_log_index": block_number_log_index,
        "block_number": block_number, "timestamp": timestamp
    }
    
    
def position_changes_list_to_df(position_changes_list: list) -> pd.DataFrame:
    """transform position changes as lists of lists into dataframe

    Args:
        position_changes_list (list): position changes as list of lists

    Returns:
        pd.DataFrame: dataframe of position changes
    """
    position_changes_transformed = [position_changes_list_to_dict(position_changes) for position_changes 
                                    in position_changes_list]
    position_changes_df = pd.DataFrame(position_changes_transformed)
    position_changes_df["time"] = pd.to_datetime(position_changes_df["timestamp"], unit='s')
    return position_changes_df
#   ============================================================================================================


#   ------------------------------------    position liquidations sections  ------------------------------------
def get_position_liquidations(range_limit: int=20000) -> list:
    """get position liquidations as list of lists

    Args:
        range_limit (int, optional): how many requests to make. Defaults to 20000.

    Returns:
        list: position liquidations as list of lists
    """
    transport = RequestsHTTPTransport(url = PERPETUAL_V2_GRAPH_ADDRESS, verify=True, retries=3)
    client = Client(transport=transport)
    data = []
    last_date = 0
    
    for skip in tqdm(range(0, range_limit)):
        try:
            query = gql(
                'query{\n'
                    'positionLiquidateds(first: 1000, orderBy: timestamp, orderDirection: asc,\n'
                        'where: {\n'
                            f'timestamp_gt: {last_date}\n'
                        '}\n'
                    ') {\n'
                        'txHash\ntrader\nbaseToken\nliquidator\nliquidationFee\n'
                        'positionSizeAbs\npositionNotionalAbs\nblockNumber\ntimestamp\n'
                    '}\n'
                '}\n'
            )
            response = client.execute(query)
            last_date = response['positionLiquidateds'][-1]['timestamp']
            data.extend(response['positionLiquidateds'])
        except Exception as e:
            print(e)
            return data
    return data


def position_liqudation_list_to_dict(position_liquidation: list) -> dict:
    """transform position liquidation record as list into dictionary

    Args:
        position_liquidation (list): position change as list

    Returns:
        dict: position change as dictionary
    """
    tx_hash = position_liquidation["txHash"]
    trader = position_liquidation["trader"]
    base_token = position_liquidation["baseToken"]
    liquidator = position_liquidation["liquidator"]
    liquidation_fee = position_liquidation["liquidationFee"]
    position_size_abs = position_liquidation["positionSizeAbs"]
    position_notional_abs = position_liquidation["positionNotionalAbs"]
    block_number = position_liquidation["blockNumber"]
    timestamp = position_liquidation["timestamp"]

    return {
        "tx_hash": tx_hash, "trader": trader, "base_token": base_token, "liquidator": liquidator,
        "liquidation_fee": liquidation_fee, "position_size_abs": position_size_abs,
        "position_notional_abs": position_notional_abs, "block_number": block_number,
        "timestamp": timestamp
    }
    
    
def position_liquidations_list_to_df(position_liquidations: list) -> pd.DataFrame:
    """transform position liquidations list of lists into dataframe

    Args:
        position_liquidations (list): position liquidations as list of lists

    Returns:
        pd.DataFrame: position liquidations as dataframe
    """
    position_liquidations_transformed = [position_liqudation_list_to_dict(position_liquidation) for position_liquidation 
                                         in position_liquidations]
    position_liquidations_df = pd.DataFrame(position_liquidations_transformed)
    position_liquidations_df["time"] = pd.to_datetime(position_liquidations_df["timestamp"], unit='s')
    return position_liquidations_df
#   ============================================================================================================


#   -------------------------------------       position closes section     ------------------------------------
def get_position_closes(range_limit: int=20000) -> list:
    """get position closes as list of lists

    Args:
        range_limit (int, optional): how many requests to make. Defaults to 20000.

    Returns:
        list: position closes as list of lists
    """
    transport = RequestsHTTPTransport(url = PERPETUAL_V2_GRAPH_ADDRESS, verify=True, retries=3)
    client = Client(transport=transport)
    data = []
    last_date = 0
    
    for skip in tqdm(range(0, range_limit)):
        try:
            query = gql(
                'query{\n'
                    'positionCloseds(first: 1000, orderBy: timestamp, orderDirection: asc,\n'
                        'where: {\n'
                            f'timestamp_gt: {last_date}\n'
                        '}\n'
                    ') {\n'
                        'id\ntxHash\ntrader\nbaseToken\nclosedPositionSize\n'
                        'closedPositionNotional\nopenNotionalBeforeClose\nrealizedPnl\n'
                        'closedPrice\nblockNumberLogIndex\nblockNumber\ntimestamp\n'
                    '}\n'
                '}\n'
            )
            response = client.execute(query)
            last_date = response['positionCloseds'][-1]['timestamp']
            data.extend(response['positionCloseds'])
        except Exception as e:
            print(e)
            return data
    return data


def position_closes_list_to_dict(position_close: list) -> dict:
    """transform position close from list to dictionary

    Args:
        position_close (list): position close as list

    Returns:
        dict: position close as dictionary
    """
    id = position_close["id"]
    tx_hash = position_close["txHash"]
    trader = position_close["trader"]
    base_token = position_close["baseToken"]
    closed_position_size = position_close["closedPositionSize"]
    closed_position_notional = position_close["closedPositionNotional"]
    open_notional_before_close = position_close["openNotionalBeforeClose"]
    realized_pnl = position_close["realizedPnl"]
    closed_price = position_close["closedPrice"]
    block_number_log_index = position_close["blockNumberLogIndex"]
    block_number = position_close["blockNumber"]
    timestamp = position_close["timestamp"]

    return {
        "id": id, "tx_hash": tx_hash, "trader": trader, "base_token": base_token,
        "closed_position_size": closed_position_size, "closed_position_notional": closed_position_notional,
        "open_notional_before_close": open_notional_before_close, "realized_pnl": realized_pnl,
        "closed_price": closed_price, "block_number_log_index": block_number_log_index, 
        "block_number": block_number, "timestamp": timestamp,
    }
    
    
def position_closes_list_to_df(position_closes_list: list) -> pd.DataFrame:
    """transform position closes as list of lists into dataframe

    Args:
        position_closes_list (list): position closes as list of lists

    Returns:
        pd.DataFrame: dataframe of position closes
    """
    position_closes_transformed = [position_closes_list_to_dict(position_closes) for position_closes 
                                         in position_closes_list]
    position_closes_df = pd.DataFrame(position_closes_transformed)
    print(position_closes_df)
    position_closes_df["time"] = pd.to_datetime(position_closes_df["timestamp"], unit='s')
    return position_closes_df
# ===========================================================================================================


#   -------------------------------------   position history section    -------------------------------------
def get_position_histories(range_limit: int=20000) -> list:
    """get list of position histories as lists

    Args:
        range_limit (int, optional): how many requests to make. Defaults to 20000.

    Returns:
        list: list of position histories as lists
    """
    transport = RequestsHTTPTransport(url = PERPETUAL_V2_GRAPH_ADDRESS, verify=True, retries=3)
    client = Client(transport=transport)
    data = []
    last_date = 0
    
    for skip in tqdm(range(0, range_limit)):
        try:
            query = gql(
                'query{\n'
                    'positionHistories(first: 1000, orderBy: timestamp, orderDirection: asc,\n'
                        'where: {\n'
                            f'timestamp_gt: {last_date}\n'
                        '}\n'
                    ') {\n'
                        'id\ntrader\nbaseToken\npositionSize\nopenNotional\nentryPrice\n'
                        'realizedPnl\nfundingPayment\ntradingFee\nliquidationFee\n'
                        'blockNumber\ntimestamp\n'
                    '}\n'
                '}\n'
            )
            response = client.execute(query)
            last_date = response['positionHistories'][-1]['timestamp']
            data.extend(response['positionHistories'])
        except Exception as e:
            print(e)
            return data
    return data


def position_history_list_to_dict(position_history: list) -> dict:
    """transform position history from list to dictionary

    Args:
        position_history (list): position history as list

    Returns:
        dict: position history as dictionary
    """
    id = position_history["id"]
    trader = position_history["trader"]
    base_token = position_history["baseToken"]
    position_size = position_history["positionSize"]
    open_notional = position_history["openNotional"]
    entry_price = position_history["entryPrice"]
    realized_pnl = position_history["realizedPnl"]
    funding_payment = position_history["fundingPayment"]
    trading_fee = position_history["tradingFee"]
    liquidation_fee = position_history["liquidationFee"]
    block_number = position_history["blockNumber"]
    timestamp = position_history["timestamp"]

    return {
        "id": id, "trader": trader, "base_token": base_token, "position_size": position_size,
        "open_notional": open_notional, "entry_price": entry_price, "realized_pnl": realized_pnl,
        "funding_payment": funding_payment, "trading_fee": trading_fee, "liquidation_fee": liquidation_fee,
        "block_number": block_number, "timestamp": timestamp
    }
    
    
def position_histories_list_to_df(position_histories_list: list) -> pd.DataFrame:
    """transform position histories from list of lists to dataframe

    Args:
        position_histories_list (list): position histories as list of lists

    Returns:
        pd.DataFrame: position histories as dataframe
    """
    position_histories_transformed = [position_history_list_to_dict(position_history) for position_history 
                                         in position_histories_list]
    position_histories_df = pd.DataFrame(position_histories_transformed)
    position_histories_df["time"] = pd.to_datetime(position_histories_df["timestamp"], unit='s')
    return position_histories_df
# ===========================================================================================================


#   ----------------------------------------    funding updated ---------------------------------------------
def get_funding_updates(range_limit: int=20000) -> list:
    """get funding updates as list of lists

    Args:
        range_limit (int, optional): how many requests to make. Defaults to 20000.

    Returns:
        list: funding updates as list of lists
    """
    transport = RequestsHTTPTransport(url = PERPETUAL_V2_GRAPH_ADDRESS, verify=True, retries=3)
    client = Client(transport=transport)
    data = []
    last_date = 0
    
    for skip in tqdm(range(0, range_limit)):
        try:
            query = gql(
                'query{\n'
                    'fundingUpdateds(first: 1000, orderBy: timestamp, orderDirection: asc,\n'
                        'where: {\n'
                            f'timestamp_gt: {last_date}\n'
                        '}\n'
                    ') {\n'
                        'id\ntxHash\nbaseToken\nmarkTwap\nindexTwap\ndailyFundingRate\n'
                        'blockNumberLogIndex\nblockNumber\ntimestamp\n'
                    '}\n'
                '}\n'
            )
            response = client.execute(query)
            last_date = response['fundingUpdateds'][-1]['timestamp']
            data.extend(response['fundingUpdateds'])
        except Exception as e:
            print(e)
            return data
    return data


def funding_updated_list_to_dict(funding_updated: list) -> dict:
    """transform funding update from list to dictionary

    Args:
        funding_updated (list): funding update as list

    Returns:
        dict: funding update as dictionary
    """
    id = funding_updated["id"]
    tx_hash = funding_updated["txHash"]
    base_token = funding_updated["baseToken"]
    mark_twap = funding_updated["markTwap"]
    index_twap = funding_updated["indexTwap"]
    daily_funding_rate = funding_updated["dailyFundingRate"]
    block_number_log_index = funding_updated["blockNumberLogIndex"]
    block_number = funding_updated["blockNumber"]
    timestamp = funding_updated["timestamp"]
    
    return {
        "id": id, "tx_hash": tx_hash, "mark_twap": mark_twap, "index_twap": index_twap,
        "daily_funding_rate": daily_funding_rate, "block_number_log_index": block_number_log_index,
        "block_number": block_number, "base_token": base_token, "timestamp": timestamp
    }
    
    
def funding_updateds_list_to_df(funding_updateds_list: list) -> pd.DataFrame:
    """transform funding updates as list of lists to dataframe

    Args:
        funding_updateds_list (list): funding updates as list of lists

    Returns:
        pd.DataFrame: dataframe of funding updates
    """
    funding_updateds_transformed = [funding_updated_list_to_dict(funding_updated) for funding_updated 
                                    in funding_updateds_list]
    funding_updates_df = pd.DataFrame(funding_updateds_transformed)
    funding_updates_df["time"] = pd.to_datetime(funding_updates_df["timestamp"], unit='s')
    return funding_updates_df
#   ==================================================================================================


#   -----------------------------   funding payment settled section ----------------------------------
def get_funding_payment_settled(range_limit: int=20000) -> list:
    """get funding payments as list of lists

    Args:
        range_limit (int): how many calls to make. Defaults to 20000

    Returns:
        list: list of funding payments as lists
    """
    transport = RequestsHTTPTransport(url = PERPETUAL_V2_GRAPH_ADDRESS, verify=True, retries=3)
    client = Client(transport=transport)
    data = []
    last_date = 0
    
    for skip in tqdm(range(0, range_limit)):
        try:
            query = gql(
                'query{\n'
                    'fundingPaymentSettleds(first: 1000, orderBy: timestamp, orderDirection: asc,\n'
                        'where: {\n'
                            f'timestamp_gt: {last_date}\n'
                        '}\n'
                    ') {\n'
                        'id\ntxHash\ntrader\nbaseToken\nfundingPayment\n'
                        'blockNumberLogIndex\nblockNumber\ntimestamp\n'
                    '}\n'
                '}\n'
            )
            response = client.execute(query)
            last_date = response['fundingPaymentSettleds'][-1]['timestamp']
            data.extend(response['fundingPaymentSettleds'])
        except Exception as e:
            print(e)
            return data
    return data


def funding_payment_settled_list_to_dict(funding_payment_settled: list) -> dict:
    """funding payment as list to dictionary

    Args:
        funding_payment_settled (list): funding payment as list

    Returns:
        dict: funding payment as dictionary
    """
    id = funding_payment_settled["id"]
    tx_hash = funding_payment_settled["txHash"]
    base_token = funding_payment_settled["baseToken"]
    funding_payment = funding_payment_settled["fundingPayment"]
    block_number_log_index = funding_payment_settled["blockNumberLogIndex"]
    block_number = funding_payment_settled["blockNumber"]
    timestamp = funding_payment_settled["timestamp"]
    
    return {
        "id": id, "tx_hash": tx_hash, "base_token": base_token, "funding_payment": funding_payment,
        "block_number_log_index": block_number_log_index, "block_number": block_number, 
        "timestamp": timestamp
    }
    

def funding_payment_settleds_list_to_df(funding_payment_settleds: list) -> pd.DataFrame:
    """funding payments list of lists to dataframe

    Args:
        funding_payment_settleds (list): list of funding payments as lists

    Returns:
        pd.DataFrame: dataframe of funding payments
    """
    funding_payment_settleds_transformed = [funding_payment_settled_list_to_dict(funding_payment_settled)
                                            for funding_payment_settled in funding_payment_settleds]
    funding_payment_settled_df = pd.DataFrame(funding_payment_settleds_transformed)
    funding_payment_settled_df["time"] = pd.to_datetime(funding_payment_settled_df["timestamp"], unit='s')
    return funding_payment_settled_df
#   ======================================================================================================


#   -------------------------------------   liquidity changed section   ----------------------------------
def get_liquidity_changes(range_limit: int=20000) -> list:
    """get liquidity changes as list of lists

    Args:
        range_limit (int, optional): how many requests to do. Defaults to 20000.

    Returns:
        list: liquidity changes as list of lists
    """
    transport = RequestsHTTPTransport(url = PERPETUAL_V2_GRAPH_ADDRESS, verify=True, retries=3)
    client = Client(transport=transport)
    data = []
    last_date = 0
    
    for skip in tqdm(range(0, range_limit)):
        try:
            query = gql(
                'query{\n'
                    'liquidityChangeds(first: 1000, orderBy: timestamp, orderDirection: asc,\n'
                        'where: {\n'
                            f'timestamp_gt: {last_date}\n'
                        '}\n'
                    ') {\n'
                        'id\ntxHash\nmaker\nbaseToken\nquoteToken\n'
                        'lowerTick\nupperTick\nbase\nquote\nliquidity\nquoteFee\n'
                        'fromFunctionSignature\nblockNumberLogIndex\nblockNumber\ntimestamp\n'
                    '}\n'
                '}\n'
            )
            response = client.execute(query)
            last_date = response['liquidityChangeds'][-1]['timestamp']
            data.extend(response['liquidityChangeds'])
        except Exception as e:
            print(e)
            return data
    return data


def liquidity_change_list_to_dict(liquidity_change: list) -> dict:
    """luquidity change record from list to dictionary

    Args:
        liquidity_change (list): liquidity change as list

    Returns:
        dict: liquidity change as dictionary
    """
    id = liquidity_change["id"]
    tx_hash = liquidity_change["txHash"]
    maker = liquidity_change["maker"]
    base_token = liquidity_change["baseToken"]
    quote_token = liquidity_change["quoteToken"]
    lower_tick = liquidity_change["lowerTick"]
    upper_tick = liquidity_change["upperTick"]
    base = liquidity_change["base"]
    quote = liquidity_change["quote"]
    liquidity = liquidity_change["liquidity"]
    quote_fee = liquidity_change["quoteFee"]
    from_function_signature = liquidity_change["fromFunctionSignature"]
    block_number_log_index = liquidity_change["blockNumberLogIndex"]
    block_number = liquidity_change["blockNumber"]
    timestamp = liquidity_change["timestamp"]
    
    return {
        "id": id, "tx_hash": tx_hash, "maker": maker, "base_token": base_token, "quote_token": quote_token,
        "lower_tick": lower_tick, "upper_tick": upper_tick, "base": base, "quote": quote, "liquidity": liquidity,
        "quote_fee": quote_fee, "from_function_signature": from_function_signature,
        "block_number_log_index": block_number_log_index, "block_number": block_number, "timestamp": timestamp
    }
    
    
def liquidity_changes_list_to_df(liquidity_changes: list) -> pd.DataFrame:
    """liquidity changes from list of lists to dataframe

    Args:
        liquidity_changes (list): liquidity changes as list of lists

    Returns:
        pd.DataFrame: liquidity changes as dataframe
    """
    liquidity_changes_transformed = [liquidity_change_list_to_dict(liquidity_change) 
                                     for liquidity_change in liquidity_changes]
    liquidity_changes_df = pd.DataFrame(liquidity_changes_transformed)
    liquidity_changes_df["time"] = pd.to_datetime(liquidity_changes_df["timestamp"], unit='s')
    return liquidity_changes_df
#   ======================================================================================================


#   --------------------------------------  trader market section   --------------------------------------
def get_trader_markets(range_limit: int=20000) -> list:
    """Get trader markets as list of lists

    Args:
        range_limit (int, optional): how many requests to make. Defaults to 20000.

    Returns:
        list: trader markets as list of lists
    """
    transport = RequestsHTTPTransport(url = PERPETUAL_V2_GRAPH_ADDRESS, verify=True, retries=3)
    client = Client(transport=transport)
    data = []
    last_date = 0
    
    for skip in tqdm(range(0, range_limit)):
        try:
            query = gql(
                'query{\n'
                    'traderMarkets(first: 1000, orderBy: timestamp, orderDirection: asc,\n'
                        'where: {\n'
                            f'timestamp_gt: {last_date}\n'
                        '}\n'
                    ') {\n'
                        'id\ntrader\nbaseToken\ntakerPositionSize\nopenNotional\nentryPrice\n'
                        'tradingVolume\nrealizedPnl\nfundingPayment\ntradingFee\n'
                        'liquidationFee\nmakerFee\nblockNumber\ntimestamp\n'
                    '}\n'
                '}\n'
            )
            response = client.execute(query)
            last_date = response['traderMarkets'][-1]['timestamp']
            data.extend(response['traderMarkets'])
        except Exception as e:
            print(e)
            return data
    return data


def trader_market_list_to_dict(trader_market: list) -> dict:
    """trader market record from list to dictionary

    Args:
        trader_market (list): trader market record as list

    Returns:
        dict: trader market record as dict
    """
    id = trader_market["id"]
    trader = trader_market["trader"]
    taker_position_size = trader_market["takerPositionSize"]
    open_notional = trader_market["openNotional"]
    entry_price = trader_market["entryPrice"]
    trading_volume = trader_market["tradingVolume"]
    realized_pnl = trader_market["realizedPnl"]
    funding_payment = trader_market["fundingPayment"]
    trading_fee = trader_market["tradingFee"]
    liquidation_fee = trader_market["liquidationFee"]
    maker_fee = trader_market["makerFee"]
    block_number = trader_market["blockNumber"]
    timestamp = trader_market["timestamp"]
    
    return {
        "id": id, "trader": trader, "taker_position_size": taker_position_size, 
        "open_notional": open_notional, "entry_price": entry_price, "trading_volume": trading_volume,
        "realized_pnl": realized_pnl, "funding_payment": funding_payment, "trading_fee": trading_fee,
        "liquidation_fee": liquidation_fee, "maker_fee": maker_fee, "block_number": block_number,
        "timestamp": timestamp
    }
    
    
def trader_markets_list_to_df(trader_markets: list) -> pd.DataFrame:
    """trader market records from list of lists to dataframe

    Args:
        trader_markets (list): trader markets list of lists

    Returns:
        pd.DataFrame: dataframe of trader markets
    """
    trader_markets_transformed = [trader_market_list_to_dict(trader_market) for trader_market 
                                  in trader_markets]
    trader_markets_df = pd.DataFrame(trader_markets_transformed)
    trader_markets_df["time"] = pd.to_datetime(trader_markets_df["timestamp"], unit='s')
    return trader_markets_df
#   ===================================================================================================


#   -------------------------------------   bad debt happened   ---------------------------------------
def get_bad_debt_happened(range_limit: int=20000) -> list:
    """get bad debt records as list of lists

    Args:
        range_limit (int, optional): how many requests to make. Defaults to 20000.

    Returns:
        list: bad debt as list of lists
    """
    transport = RequestsHTTPTransport(url = PERPETUAL_V2_GRAPH_ADDRESS, verify=True, retries=3)
    client = Client(transport=transport)
    data = []
    last_date = 0
    
    for skip in tqdm(range(0, range_limit)):
        try:
            query = gql(
                'query{\n'
                    'badDebtHappeneds(first: 1000, orderBy: timestamp, orderDirection: asc,\n'
                        'where: {\n'
                            f'timestamp_gt: {last_date}\n'
                        '}\n'
                    ') {\n'
                        'id\ntxHash\ntrader\namount\nblockNumberLogIndex\nblockNumber\n'
                        'timestamp\n'
                    '}\n'
                '}\n'
            )
            response = client.execute(query)
            last_date = response['traderMarkets'][-1]['timestamp']
            data.extend(response['traderMarkets'])
        except Exception as e:
            print(e)
            return data
    return data


def bad_debt_happened_list_to_dict(bad_debt_happened: list) -> dict:
    """bad debt record from list to dict

    Args:
        bad_debt_happened (list): bad debt record as list

    Returns:
        dict: bad debt record as dict
    """
    id = bad_debt_happened["id"]
    tx_hash = bad_debt_happened["txHash"]
    trader = bad_debt_happened["trader"]
    amount = bad_debt_happened["amount"]
    block_number_log_index = bad_debt_happened["blockNumberLogIndex"]
    block_number = bad_debt_happened["block_number"]
    timestamp = bad_debt_happened["timestamp"]
    
    return {
        "id": id, "tx_hash": tx_hash, "trader": trader, "amount": amount, 
        "block_number_log_index": block_number_log_index, "block_number": block_number,
        "timestamp": timestamp
    }
    
    
def bad_debt_happeneds_list_to_df(bad_debt_happeneds: list) -> pd.DataFrame:
    """bad debt from list of lists to dataframe

    Args:
        bad_debt_happeneds (list): bad debt as list of lists

    Returns:
        pd.DataFrame: dataframe of bad debts
    """
    bad_debt_happeneds_transformed = [bad_debt_happened_list_to_dict(bad_debt_happened) 
                                       for bad_debt_happened in bad_debt_happeneds]
    bad_debt_happened_df = pd.DataFrame(bad_debt_happeneds_transformed)
    bad_debt_happened_df["time"] = pd.to_datetime(bad_debt_happened_df["timestamp"], unit='s')
    return bad_debt_happened_df
#   ===================================================================================================


#   ---------------------------------   trader day data section ---------------------------------------
def get_trader_day_data(range_limit: int=20000) -> list:
    """daily trader data as list of lists

    Args:
        range_limit (int, optional): how many requests to make. Defaults to 20000.

    Returns:
        list: daily trader data as list of lists
    """
    transport = RequestsHTTPTransport(url = PERPETUAL_V2_GRAPH_ADDRESS, verify=True, retries=3)
    client = Client(transport=transport)
    data = []
    last_date = 0
    
    for skip in tqdm(range(0, range_limit)):
        try:
            query = gql(
                'query{\n'
                    'traderDayDatas(first: 1000, orderBy: timestamp, orderDirection: asc,\n'
                        'where: {\n'
                            f'date_gt: {last_date}\n'
                        '}\n'
                    ') {\n'
                        'id\ntrader\ndate\ntradingVolume\nfee\nrealizedPnl\n'
                    '}\n'
                '}\n'
            )
            response = client.execute(query)
            last_date = response['traderDayDatas'][-1]['date']
            data.extend(response['traderDayDatas'])
        except Exception as e:
            print(e)
            return data
    print(data)
    return data


def trader_day_record_list_to_dict(trader_day_record: list) -> dict:
    """trader day record from list to dict

    Args:
        trader_day_record (list): trader day record as list

    Returns:
        dict: trader day record as dict
    """
    id = trader_day_record["id"]
    trader = trader_day_record["trader"]
    trading_volume = trader_day_record["tradingVolume"]
    date = trader_day_record["date"]
    fee = trader_day_record["fee"]
    realized_pnl = trader_day_record["realizedPnl"]
    
    return {
        "id": id, "trader": trader, "trading_volume": trading_volume, "fee": fee,
        "realized_pnl": realized_pnl, "date": date
    }
    

def trader_day_data_list_to_df(trader_day_data: list) -> pd.DataFrame:
    """trader day data from list of lists to dataframe

    Args:
        trader_day_data (list): trader day data as list of lists

    Returns:
        pd.DataFrame: dataframe of trader day data
    """
    trader_day_data_transformed = [trader_day_record_list_to_dict(trader_day_record) 
                                   for trader_day_record in trader_day_data]
    trader_day_data_df = pd.DataFrame(trader_day_data_transformed)
    return trader_day_data_df
#   ======================================================================================================

#   ---------------------------------   withdraws section   ----------------------------------------------
def get_withdraws(range_limit: int=20000) -> list:
    """get withdraws as list of lists

    Args:
        range_limit (int, optional): how many requests to make. Defaults to 20000.

    Returns:
        list: withdraws as list of lists
    """
    transport = RequestsHTTPTransport(url = PERPETUAL_V2_GRAPH_ADDRESS, verify=True, retries=3)
    client = Client(transport=transport)
    data = []
    last_date = 0
    
    for skip in tqdm(range(0, range_limit)):
        try:
            query = gql(
                'query{\n'
                    'withdrawns(first: 1000, orderBy: timestamp, orderDirection: asc,\n'
                        'where: {\n'
                            f'timestamp_gt: {last_date}\n'
                        '}\n'
                    ') {\n'
                        'id\ntxHash\ntrader\ncollateralToken\namount\nblockNumberLogIndex\n'
                        'blockNumber\ntimestamp\n'
                    '}\n'
                '}\n'
            )
            response = client.execute(query)
            last_date = response['withdrawns'][-1]['timestamp']
            data.extend(response['withdrawns'])
        except Exception as e:
            print(e)
            return data
    return data


def withdraw_list_to_dict(withdraw: list) -> dict:
    """withdraw record from list to dict

    Args:
        withdraw (list): withdraw record as list

    Returns:
        dict: withdraw record as dict
    """
    id = withdraw["id"]
    tx_hash = withdraw["txHash"]
    trader = withdraw["trader"]
    collateral_token = withdraw["collateralToken"]
    amount = withdraw["amount"]
    block_number_log_index = withdraw["blockNumberLogIndex"]
    block_number = withdraw["blockNumber"]
    timestamp = withdraw["timestamp"]
    
    return {
        "id": id, "tx_hash": tx_hash, "trader": trader, "collateral_token": collateral_token,
        "amount": amount, "block_number_log_index": block_number_log_index, 
        "block_number": block_number, "timestamp": timestamp
    }
    
    
def withdraws_list_to_df(withdraws: list) -> pd.DataFrame:
    """withdraws from list of lists to dataframe

    Args:
        withdraws (list): withdraws as list of lists

    Returns:
        pd.DataFrame: dataframe of withdraws
    """
    withdraws_transformed = [withdraw_list_to_dict(withdraw) for withdraw in withdraws]
    withdraws_df = pd.DataFrame(withdraws_transformed)
    withdraws_df["time"] = pd.to_datetime(withdraws_df["timestamp"], unit='s')
    return withdraws_df
#   =====================================================================================================


#   -------------------------------     deposited section   ---------------------------------------------
def get_depositeds(range_limit: int=20000) -> list:
    """get deposits as list of lists

    Args:
        range_limit (int, optional): how many requests to make. Defaults to 20000.

    Returns:
        list: deposits as list of lists
    """
    transport = RequestsHTTPTransport(url = PERPETUAL_V2_GRAPH_ADDRESS, verify=True, retries=3)
    client = Client(transport=transport)
    data = []
    last_date = 0
    
    for skip in tqdm(range(0, range_limit)):
        try:
            query = gql(
                'query{\n'
                    'depositeds(first: 1000, orderBy: timestamp, orderDirection: asc,\n'
                        'where: {\n'
                            f'timestamp_gt: {last_date}\n'
                        '}\n'
                    ') {\n'
                        'id\ntxHash\ntrader\ncollateralToken\namount\nblockNumberLogIndex\n'
                        'blockNumber\ntimestamp\n'
                    '}\n'
                '}\n'
            )
            response = client.execute(query)
            last_date = response['depositeds'][-1]['timestamp']
            data.extend(response['depositeds'])
        except Exception as e:
            print(e)
            return data
    return data


def deposited_list_to_dict(deposited: list) -> dict:
    """deposit record from list to dict

    Args:
        deposited (list): deposit as list

    Returns:
        dict: deposit as dict
    """
    id = deposited["id"]
    tx_hash = deposited["txHash"]
    trader = deposited["trader"]
    collateral_token = deposited["collateralToken"]
    amount = deposited["amount"]
    block_number_log_index = deposited["blockNumberLogIndex"]
    block_number = deposited["blockNumber"]
    timestamp = deposited["timestamp"]
    
    return {
        "id": id, "tx_hash": tx_hash, "trader": trader, "collateral_token": collateral_token,
        "amount": amount, "block_number_log_index": block_number_log_index, 
        "block_number": block_number, "timestamp": timestamp
    }
    
    
def depositeds_list_to_df(depositeds: list) -> pd.DataFrame:
    """deposits from list of lists to dataframe

    Args:
        depositeds (list): deposits as list of lists

    Returns:
        pd.DataFrame: dataframe of deposits
    """
    depositeds_transformed = [deposited_list_to_dict(deposited) for deposited in depositeds]
    depositeds_df = pd.DataFrame(depositeds_transformed)
    depositeds_df["time"] = pd.to_datetime(depositeds_df["timestamp"], unit='s')
    return depositeds_df
#   ========================================================================================================


#   ----------------------------------  realized pnl section    --------------------------------------------
def get_pnl_realizeds(range_limit: int=20000) -> list:
    """get realized pnl history as list of lists 

    Args:
        range_limit (int, optional): how many requests to make. Defaults to 20000.

    Returns:
        list: realized pnl history as list of lists
    """
    transport = RequestsHTTPTransport(url = PERPETUAL_V2_GRAPH_ADDRESS, verify=True, retries=3)
    client = Client(transport=transport)
    data = []
    last_date = 0
    
    for skip in tqdm(range(0, range_limit)):
        try:
            query = gql(
                'query{\n'
                    'pnlRealizeds(first: 1000, orderBy: timestamp, orderDirection: asc,\n'
                        'where: {\n'
                            f'timestamp_gt: {last_date}\n'
                        '}\n'
                    ') {\n'
                        'id\ntxHash\ntrader\namount\nblockNumberLogIndex\nblockNumber\ntimestamp\n'
                    '}\n'
                '}\n'
            )
            response = client.execute(query)
            last_date = response['pnlRealizeds'][-1]['timestamp']
            data.extend(response['pnlRealizeds'])
        except Exception as e:
            print(e)
            return data
    return data


def pnl_realized_list_to_dict(pnl_realized: list) -> pd.DataFrame:
    """realized pnl history record from list to dict

    Args:
        pnl_realized (list): realized pnl record as list

    Returns:
        pd.DataFrame: realized pnl record as dict
    """
    id = pnl_realized["id"]
    tx_hash = pnl_realized["txHash"]
    trader = pnl_realized["trader"]
    amount = pnl_realized["amount"]
    block_number_log_index = pnl_realized["blockNumberLogIndex"]
    block_number = pnl_realized["blockNumber"]
    timestamp = pnl_realized["timestamp"]
    
    return {
        "id": id, "tx_hash": tx_hash, "trader": trader, "amount": amount,
        "block_number_log_index": block_number_log_index, "block_number": block_number,
        "timestamp": timestamp
    }
    
    
def pnl_realizeds_list_to_df(pnl_realizeds: list) -> pd.DataFrame:
    """realized pnl from list of lists to dataframe

    Args:
        pnl_realizeds (list): realized pnl history as list of lists

    Returns:
        pd.DataFrame: dataframe of realized pnl history
    """
    pnl_realizeds_transformed = [pnl_realized_list_to_dict(pnl_realized) for pnl_realized in pnl_realizeds]
    pnl_realized_df = pd.DataFrame(pnl_realizeds_transformed)
    pnl_realized_df["time"] = pd.to_datetime(pnl_realized_df["timestamp"], unit='s')
    return pnl_realized_df
#   ========================================================================================================

#   ----------------------------------  makers section    --------------------------------------------------
def get_makers(range_limit: int=20000) -> list:
    """get makers on the platform 

    Args:
        range_limit (int, optional): how many requests to make. Defaults to 20000.

    Returns:
        list: makers on the platform as list ot lists
    """
    transport = RequestsHTTPTransport(url = PERPETUAL_V2_GRAPH_ADDRESS, verify=True, retries=3)
    client = Client(transport=transport)
    data = []
    last_date = 0
    
    for skip in tqdm(range(0, range_limit)):
        try:
            query = gql(
                'query{\n'
                    'makers(first: 1000, orderBy: timestamp, orderDirection: asc,\n'
                        'where: {\n'
                            f'timestamp_gt: {last_date}\n'
                        '}\n'
                    ') {\n'
                        'id\ncollectedFee\nblockNumber\ntimestamp\n'
                    '}\n'
                '}\n'
            )
            response = client.execute(query)
            last_date = response['makers'][-1]['timestamp']
            data.extend(response['makers'])
        except Exception as e:
            print(e)
            return data
    return data


def maker_list_to_dict(maker: list) -> pd.DataFrame:
    """realized pnl history record from list to dict

    Args:
        maker (list): realized pnl record as list

    Returns:
        pd.DataFrame: realized pnl record as dict
    """
    id = maker["id"]
    collected_fee = maker["collectedFee"]
    block_number = maker["blockNumber"]
    timestamp = maker["timestamp"]
    
    return {
        "id": id, "collected_fee": collected_fee, "block_number": block_number,
        "timestamp": timestamp
    }
    
    
def makers_list_to_df(makers: list) -> pd.DataFrame:
    """realized pnl from list of lists to dataframe

    Args:
        makers (list): makers history as list of lists

    Returns:
        pd.DataFrame: dataframe of realized pnl history
    """
    makers_transformed = [maker_list_to_dict(maker) for maker in makers]
    maker_df = pd.DataFrame(makers_transformed)
    maker_df["time"] = pd.to_datetime(maker_df["timestamp"], unit='s')
    return maker_df
#   ========================================================================================================

#   ----------------------------------  open orders section    ---------------------------------------------
def get_open_orders(range_limit: int=20000) -> list:
    """get makers on the platform 

    Args:
        range_limit (int, optional): how many requests to make. Defaults to 20000.

    Returns:
        list: open orders on the platform as list ot lists
    """
    transport = RequestsHTTPTransport(url = PERPETUAL_V2_GRAPH_ADDRESS, verify=True, retries=3)
    client = Client(transport=transport)
    data = []
    last_date = 0
    
    for skip in tqdm(range(0, range_limit)):
        try:
            query = gql(
                'query{\n'
                    'openOrders(first: 1000, orderBy: timestamp, orderDirection: asc,\n'
                        'where: {\n'
                            f'timestamp_gt: {last_date}\n'
                        '}\n'
                    ') {\n'
                        'id\nmaker\nbaseToken\nlowerTick\nupperTick\nliquidity\ncollectedFee\n'
                        'collectedFeeInThisLifecycle\nblockNumber\ntimestamp\n'
                    '}\n'
                '}\n'
            )
            response = client.execute(query)
            last_date = response['openOrders'][-1]['timestamp']
            data.extend(response['openOrders'])
        except Exception as e:
            print(e)
            return data
    return data


def open_order_list_to_dict(open_order: list) -> dict:
    """open order history record from list to dict

    Args:
        open_order (list): realized pnl record as list

    Returns:
        dict: open_order record as dict
    """
    id = open_order["id"]
    base_token = open_order["baseToken"]
    lower_tick = open_order["lowerTick"]
    upper_tick = open_order["upperTick"]
    liquidity = open_order["liquidity"]
    collected_fee = open_order["collectedFee"]
    collected_fee_in_lifecycle = open_order["collectedFeeInThisLifecycle"]
    block_number = open_order["blockNumber"]
    timestamp = open_order["timestamp"]
    
    return {
        "id": id, "base_token": base_token, "lower_tick": lower_tick, "upper_tick": upper_tick,
        "liquidity": liquidity, "collected_fee": collected_fee, 
        "collected_fee_in_lifecycle": collected_fee_in_lifecycle,
        "block_number": block_number, "timestamp": timestamp
    }
    

def open_orders_list_to_df(open_orders: list) -> pd.DataFrame:
    """realized pnl from list of lists to dataframe

    Args:
        open_orders (list): open orders history as list of lists

    Returns:
        pd.DataFrame: dataframe of open orders history
    """
    open_orders_transformed = [open_order_list_to_dict(open_order) for open_order in open_orders]
    open_order_df = pd.DataFrame(open_orders_transformed)
    open_order_df["time"] = pd.to_datetime(open_order_df["timestamp"], unit='s')
    return open_order_df


#   ---------------------------------   trader day data section ---------------------------------------
def get_collateral_liquidations(range_limit: int=20000) -> list:
    """collateral liquidations  as list of lists

    Args:
        range_limit (int, optional): how many requests to make. Defaults to 20000.

    Returns:
        list: collateral liquidations as list of lists
    """
    transport = RequestsHTTPTransport(url = PERPETUAL_V2_GRAPH_ADDRESS, verify=True, retries=3)
    client = Client(transport=transport)
    data = []
    last_date = 0
    
    for skip in tqdm(range(0, range_limit)):
        try:
            query = gql(
                'query{\n'
                    'collateralLiquidateds(first: 1000, orderBy: timestamp, orderDirection: asc,\n'
                        'where: {\n'
                            f'timestamp_gt: {last_date}\n'
                        '}\n'
                    ') {\n'
                        'id\ntxHash\ntrader\ncollateralToken\nliquidator\ncollateral\n'
                        'repaidSettlementWithoutInsuranceFundFee\ninsuranceFundFee\n'
                        'discountRatio\nblockNumberLogIndex\nblockNumber\ntimestamp'
                    '}\n'
                '}\n'
            )
            response = client.execute(query)
            last_date = response['collateralLiquidateds'][-1]['timestamp']
            data.extend(response['collateralLiquidateds'])
        except Exception as e:
            print(e)
            return data
    print(data)
    return data


def collateral_liquidation_list_to_dict(collateral_liquidation: list) -> dict:
    """collateral liquidation from list to dict

    Args:
        collateral_liquidation (list): collateral liquidation as list

    Returns:
        dict: trader day record as dict
    """
    id = collateral_liquidation["id"]
    tx_hash = collateral_liquidation["txHash"]
    trader = collateral_liquidation["trader"]
    collateral_token = collateral_liquidation["collateralToken"]
    liquidator = collateral_liquidation["liquidator"]
    collateral = collateral_liquidation["collateral"]
    repaid_settlement_without_insurance_fund_fee = collateral_liquidation[
        "repaidSettlementWithoutInsuranceFundFee"]
    insurance_fund_fee = collateral_liquidation["insuranceFundFee"]
    discount_ratio = collateral_liquidation["discountRatio"]
    block_number_log_index = collateral_liquidation["blockNumberLogIndex"]
    block_number = collateral_liquidation["blockNumber"]
    timestamp = collateral_liquidation["timestamp"]
    
    return {
        "id": id, "tx_hash": tx_hash, "trader": trader, "collateral_token": collateral_token,
        "liquidator": liquidator, "collateral": collateral,
        "repaid_settlement_without_insurance_fund_fee": repaid_settlement_without_insurance_fund_fee,
        "insurance_fund_fee": insurance_fund_fee, "discount_ratio": discount_ratio,
        "block_number_log_index": block_number_log_index, "block_number": block_number,
        "timestamp": timestamp
    }
    

def collateral_liquidations_list_to_df(collateral_liquidations: list) -> pd.DataFrame:
    """collateral_liquidations from list of lists to dataframe

    Args:
        collateral_liquidations (list): collateral liquidations as list of lists

    Returns:
        pd.DataFrame: dataframe of collateral liquidations
    """
    collateral_liquidations_transformed = [collateral_liquidation_list_to_dict(trader_day_record) 
                                   for trader_day_record in collateral_liquidations]
    collateral_liquidations_df = pd.DataFrame(collateral_liquidations_transformed)
    return collateral_liquidations_df
#   ======================================================================================================
