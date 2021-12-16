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


def show_swaps_count_moving_averages(swaps_df: pd.DataFrame, pool_name: str, x_size: int=10, y_size: int=5):
    """Show moving averages of the transactions count

    Args:
        swaps_df (pd.DataFrame): swap transaction history
        pool_name (str): name of pool
        x_size (int, optional): width of figure. Defaults to 10.
        y_size (int, optional): height of figure. Defaults to 5.
    """
    # transform unix timestamps into datetime
    transactions_time = swaps_df.copy()
    transactions_time.timestamp = pd.to_datetime(swaps_df.timestamp, unit='s')
    
    # set index datetime column, resample data and find rolling average per week
    transactions_time.index = transactions_time.timestamp
    transactions_time = transactions_time.resample('1D').size()
    transactions_avg_time = transactions_time.rolling('7D').mean()
    
    fig, ax = plt.subplots(figsize=(x_size, y_size))
    fig.autofmt_xdate()

    # plot presented information
    ax.plot_date(transactions_time.index, transactions_time, linestyle='solid', marker=None, label='Daily average')
    ax.plot_date(transactions_avg_time.index, transactions_avg_time, linestyle='solid', marker=None, color='red', label='Weekly rolling average')
    
    # set labels
    ax.set_xlabel("Day")
    ax.set_ylabel("Count")
    ax.set_title("Daily swaps count of pool " + pool_name)
    fig.legend()
    

def show_swaps_reserves_evolution_through_time(swaps_df: pd.DataFrame, first_token_reserve_name: str, second_token_reserve_name: str, 
                                               x: int=10, y: int=5):
    """Draw reserves distributions through time

    Args:
        swaps_df (pd.DataFrame): daily reserves history
        first_token_reserve_name (str): name of the first token
        second_token_reserve_name (str): name of the second token
        x (int, optional): width of the figure. Defaults to 10.
        y (int, optional): height of the figure. Defaults to 5.
    """
    fig = plt.figure(figsize=(x, y))
    
    plt.subplot(1, 2, 1)
    sns.lineplot(data=swaps_df, x='date', y='reserve0', color='green').set_title(first_token_reserve_name)
    plt.subplot(1, 2, 2)
    sns.lineplot(data=swaps_df, x='date', y='reserve1', color='red').set_title(second_token_reserve_name)
    
    fig.autofmt_xdate()
    plt.show()
    
    
def show_pool_price_evolution_from_reserves(df: pd.DataFrame, first_token_price_name: str, second_token_price_name: str, 
                                            x: int=10, y: int=5, hspace: float=0.25, wspace: float=0.25):
    """Show reserve-based price distributions. Ensure that you set names of the first and the
    second tokens correctly, considering that addressing the reserves is abstract and price
    may not match their names

    Args:
        df (pd.DataFrame): daily reserves updates
        first_token_price_name (str): name of the first token
        second_token_price_name (str): name of the second token
        x (int, optional): width of the figure. Defaults to 10.
        y (int, optional): height of the figure. Defaults to 5.
        hspace (float, optional): height space between charts. Defaults to 0.25.
        wspace (float, optional): width space between charts. Defaults to 0.25.
    """
    fig = plt.figure(figsize=(x, y))    
    
    df['first_price'] = df['reserve0'] / df['reserve1']
    df['second_price'] = df['reserve1'] / df['reserve0']
    
    plt.subplot(1, 2, 1)
    sns.lineplot(data=df, x='date', y='first_price', color='green').set_title(first_token_price_name)
    plt.subplot(1, 2, 2)
    sns.lineplot(data=df, x='date', y='second_price', color='red').set_title(second_token_price_name)

    fig.autofmt_xdate()
    plt.subplots_adjust(wspace=wspace, hspace=hspace)
    plt.show()
    
    
def show_swaps_amount_in_moving_averages(swaps_df: pd.DataFrame, pool_name: str, x_size: int=10, y_size: int=5):
    """Show moving averages of transaction amount in values

    Args:
        swaps_df (pd.DataFrame): swapping history
        pool_name (str): name of the pool
        x_size (int, optional): [description]. width of the figure.
        y_size (int, optional): [description]. height of the figure.
    """
    # transform unix timestamps into datetime
    transactions_time = swaps_df.copy()
    transactions_time.timestamp = pd.to_datetime(swaps_df.timestamp, unit='s')
    
    # set index datetime column, resample data and find rolling average per week
    transactions_time.index = transactions_time.timestamp
    transactions_time = transactions_time.resample('1D').mean()
    transactions_avg_time = transactions_time.rolling('7D').mean()
    
    fig, ax = plt.subplots(figsize=(x_size, y_size))
    fig.autofmt_xdate()

    # plot presented information
    ax.plot_date(transactions_time.index, transactions_time.amount_in, linestyle='solid', marker=None, label='Number of swaps per day')
    ax.plot_date(transactions_avg_time.index, transactions_avg_time.amount_in, linestyle='solid', marker=None, color='red', label='Moving average 7 days')
    
    # set labels
    ax.set_xlabel("Day")
    ax.set_ylabel("Value")
    ax.set_title("Daily swaps in of pool " + pool_name)
    fig.legend()