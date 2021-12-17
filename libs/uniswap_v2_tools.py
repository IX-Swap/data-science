import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
import sys


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
    ax.plot_date(transactions_time.index, transactions_time, linestyle='solid', marker=None, label='Daily count')
    ax.plot_date(transactions_avg_time.index, transactions_avg_time, linestyle='solid', marker=None, color='red', label='Weekly rolling count')
    
    # set labels
    ax.set_xlabel("Day")
    ax.set_ylabel("Count")
    ax.set_title("Daily swaps count of pool " + pool_name)
    fig.legend()
    

def show_reserves_time_distribution(swaps_df: pd.DataFrame, first_token_reserve_name: str, second_token_reserve_name: str, 
                                               x: int=10, y: int=5, hspace: float=0.25, wspace: float=0.25):
    """Draw reserves distributions through time

    Args:
        swaps_df (pd.DataFrame): daily reserves history
        first_token_reserve_name (str): name of the first token
        second_token_reserve_name (str): name of the second token
        x (int, optional): width of the figure. Defaults to 10.
        y (int, optional): height of the figure. Defaults to 5.
        hspace (float, optional): height space between charts. Defaults to 0.25.
        wspace (float, optional): width space between charts. Defaults to 0.25.
    """
    fig = plt.figure(figsize=(x, y))
    
    plt.subplot(1, 2, 1)
    sns.lineplot(data=swaps_df, x='date', y='reserve0', color='green').set_title(first_token_reserve_name)
    plt.subplot(1, 2, 2)
    sns.lineplot(data=swaps_df, x='date', y='reserve1', color='red').set_title(second_token_reserve_name)
    
    fig.autofmt_xdate()
    plt.subplots_adjust(wspace=wspace, hspace=hspace)
    plt.show()
    
    
