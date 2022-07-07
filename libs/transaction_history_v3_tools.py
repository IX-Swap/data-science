import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
from datetime import datetime, timedelta
from scipy.stats import poisson, truncnorm
from random import randrange
import pandas as pd
from scipy.stats import halfcauchy 

warnings.filterwarnings("ignore", category = UserWarning)

from monte_carlo import CauchyGenerator, PoissonGenerator, NormalGenerator, ParetoGenerator, LognormalGenerator, Transaction, MonteCarloTransactionSimulator, CauchyParameterSearcher, LognormalParameterSearcher



class TransactionHistory:
    """
    Class that will separate transaction history by categories
    """
    def __init__(self):
        self.pool_address = None

        # basic dataframes references
        self.user_in_swap_df = None
        self.user_out_swap_df = None
        self.pool_investments_df = None
        self.pool_extractions_df = None
        self.anomalies_df = None

        # additional dataframes references with moving averages
        self.smaller_avg_in_swap_df = None
        self.bigger_avg_in_swap_df = None
        self.smaller_avg_out_swap_df = None
        self.bigger_avg_out_swap_df = None
        self.smaller_avg_investments_df = None
        self.bigger_avg_investmets_df = None
        self.smaller_avg_exractions_df = None
        self.bigger_avg_extractions_df = None
        self.smaller_avg_anomalies = None
        self.bigger_avg_anomalies = None


    def __contract_address_count__(self, s):
        return (s == self.pool_address).sum()


    def __set_mov_smaller_avg__(self, df: pd.DataFrame, smaller_avg: str) -> pd.DataFrame:
        """
        generate dataframe with smaller cycle of moving average

        Keyword arguments:
        df (pandas.DataFrame) -- table for which moving average should be found
        smaller_avg (str) -- string that defines cycle size to calculate
            moving average
        """
        df_time = df.copy()
        df_time.UnixTimestamp = pd.to_datetime(df_time.UnixTimestamp, unit='s')
        df_time.index = df_time.UnixTimestamp
        return df_time.resample(smaller_avg).mean()

    
    def __set_mov_bigger_avg__(self, df: pd.DataFrame, bigger_avg: str) -> pd.DataFrame:
        """
        generate dataframe with bigger cycle of moving average (resampling)

        Keyword arguments:
        df (pandas.DataFrame) -- table for which moving average should be found
        smaller_avg (str) -- string that defines cycle size to calculate
            moving average
        """
        df_time = df.copy()
        df_time.UnixTimestamp = pd.to_datetime(df_time.UnixTimestamp, unit='s')
        df_time.index = df_time.UnixTimestamp
        return df_time.rolling(bigger_avg).mean()
   
    
    def classify_history(self, transactions_df: pd.DataFrame):
        """
        Separate history in different dataframes conform transaction parameters
        ('swapping in/out', 'investments, extractions' and 'anomalies') that
        can be requested as current class object fields
        
        Keyword arguments:
        transactions_df (pandas.DataFrame) -- table of all transactions
        """
        # find address of the pool - most of the transactions will be related to pool
        self.pool_address = transactions_df['From'].mode()[0]
        
        # create matrix of transactions hashes and counters of in/out pool movements
        group_df = transactions_df.groupby('Txhash').agg({
            'From': self.__contract_address_count__,
            'To': self.__contract_address_count__
        })
        
        # form lists of swapping transactions, investments, extractions, anomalies
        swap_txhash_list = group_df[(group_df['From'] == 1) & (group_df['To'] == 1)].index.values
        investments_list = group_df[group_df['To'] == 2].index.values
        extractions_list = group_df[group_df['From'] == 2].index.values
        anomalies_list =   group_df[(group_df['From'] > 2) | (group_df['To'] > 2)].index.values

        # record swapping in/out operations
        self.user_in_swap_df = transactions_df[(transactions_df['Txhash'].isin(swap_txhash_list)) & 
                                                (transactions_df['To'] == self.pool_address)]
        self.user_out_swap_df = transactions_df[(transactions_df['Txhash'].isin(swap_txhash_list)) & 
                                                (transactions_df['From'] == self.pool_address)]

        # record investments and extractions
        self.pool_investments_df = transactions_df[transactions_df['Txhash'].isin(investments_list)]
        self.pool_extractions_df = transactions_df[transactions_df['Txhash'].isin(extractions_list)]
        
        # record anomalies
        self.anomalies_df = transactions_df[transactions_df['Txhash'].isin(anomalies_list)]


    def form_moving_averages_for_token(self, smaller_average: str, bigger_average: str, target_token: str):
        """
        calculate tables with moving averages for given token and append those tables to object fields

        Keyword argument:
        smaller_average (str) -- string formatted smaller cycle to find moving average
        bigger_average (str) -- string formatted bigger cycle to find moving average
        target_token (str) -- token name for which moving average should be calculated
        """
        self.smaller_avg_in_swap_df = self.__set_mov_smaller_avg__(
            self.user_in_swap_df[self.user_in_swap_df['TokenSymbol'] == target_token], smaller_average)
        self.bigger_avg_in_swap_df = self.__set_mov_bigger_avg__(
            self.user_in_swap_df[self.user_in_swap_df['TokenSymbol'] == target_token], bigger_average)
        
        self.smaller_avg_out_swap_df = self.__set_mov_smaller_avg__(
            self.user_out_swap_df[self.user_out_swap_df['TokenSymbol'] == target_token], smaller_average)
        self.bigger_avg_out_swap_df = self.__set_mov_bigger_avg__(
            self.user_out_swap_df[self.user_out_swap_df['TokenSymbol'] == target_token], bigger_average)
        
        self.smaller_avg_investments_df = self.__set_mov_smaller_avg__(
            self.pool_investments_df[self.pool_investments_df['TokenSymbol'] == target_token], smaller_average)
        self.bigger_avg_investmets_df = self.__set_mov_bigger_avg__(
            self.pool_investments_df[self.pool_investments_df['TokenSymbol'] == target_token], bigger_average)
        
        self.smaller_avg_exractions_df = self.__set_mov_smaller_avg__(
            self.pool_extractions_df[self.pool_extractions_df['TokenSymbol'] == target_token], smaller_average)
        self.bigger_avg_extractions_df = self.__set_mov_bigger_avg__(
            self.pool_extractions_df[self.pool_extractions_df['TokenSymbol'] == target_token], bigger_average)
        
        self.smaller_avg_anomalies = self.__set_mov_smaller_avg__(
            self.anomalies_df[self.anomalies_df['TokenSymbol'] == target_token], smaller_average)
        self.bigger_avg_anomalies = self.__set_mov_bigger_avg__(
            self.anomalies_df[self.anomalies_df['TokenSymbol'] == target_token], bigger_average)


    def lineplots_matrix(self, x_size: int, y_size: int, hspace:int, wspace: int, period_name: str):
        """
        make lineplots matrix

        Keyword arguments:
        x_size (int) -- matrix width
        y_size (int) -- matrix height
        hspace (int) -- inter-elements height
        wspace (int) -- inter-elements width
        period_name (str) -- name of analyzed time period
        """
        # get tokens present in dataframe
        tokens = self.user_in_swap_df['TokenSymbol'].unique()
        print(tokens)
        plt.figure(figsize=(x_size, y_size))

        # first currency graphs
        plt.subplot(5, 2, 1)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.user_in_swap_df[self.user_in_swap_df['TokenSymbol'] == tokens[0]], 
                    x='Datetime', y='Value', color='red').set_title(tokens[0] + ' swapping in (' + period_name + ')')
        plt.subplot(5, 2, 2)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.user_out_swap_df[self.user_out_swap_df['TokenSymbol'] == tokens[0]], 
                    x='Datetime', y='Value', color='green').set_title(tokens[0] + ' swapping out (' + period_name + ')')

        # second currency graphs
        plt.subplot(5, 2, 3)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.user_in_swap_df[self.user_in_swap_df['TokenSymbol'] == tokens[1]], 
                    x='Datetime', y='Value', color='red').set_title(tokens[1] + ' swapping in (' + period_name + ')')
        plt.subplot(5, 2, 4)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.user_out_swap_df[self.user_out_swap_df['TokenSymbol'] == tokens[1]], 
                    x='Datetime', y='Value', color='green').set_title(tokens[1] + ' swapping out (' + period_name + ')')


        plt.subplot(5, 2, 5)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.pool_investments_df[self.pool_investments_df['TokenSymbol'] == tokens[0]],
                    x='Datetime', y='Value', color='orange').set_title(tokens[0] + ' investments (' + period_name + ')')
        plt.subplot(5, 2, 6)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.pool_investments_df[self.pool_investments_df['TokenSymbol'] == tokens[1]],
                    x='Datetime', y='Value', color='magenta').set_title(tokens[1] + ' investments (' + period_name + ')')

        # extractions
        plt.subplot(5, 2, 7)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.pool_extractions_df[self.pool_extractions_df['TokenSymbol'] == tokens[0]],
                    x='Datetime', y='Value', color='orange').set_title(tokens[0] + ' extractions (' + period_name + ')')
        plt.subplot(5, 2, 8)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.pool_extractions_df[self.pool_extractions_df['TokenSymbol'] == tokens[1]],
                    x='Datetime', y='Value', color='magenta').set_title(tokens[1] + ' extractions (' + period_name + ')')

        # anomalies
        plt.subplot(5, 2, 9)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.anomalies_df[self.anomalies_df['TokenSymbol'] == tokens[0]],
                    x='Datetime', y='Value', color='orange').set_title(tokens[0] + ' anomalies (' + period_name + ')')
        plt.subplot(5, 2, 10)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.anomalies_df[self.anomalies_df['TokenSymbol'] == tokens[1]],
                    x='Datetime', y='Value', color='magenta').set_title(tokens[1] + ' anomalies (' + period_name + ')')

        plt.subplots_adjust(hspace=hspace, wspace=wspace)
        plt.show()


    def histplots_matrix(self, x_size: int, y_size: int, hspace:int, wspace: int, period_name: str, bins_v: int):
        """
        make histplots matrix

        Keyword arguments:
        x_size (int) -- matrix width
        y_size (int) -- matrix height
        hspace (int) -- inter-elements height
        wspace (int) -- inter-elements width
        period_name (str) -- name of analyzed time period
        """
        # get tokens present in dataframe
        tokens = self.user_in_swap_df['TokenSymbol'].unique()
        print(tokens)
        plt.figure(figsize=(x_size, y_size))

        # first currency graphs
        plt.subplot(5, 2, 1)
        plt.xticks(rotation=45)
        sns.histplot(data=self.user_in_swap_df[self.user_in_swap_df['TokenSymbol'] == tokens[0]], 
                    x='Value', color='red', bins=bins_v).set_title(tokens[0] + ' swapping in (' + period_name + ')')
        plt.subplot(5, 2, 2)
        plt.xticks(rotation=45)
        sns.histplot(data=self.user_out_swap_df[self.user_out_swap_df['TokenSymbol'] == tokens[0]], 
                    x='Value', color='green', bins=bins_v).set_title(tokens[0] + ' swapping out (' + period_name + ')')

        # second currency graphs
        plt.subplot(5, 2, 3)
        plt.xticks(rotation=45)
        sns.histplot(data=self.user_in_swap_df[self.user_in_swap_df['TokenSymbol'] == tokens[1]], 
                    x='Value', color='red', bins=bins_v).set_title(tokens[1] + ' swapping in (' + period_name + ')')
        plt.subplot(5, 2, 4)
        plt.xticks(rotation=45)
        sns.histplot(data=self.user_out_swap_df[self.user_out_swap_df['TokenSymbol'] == tokens[1]], 
                    x='Value', color='green', bins=bins_v).set_title(tokens[1] + ' swapping out (' + period_name + ')')


        plt.subplot(5, 2, 5)
        plt.xticks(rotation=45)
        sns.histplot(data=self.pool_investments_df[self.pool_investments_df['TokenSymbol'] == tokens[0]],
                    x='Value', color='orange', bins=bins_v).set_title(tokens[0] + ' investments (' + period_name + ')')
        plt.subplot(5, 2, 6)
        plt.xticks(rotation=45)
        sns.histplot(data=self.pool_investments_df[self.pool_investments_df['TokenSymbol'] == tokens[1]],
                    x='Value', color='magenta', bins=bins_v).set_title(tokens[1] + ' investments (' + period_name + ')')

        # extractions
        plt.subplot(5, 2, 7)
        plt.xticks(rotation=45)
        sns.histplot(data=self.pool_extractions_df[self.pool_extractions_df['TokenSymbol'] == tokens[0]],
                    x='Value', color='orange', bins=bins_v).set_title(tokens[0] + ' extractions (' + period_name + ')')
        plt.subplot(5, 2, 8)
        plt.xticks(rotation=45)
        sns.histplot(data=self.pool_extractions_df[self.pool_extractions_df['TokenSymbol'] == tokens[1]],
                    x='Value', color='magenta', bins=bins_v).set_title(tokens[1] + ' extractions (' + period_name + ')')

        # anomalies
        plt.subplot(5, 2, 9)
        plt.xticks(rotation=45)
        sns.histplot(data=self.anomalies_df[self.anomalies_df['TokenSymbol'] == tokens[0]],
                    x='Value', color='orange', bins=bins_v).set_title(tokens[0] + ' anomalies (' + period_name + ')')
        plt.subplot(5, 2, 10)
        plt.xticks(rotation=45)
        sns.histplot(data=self.anomalies_df[self.anomalies_df['TokenSymbol'] == tokens[1]],
                    x='Value', color='magenta', bins=bins_v).set_title(tokens[1] + ' anomalies (' + period_name + ')')

        plt.subplots_adjust(hspace=hspace, wspace=wspace)
        plt.show()


    def show_transactions_frequencies_per_minute(self):
        tokens = self.user_in_swap_df.TokenSymbol.unique()

        print("Swapping in " + tokens[0] + " transactions frequency: " + str(
            len(self.user_in_swap_df[self.user_in_swap_df.TokenSymbol == tokens[0]].Txhash.unique()) /
            ((self.user_in_swap_df.Datetime.max() - self.user_in_swap_df.Datetime.min()).total_seconds() 
            // 60)
        ))
        print("Swapping in " + tokens[1] + " transactions frequency: " + str(
            len(self.user_in_swap_df[self.user_in_swap_df.TokenSymbol == tokens[1]].Txhash.unique()) /
            ((self.user_in_swap_df.Datetime.max() - self.user_in_swap_df.Datetime.min()).total_seconds() 
            // 60)
        ))
        print("Swapping out transactions frequency: " + str(
            len(self.user_out_swap_df.Txhash.unique()) /
            ((self.user_out_swap_df.Datetime.max() - self.user_out_swap_df.Datetime.min()).total_seconds() 
            // 60)
        ))
        print("Investitions frequency: " + str(
            len(self.pool_investments_df.Txhash.unique()) /
            ((self.pool_investments_df.Datetime.max() - self.pool_investments_df.Datetime.min()).total_seconds() 
            // 60)
        ))
        print("Extractions frequency: " + str(
            len(self.pool_extractions_df.Txhash.unique()) /
            ((self.pool_extractions_df.Datetime.max() - self.pool_extractions_df.Datetime.min()).total_seconds() 
            // 60)
        ))


    def show_min_max_values_by_token(self):
        for token in self.user_in_swap_df['TokenSymbol'].unique():
            print("swapping in " + token + " min = " + str(self.user_in_swap_df[self.user_in_swap_df.TokenSymbol == token].Value.min()))
            print("swapping in " + token + " max = " + str(self.user_in_swap_df[self.user_in_swap_df.TokenSymbol == token].Value.max()))
            print("swapping out " + token + " min = " + str(self.user_out_swap_df[self.user_out_swap_df.TokenSymbol == token].Value.min()))
            print("swapping out " + token + " max = " + str(self.user_out_swap_df[self.user_out_swap_df.TokenSymbol == token].Value.max()))


    def lineplots_moving_averages_matrix_by_token(self, x_size: int, y_size: int, hspace: int, wspace: int,
                                first_token: str, second_token: str, 
                                period_name: str, smaller_avg: str, bigger_avg: str):
        """
        create lineplots matrix that shows moving averages for pool tokens

        Keyword arguments:
        x_size (int) -- width of lineplots matrix
        y_size (int) -- height of lineplots matrix
        hspace (int) -- height space between matrix subplots
        wspace (int) -- width space between matrix subplots
        first_token (str) -- name of left side token
        second_token (str) -- name of right side token
        period_name (str) -- string that defines time period of transactions
        smaller_avg (str) -- time cycle for finding small moving averages
        bigger_avg (str) -- time cycle for finding bigger moving averages
        """
        
        plt.figure(figsize=(x_size, y_size))

        # -----------------------------         first_token section     -----------------------------------
        self.form_moving_averages_for_token(smaller_avg, bigger_avg, first_token)

        plt.subplot(5, 2, 1)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.smaller_avg_in_swap_df, x='UnixTimestamp', y='Value', color='red'
                    ).set_title(first_token + ' swap in moving average (' + period_name + '), green - ' + 
                                bigger_avg + ' avg, red - ' + smaller_avg + ' avg')
        plt.subplot(5, 2, 1)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.bigger_avg_in_swap_df, x='UnixTimestamp', y='Value', color='green'
                    ).set_title(first_token + ' swap in moving average (' + period_name + '), green - ' + 
                                bigger_avg + ' avg, red - ' + smaller_avg + ' avg')

        plt.subplot(5, 2, 3)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.smaller_avg_out_swap_df, x='UnixTimestamp', y='Value', color='red'
                    ).set_title(first_token + ' swap out moving average (' + period_name + '), green - ' + 
                                bigger_avg + ' avg, red - ' + smaller_avg + ' avg')
        plt.subplot(5, 2, 3)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.bigger_avg_out_swap_df, x='UnixTimestamp', y='Value', color='green'
                    ).set_title(first_token + ' swap out moving average (' + period_name + '), green - ' + 
                                bigger_avg + ' avg, red - ' + smaller_avg + ' avg')

        plt.subplot(5, 2, 5)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.smaller_avg_investments_df, x='UnixTimestamp', y='Value', color='red'
                    ).set_title(first_token + ' investments moving average (' + period_name + '), green - ' + 
                                bigger_avg + ' avg, red - ' + smaller_avg + ' avg')
        plt.subplot(5, 2, 5)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.bigger_avg_investmets_df, x='UnixTimestamp', y='Value', color='green'
                    ).set_title(first_token + ' investments moving average (' + period_name + '), green - ' + 
                                bigger_avg + ' avg, red - ' + smaller_avg + ' avg')

        plt.subplot(5, 2, 7)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.smaller_avg_exractions_df, x='UnixTimestamp', y='Value', color='red'
                    ).set_title(first_token + ' extractions moving average (' + period_name + '), green - ' + 
                                bigger_avg + ' avg, red - ' + smaller_avg + ' avg')
        plt.subplot(5, 2, 7)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.bigger_avg_extractions_df, x='UnixTimestamp', y='Value', color='green'
                    ).set_title(first_token + ' extractions moving average (' + period_name + '), green - ' + 
                                bigger_avg + ' avg, red - ' + smaller_avg + ' avg')

        plt.subplot(5, 2, 9)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.smaller_avg_anomalies, x='UnixTimestamp', y='Value', color='red'
                    ).set_title(first_token + ' anomalies moving average (' + period_name + '), green - ' + 
                                bigger_avg + ' avg, red - ' + smaller_avg + ' avg')
        plt.subplot(5, 2, 9)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.bigger_avg_anomalies, x='UnixTimestamp', y='Value', color='green'
                    ).set_title(first_token + ' anomalies moving average (' + period_name + '), green - ' + 
                                bigger_avg + ' avg, red - ' + smaller_avg + ' avg')

        # -----------------------------         second_token section     -------------------------------------
        self.form_moving_averages_for_token(smaller_avg, bigger_avg, second_token)

        plt.subplot(5, 2, 2)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.smaller_avg_in_swap_df, x='UnixTimestamp', y='Value', color='orange'
                    ).set_title(second_token + ' swap in moving average (' + period_name + '), magenta - ' + 
                                bigger_avg + ' avg, orange - ' + smaller_avg + ' avg')
        plt.subplot(5, 2, 2)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.bigger_avg_in_swap_df, x='UnixTimestamp', y='Value', color='magenta'
                    ).set_title(second_token + ' swap in moving average (' + period_name + '), magenta - ' + 
                                bigger_avg + ' avg, orange - ' + smaller_avg + ' avg')

        plt.subplot(5, 2, 4)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.smaller_avg_out_swap_df, x='UnixTimestamp', y='Value', color='orange'
                    ).set_title(second_token + ' swap out moving average (' + period_name + '), magenta - ' + 
                                bigger_avg + ' avg, orange - ' + smaller_avg + ' avg')
        plt.subplot(5, 2, 4)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.bigger_avg_out_swap_df, x='UnixTimestamp', y='Value', color='magenta'
                    ).set_title(second_token + ' swap out moving average (' + period_name + '), magenta - ' + 
                                bigger_avg + ' avg, orange - ' + smaller_avg + ' avg')

        plt.subplot(5, 2, 6)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.smaller_avg_investments_df, x='UnixTimestamp', y='Value', color='orange'
                    ).set_title(second_token + ' investments moving average (' + period_name + '), magenta - ' + 
                                bigger_avg + ' avg, orange - ' + smaller_avg + ' avg')
        plt.subplot(5, 2, 6)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.bigger_avg_investmets_df, x='UnixTimestamp', y='Value', color='magenta'
                    ).set_title(second_token + ' investments moving average (' + period_name + '), magenta - ' + 
                                bigger_avg + ' avg, orange - ' + smaller_avg + ' avg')

        plt.subplot(5, 2, 8)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.smaller_avg_exractions_df, x='UnixTimestamp', y='Value', color='orange'
                    ).set_title(second_token + ' extractions moving average (' + period_name + '), magenta - ' + 
                                bigger_avg + ' avg, orange - ' + smaller_avg + ' avg')
        plt.subplot(5, 2, 8)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.bigger_avg_extractions_df, x='UnixTimestamp', y='Value', color='magenta'
                    ).set_title(second_token + ' extractions moving average (' + period_name + '), magenta - ' + 
                                bigger_avg + ' avg, orange - ' + smaller_avg + ' avg')

        plt.subplot(5, 2, 10)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.smaller_avg_anomalies, x='UnixTimestamp', y='Value', color='orange'
                    ).set_title(second_token + ' anomalies moving average (' + period_name + '), magenta - ' + 
                                bigger_avg + ' avg, orange - ' + smaller_avg + ' avg')
        plt.subplot(5, 2, 10)
        plt.xticks(rotation=45)
        sns.lineplot(data=self.bigger_avg_anomalies, x='UnixTimestamp', y='Value', color='magenta'
                    ).set_title(second_token + ' anomalies moving average (' + period_name + '), magenta - ' + 
                                bigger_avg + ' avg, orange - ' + smaller_avg + ' avg')

        plt.subplots_adjust(hspace=hspace, wspace=wspace)
        plt.show()