def show_reserve_price_distributions(df: pd.DataFrame, first_token_price_name: str, second_token_price_name: str, 
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
    ax.plot_date(transactions_time.index, transactions_time.amount_in, linestyle='solid', marker=None, label='Daily average')
    ax.plot_date(transactions_avg_time.index, transactions_avg_time.amount_in, linestyle='solid', marker=None, color='red', 
                 label='Weekly rolling average')
    
    # set labels
    ax.set_xlabel("Day")
    ax.set_ylabel("Value")
    ax.set_title("Averages of swaps in values of the pool" + pool_name)
    fig.legend()
    
    
def calc_price_and_increase_rates(df: pd.DataFrame):
    """Append prices conform reserves changes and find price increase rates

    Args:
        df (pd.DataFrame): reserves dataframe
    """
    #   setting current price for each reserves update
    first_price_sequence = df.reserve0 / df.reserve1
    second_price_sequence = df.reserve1 / df.reserve0
    df['first_price'] = first_price_sequence
    df['second_price'] = second_price_sequence

    first_price_sequence = first_price_sequence.shift(periods=-1)
    second_price_sequence = second_price_sequence.shift(periods=-1)

    df['first_price_increase_rate'] = ((df.first_price - first_price_sequence) / first_price_sequence) * 100
    df['second_price_increase_rate'] = ((df.second_price - second_price_sequence) / second_price_sequence) * 100
    
    
def calc_price_and_increase_rates(df: pd.DataFrame):
    """Find reserve-based prices and prices increase rates

    Args:
        df (pd.DataFrame): reserves dataframe
    """
    first_price_sequence = df.reserve0 / df.reserve1
    second_price_sequence = df.reserve1 / df.reserve0
    df['first_price'] = first_price_sequence
    df['second_price'] = second_price_sequence

    first_price_sequence = first_price_sequence.shift(periods=-1)
    second_price_sequence = second_price_sequence.shift(periods=-1)

    df['first_price_increase_rate'] = ((df.first_price - first_price_sequence) / first_price_sequence) * 100
    df['second_price_increase_rate'] = ((df.second_price - second_price_sequence) / second_price_sequence) * 100
    
    
def increase_rate_moving_averages(df: pd.DataFrame, first_plot_name: str, second_plot_name: str, x_size: int=10, y_size: int=5, wspace: int=0.1, hspace: int=0.1):
    """plot price change rates moving averages

    Args:
        df (pd.DataFrame): reserves dataframe
        first_plot_name (str): name of first plot
        second_plot_name (str): name of second plot
        x_size (int, optional): x-size of window. Defaults to 10.
        y_size (int, optional): y-size of window. Defaults to 5.
        wspace (int, optional): space between plots. Defaults to 0.1.
        hspace (int, optional): height space between plots. Defaults to 0.1.
    """
    # copy dataframe and get date as index
    transactions_time = df.copy()
    transactions_time.index = transactions_time.date
    
    # resample data and find rolling average per week
    transactions_time = transactions_time.resample('7D').mean()
    transactions_avg_time = transactions_time.rolling('14D').mean()
    
    fig = plt.subplots(figsize=(x_size, y_size))
    
    plt.subplot(1, 2, 1)
    sns.lineplot(data=transactions_time, x='date', y='first_price_increase_rate', color='green', label='7 days mean')
    plt.subplot(1, 2, 1)
    sns.lineplot(data=transactions_avg_time, x='date', y='first_price_increase_rate', color='red', 
                 label='14 days rolling mean').set_title(first_plot_name)
    
    plt.subplot(1, 2, 2)
    sns.lineplot(data=transactions_time, x='date', y='second_price_increase_rate', color='green', label='7 days mean')
    plt.subplot(1, 2, 2)
    sns.lineplot(data=transactions_avg_time, x='date', y='second_price_increase_rate', color='red', 
                 label='14 days rolling mean').set_title(second_plot_name)
    
    plt.subplots_adjust(wspace=wspace, hspace=hspace)
    plt.show()
    
    
def swaps_price_change_rates_moving_averages(df: pd.DataFrame, first_token: str, second_token: str, first_plot_name: str, second_plot_name: str, 
                                               x_size: int=10, y_size: int=5, wspace: int=0.1, hspace: int=0.1):
    """swaps price inrease rates moving averages plot using seaborn

    Args:
        df (pd.DataFrame): swaps dataframe with swaps prices and swaps prices increase rates
        first_token (str): name of the first token
        second_token (str): name of the second token
        first_plot_name (str): name of the first subplot
        second_plot_name (str): name of the second subplot
        x_size (int, optional): plot width. Defaults to 10.
        y_size (int, optional): plot height. Defaults to 5.
        wspace (int, optional): width space between subplots. Defaults to 0.1.
        hspace (int, optional): height space between subplots. Defaults to 0.1.
    """
    first_transactions_time = df[df.token_in == first_token]
    second_transactions_time = df[df.token_in == second_token]
    first_transactions_time.index = first_transactions_time.timestamp
    second_transactions_time.index = second_transactions_time.timestamp
    
    first_transactions_time = first_transactions_time.resample('1D').mean()
    first_transactions_avg_time = first_transactions_time.rolling('7D').mean()
    second_transactions_time = second_transactions_time.resample('1D').mean()
    second_transactions_avg_time = second_transactions_time.rolling('7D').mean()
    
    fig = plt.subplots(figsize=(x_size, y_size))
    
    plt.subplot(1, 2, 1)
    sns.lineplot(data=first_transactions_time, x='timestamp', y='price_change_rate', color='green', 
                 label='1 day mean')
    plt.subplot(1, 2, 1)
    sns.lineplot(data=first_transactions_avg_time, x='timestamp', y='price_change_rate', 
                 color='red', label='7 days rolling mean').set_title(first_plot_name)
    
    plt.subplot(1, 2, 2)
    sns.lineplot(data=second_transactions_time, x='timestamp', y='price_change_rate', color='green', 
                 label='1 day mean')
    plt.subplot(1, 2, 2)
    sns.lineplot(data=second_transactions_avg_time, x='timestamp', y='price_change_rate', 
                 color='red', label='7 days rolling mean').set_title(second_plot_name)
    
    plt.subplots_adjust(wspace=wspace, hspace=hspace)
    plt.show()
    
    
def pyplot_line_swap_change_rate(df: pd.DataFrame, first_token: str, second_token: str, xsize: int=20, ysize=10, wspace: float=0.1, hspace: float=0.1):
    """plot using pyplot distribution of swap prices change rates

    Args:
        df (pd.DataFrame): swaps dataframe with found swaps prices and swaps prices change rates
        first_token (str): name of the first token
        second_token (str): name of the second token
        xsize (int, optional): width of plot. Defaults to 20.
        ysize (int, optional): height of plot. Defaults to 10.
        wspace (float, optional): width space between subplots. Defaults to 0.1.
        hspace (float, optional): height space between subplots. Defaults to 0.1.
    """
    fig, ax = plt.subplots(figsize=(xsize, ysize))

    ax1 = plt.subplot(1, 2, 1)
    ax1.plot_date(df[(df.token_in == first_token)].timestamp, df[(df.token_in == first_token)].price_change_rate, 
                linestyle='solid', marker=None)
    ax1.set_xlabel("Time")
    ax1.set_ylabel("Change rate in percents")
    ax1.set_title("Swap price change rate for " + first_token + " price")

    ax2 = plt.subplot(1, 2, 2)
    ax2.plot_date(df[(df.token_in == second_token)].timestamp, df[(df.token_in == second_token)].price_change_rate, 
                linestyle='solid', marker=None, color='red')
    ax2.set_xlabel("Time")
    ax2.set_ylabel("Change rate in percents")
    ax2.set_title("Swap price change rate for " + second_token + " price")

    fig.autofmt_xdate()
    fig.subplots_adjust(wspace=wspace, hspace=hspace) 

    plt.show()
    
    
def pyplot_line_swap_prices(df: pd.DataFrame, first_token: str, second_token: str, xsize: int=20, ysize=10, wspace: float=0.1, hspace: float=0.1):
    """plot using pyplot distribution of swap prices change rates

    Args:
        df (pd.DataFrame): swaps dataframe with found swaps prices and swaps prices change rates
        first_token (str): name of the first token
        second_token (str): name of the second token
        xsize (int, optional): width of plot. Defaults to 20.
        ysize (int, optional): height of plot. Defaults to 10.
        wspace (float, optional): width space between subplots. Defaults to 0.1.
        hspace (float, optional): height space between subplots. Defaults to 0.1.
    """
    fig, ax = plt.subplots(figsize=(xsize, ysize))

    ax1 = plt.subplot(1, 2, 1)
    ax1.plot_date(df[(df.token_in == first_token)].timestamp, df[(df.token_in == first_token)].first_to_second_price, 
                linestyle='solid', marker=None)
    ax1.set_xlabel("Time")
    ax1.set_ylabel("Amount of " + str(second_token) + " per one " + str(first_token))
    ax1.set_title("Swap price of the " + first_token + " in " + second_token)

    ax2 = plt.subplot(1, 2, 2)
    ax2.plot_date(df[(df.token_in == second_token)].timestamp, df[(df.token_in == second_token)].first_to_second_price, 
                linestyle='solid', marker=None, color='red')
    ax2.set_xlabel("Time")
    ax2.set_ylabel("Amount of " + str(first_token) + " per one " + str(second_token))
    ax2.set_title("Swap price of the " + second_token + " in " + first_token)

    fig.autofmt_xdate()
    fig.subplots_adjust(wspace=wspace, hspace=hspace) 

    plt.show()
    
    
def get_df_with_swap_prices_and_change_rates(df: pd.DataFrame, first_token: str, second_token:str) -> pd.DataFrame:
    """form swaps price and form swaps price change rate for each token independently

    Args:
        df (pd.DataFrame): swaps dataframe
        first_token (str): name of the first token
        second_token (str): name of the second token

    Returns:
        pd.DataFrame: dataframe with formed swaps price and swaps price changes
    """
    df['first_to_second_price'] = df.amount_out / df.amount_in
    df['price_change_rate'] = np.ones(len(df))

    first_token_price_story = df[df.token_in == first_token].first_to_second_price
    second_token_price_story = df[df.token_in == second_token].first_to_second_price
    first_token_price_story = first_token_price_story.shift(periods=1)
    second_token_price_story = second_token_price_story.shift(periods=1)

    first_token_df = df[df.token_in == first_token]
    second_token_df = df[df.token_in == second_token]

    first_token_df.price_change_rate = ((first_token_df.first_to_second_price - first_token_price_story) / 
                                        first_token_price_story) * 100
    second_token_df.price_change_rate = ((second_token_df.first_to_second_price - second_token_price_story) / 
                                        second_token_price_story) * 100

    df = pd.concat([first_token_df, second_token_df])
    df.sort_index(inplace=True)
    
    return df