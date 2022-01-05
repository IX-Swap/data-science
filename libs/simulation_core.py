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
from monte_carlo import Transaction 
from tqdm import tqdm
import plotly.express as px
import matplotlib.pyplot as plt
from scipy import stats
import seaborn as sns


logging.basicConfig(level=logging.WARN, format='%(asctime)s:%(name)s:%(message)s', 
                    datefmt="%m/%d/%Y %I:%M:%S %p")
logger = logging.getLogger(__name__)

"""
    RUNS SIMULATIONS FOR POOL X_Y BASED ON HISTORICAL TRANSACTIONS WITH VOLATILITY MITIGATION 
MECHANISM ENABLED / DISABLED
"""

# EXPERIMENT_ID = 84
# X_NAME = 'MAMZN'
# Y_NAME = 'UST'
# X_INDEX = '0'
# Y_INDEX = '1'

class Simulation:
    def __init__(self, experiment_id: int, x_name: str, y_name: str, window_size: int, base_dir: str, 
                 x_index: str='0', y_index: str='1'):
        """Initialize new simulation entity with predefined settings and parameters

        Args:
            experiment_id (int): ID of the experiment
            x_name (str): name of the X-axis (first token name)
            y_name (str): name of the Y-axis (second token name)
            window_size (int): window size for mitigation
            base_dir (str): base directory of the project
            x_index (str, optional): index of the X-axis. Defaults to '0'.
            y_index (str, optional): index of the Y-axis. Defaults to '1'.
        """
        self.x_name = x_name
        self.y_name = y_name
        self.window_size = window_size
        self.base_dir = base_dir + str(experiment_id)
        self.iteration = 0
        self.granularity = self.window_size
        self.experiment_id = experiment_id
        self.x_index = x_index
        self.y_index = y_index


    def run_simulation(self, isBurnAvailable: bool, isMintAvailable: bool): 
        """Run simulation over the given swaps, mints and burns and save all of them into csv files of specific names
        
        Args:
            isBurnAvailable (bool): is there burn history
            isMintAvailable (bool): is there mint history
        """
        swaps_path = fr'{os.getcwd()}\data\pair_history\{self.x_name}_{self.y_name}\{self.x_name.lower()}_{self.y_name.lower()}_swaps.pkl'
        mints_path = fr'{os.getcwd()}\data\pair_history\{self.x_name}_{self.y_name}\{self.x_name.lower()}_{self.y_name.lower()}_mints.pkl'
        burns_path = fr'{os.getcwd()}\data\pair_history\{self.x_name}_{self.y_name}\{self.x_name.lower()}_{self.y_name.lower()}_burns.pkl'

        swaps_df = pd.read_pickle(swaps_path)
        mints_df = pd.DataFrame()
        burns_df = pd.DataFrame()
        if isMintAvailable:
            mints_df = pd.read_pickle(mints_path)
            mints_df['type'] = 'MINT'
        if isBurnAvailable:
            burns_df = pd.read_pickle(burns_path)
            burns_df['type'] = 'BURN'
            burns_df = burns_df[~burns_df.isnull().any(axis=1)]

        swaps_df['type'] = 'SWAP'

        swaps_df, mints_df, burns_df = self.expand_all_transactions_history(swaps_df, mints_df, burns_df)
        transactions_df = pd.concat([swaps_df, mints_df, burns_df])

        transactions_df.sort_values('timestamp', inplace=True)

        base_experiment_path = fr'{os.getcwd()}/data/real_transactions/experiment_{self.experiment_id}'
        os.makedirs(base_experiment_path)
        
        with open(f'{base_experiment_path}/config.txt', 'w') as f:
            f.write(base_experiment_path)

        for vm in [False, True]:
            os.makedirs(f'{base_experiment_path}/{self.iteration}')

            amm.reset(self.x_name, self.y_name, int(0), int(0), vm, 
                      self.window_size * 60 * 60, 
                      self.window_size * 60 * 60 // self.granularity, 
                      self.granularity)

            cnt = 0 
            
            for index, row in tqdm(transactions_df.iterrows()):
                blockchain.update(row['timestamp'].second)
                if row['type'] == 'SWAP':
                    amm.swap(cnt, Transaction(row['timestamp'], int(row['amount_in']), row['token_in'], row['token_out'], 100, row['txd'], row['sender'], row['to']))
                elif row['type'] == 'MINT':
                    amm.mint(int(row[f'amount{self.x_index}']), int(row[f'amount{self.y_index}']), row['timestamp'], cnt)
                elif row['type'] == 'BURN':
                    amm.burn(int(row[f'amount{self.x_index}']), int(row[f'amount{self.y_index}']), row['timestamp'], cnt)
                cnt += 1


            SwapTransaction.save_all(f'{base_experiment_path}/{self.iteration}/swaps.csv')
            MintTransaction.save_all(f'{base_experiment_path}/{self.iteration}/mints.csv')
            BurnTransaction.save_all(f'{base_experiment_path}/{self.iteration}/burns.csv')
            blockchain.reset_state()
            
            amm.export_pool_states_to_csv(f'{base_experiment_path}/{self.iteration}/pool_before_transaction.csv', 
                                            f'{base_experiment_path}/{self.iteration}/pool_after_transaction.csv')

            logger.info("Start normalizing...")
            self.normalize_csv(f'{base_experiment_path}/{self.iteration}/swaps.csv', 
                               ['token_in_amount', 'token_out_amount', 'token_out_amount_min', 'system_fee', 'oracle_amount_out'], 
                               f'{base_experiment_path}/{self.iteration}/swaps_normalized.csv')
            self.normalize_csv(f'{base_experiment_path}/{self.iteration}/mints.csv', 
                               ['X_amount', 'Y_amount'], 
                               f'{base_experiment_path}/{self.iteration}/mints_normalized.csv')
            self.normalize_csv(f'{base_experiment_path}/{self.iteration}/burns.csv', 
                               ['X_amount', 'Y_amount'], 
                               f'{base_experiment_path}/{self.iteration}/burns_normalized.csv')

            self.normalize_pool_state(f'{base_experiment_path}/{self.iteration}/pool_before_transaction.csv', 
                                      f'{base_experiment_path}/{self.iteration}/pool_before_transaction_normalized.csv')
            self.normalize_pool_state(f'{base_experiment_path}/{self.iteration}/pool_after_transaction.csv', 
                                      f'{base_experiment_path}/{self.iteration}/pool_after_transaction_normalized.csv')
            logging.info("Finished normalizing")

            self.iteration += 1


    def expand_all_transactions_history(self, swaps_df: pd.DataFrame, mints_df: pd.DataFrame, burns_df: pd.DataFrame):
        """Expand all values of the transaction history to 18 decimals and return changed
        Pandas DataFrames

        Args:
            swaps_df (pd.DataFrame): swap-operations history DataFrame
            mints_df (pd.DataFrame): mint-operations history DataFrame
            burns_df (pd.DataFrame): burn-operations history DataFrame

        Returns:
            3 Pandas DataFrames: swaps, mints and burns histories DataFrames
        """
        swaps_df['amount_in'] = swaps_df['amount_in'].apply(expand_to_18_decimals_object)
        swaps_df['amount_out'] = swaps_df['amount_out'].apply(expand_to_18_decimals_object)
        
        if not mints_df.empty:
            mints_df[f'amount{self.x_index}'] = mints_df[f'amount{self.x_index}'].apply(expand_to_18_decimals_object)
            mints_df[f'amount{self.y_index}'] = mints_df[f'amount{self.y_index}'].apply(expand_to_18_decimals_object)

        if not burns_df.empty:
            burns_df[f'amount{self.x_index}'] = burns_df[f'amount{self.x_index}'].apply(expand_to_18_decimals_object)
            burns_df[f'amount{self.y_index}'] = burns_df[f'amount{self.y_index}'].apply(expand_to_18_decimals_object)

        return swaps_df, mints_df, burns_df



    def normalize_csv(self, filename, cols_to_normalize, normalized_filename):
        """transform CSV witn 18 decimals numbers back to floats and save into new csv

        Args:
            filename (str): name of file which is required to change
            cols_to_normalize (list of str): what columns require transformation
            normalized_filename (str): name for new generated file where changed data will
                                        be saved
        """
        df = pd.read_csv(filename)

        for col in cols_to_normalize:
            df[col] = df[col].apply(contract_18_decimals_to_float)
        
        df.to_csv(normalized_filename, index=False)


    def normalize_pool_state(self, pool_state_filename, normalized_filename):
        """change data type of the pool state DataFrame from contract 18 decimals to float

        Args:
            pool_state_filename (str): name of file covering current pool state
            normalized_filename ([type]): name of file with changed current pool state
        """
        pool_state_df = pd.read_csv(pool_state_filename)

        pool_state_df['reserve_X'] = pool_state_df['reserve_X'].apply(contract_18_decimals_to_float)
        pool_state_df['reserve_Y'] = pool_state_df['reserve_Y'].apply(contract_18_decimals_to_float)
        pool_state_df['k'] = pool_state_df['k'].apply(contract_18_decimals_to_float)
        pool_state_df['k'] = pool_state_df['k'].apply(contract_18_decimals_to_float) # second time!!!
        pool_state_df['price_X_cumulative'] = pool_state_df['price_X_cumulative'].apply(int).apply(q_decode_144)
        pool_state_df['price_Y_cumulative'] = pool_state_df['price_Y_cumulative'].apply(int).apply(q_decode_144)

        pool_state_df.to_csv(normalized_filename, index=False)
        
        
    def read_simulation(self, sim_id: int):
        """Read simulation from csv's setting simulation ID to 0 in case without Mitigation and
        setting ID to 1 with Mitigation (requires preset base_dir and x/y tokens names)

        Args:
            sim_id (int): simulation ID, where 1 - with Mitigaction and 0 - without

        Returns:
            3 Pandas DataFrames: Pandas DataFrames of swaps, mints and burns
        """
        # set paths
        pool_state_before_transactions_path = fr'{self.base_dir}\{sim_id}\pool_before_transaction_normalized.csv'
        pool_state_after_transactions_path = fr'{self.base_dir}\{sim_id}\pool_after_transaction_normalized.csv'
        swap_transactions_path = fr'{self.base_dir}\{sim_id}\swaps_normalized.csv'
        mint_transactions_path = fr'{self.base_dir}\{sim_id}\mints_normalized.csv'
        burn_transactions_path = fr'{self.base_dir}\{sim_id}\burns_normalized.csv'
        
        # read swaps
        pool0_df = pd.read_csv(pool_state_before_transactions_path)
        pool1_df = pd.read_csv(pool_state_after_transactions_path)
        swaps_df = pd.read_csv(swap_transactions_path)
        
        # form columns, separating old ones without mitigation and forming new ones with mitigation
        pool0_df.columns = pool0_df.columns.map(lambda x : x + '_before' if x != 'transaction_id' else x)

        # perform dataframes concatenation
        swaps_df = pd.merge(swaps_df, pool0_df, left_on='id', right_on='transaction_id')
        swaps_df = pd.merge(swaps_df, pool1_df, left_on='transaction_id', right_on='transaction_id')
        
        # extract transaction and block timestamps
        swaps_df['transaction_timestamp'] = pd.to_datetime(swaps_df.transaction_timestamp, unit='s')
        swaps_df['block_timestamp'] = pd.to_datetime(swaps_df.block_timestamp, unit='s')
        
        # form x token price
        swaps_df.loc[:, 'X_price'] = swaps_df['reserve_Y'] / swaps_df['reserve_X']
        
        # price impact of swap / 100%
        swaps_df.loc[:, 'price_diff'] = (swaps_df['reserve_Y'] / swaps_df['reserve_X'] - swaps_df['reserve_Y_before'] / swaps_df['reserve_X_before']) / (
                                                        swaps_df['reserve_Y_before'] / swaps_df['reserve_X_before'])
        
        # read mints
        mints_df = pd.read_csv(mint_transactions_path)
        mints_df = pd.merge(mints_df, pool0_df, left_on='id', right_on='transaction_id')
        mints_df = pd.merge(mints_df, pool1_df, left_on='transaction_id', right_on='transaction_id')
        
        # read burns
        burns_df = pd.read_csv(burn_transactions_path)
        burns_df = pd.merge(burns_df, pool0_df, left_on='id', right_on='transaction_id')
        burns_df = pd.merge(burns_df, pool1_df, left_on='transaction_id', right_on='transaction_id') 
        
        return swaps_df, mints_df, burns_df
    

    def show_mitigation_comparison(self, pure_df: pd.DataFrame, mitigated_df: pd.DataFrame):
        """show comparison of blocked and passed transactions, TWAP availability ratio, TWAP statuses obtained during mitigation

        Args:
            pure_df (pd.DataFrame): simple transaction history
            mitigated_df (pd.DataFrame): transaction history with mitigation regulation
        """
        print(f"Original {self.x_name}/{self.y_name} pool has next statuses counts:")
        print(pure_df.status.value_counts())
        
        print(f"Mitigated {self.x_name}/{self.y_name} dataframe has next statuses counts:")
        print(mitigated_df.status.value_counts())
        
        print(f"TWAP unavailability ratio for {self.x_name}/{self.y_name} is {mitigated_df[mitigated_df.mitigator_check_status == 'CANT_CONSULT_ORACLE'].shape[0]/mitigated_df.shape[0]}")
        
        print(f"Mitigated {self.x_name}/{self.y_name} dataframe has next Mitigator statuses:")
        print(mitigated_df.mitigator_check_status.value_counts())
        
        
    def plot_hist_blocked_transactions_slice(self, mitigated_df: pd.DataFrame):
        """Plot a histogram of slice factors for blocked transactions

        Args:
            mitigated_df (pd.DataFrame): mitigated dataframe
        """
        ax = mitigated_df[mitigated_df.status=='BLOCKED_BY_VOLATILITY_MITIGATION'].slice_factor.hist()
        ax.set_title(f'Slice Factor Histogram for {self.x_name}/{self.y_name} pool (blocked transactions)')
        plt.show()
        
        
    def plot_hist_blocked_trannsactions_slice_curve(self, mitigated_df: pd.DataFrame):
        """Plot a histogram of slice factor curve for blocked transactions

        Args:
            mitigated_df (pd.DataFrame): mitigated dataframe
        """
        ax = mitigated_df[mitigated_df.status=='BLOCKED_BY_VOLATILITY_MITIGATION'].slice_factor_curve.hist()
        ax.set_title(f'Slice Factor Curve Histogram for {self.x_name}/{self.y_name} pool (blocked transactions)')
        plt.show()
        
        
    def px_hist_blocked_transactions_slice(self, mitigated_df: pd.DataFrame, width: int=900, height: int=500):
        """Plot in plotly.express a histogram of slice factor distribution for blocked transactions

        Args:
            mitigated_df (pd.DataFrame): swaps dataframe with performed mitigation
            width (int, optional): width of final figure. Defaults to 900.
            height (int, optional): height of final figure. Defaults to 500.
        """
        fig = px.histogram(mitigated_df, x="slice_factor", color="status",
                  title=f'Slice factor distribution for {self.x_name}/{self.y_name} pool (split by transaction status)', 
                  width=width, height=height).update_xaxes(categoryorder='total descending')
        fig.show()
        
        
    def px_hist_blocked_transactions_difference_from_oracle(self, mitigated_df: pd.DataFrame, 
                                                            width: int=900, height: int=500):
        """[summary]

        Args:
            mitigated_df (pd.DataFrame): mitigated dataframe
            width (int, optional): width of final figure. Defaults to 900.
            height (int, optional): height of final figure. Defaults to 500.
        """
        fig = px.histogram(mitigated_df[mitigated_df.slice_factor > 1], x="out_amount_diff", color="status",
                  title=f'Percentage difference of amount_out with oracle based amount_out for {self.x_name}/{self.y_name} pool, histogram', 
                  width=width, height=height).update_xaxes(categoryorder='total descending')
        fig.show()
        
        
    def plot_slice_distribution_and_diff_limit_line(self, mitigated_df: pd.DataFrame):
        """plotting slice factor distribution of the mitigated dataframe and limit line for separating passed and
        blocked transactions

        Args:
            mitigated_df (pd.DataFrame): mitigated dataframe
        """
        fig, ax = plt.subplots(figsize=(15, 8))
        sns.scatterplot(data=mitigated_df[mitigated_df.mitigator_check_status == 'CHECKED'], x='slice_factor', 
                        y='out_amount_diff', hue='status')

        slice_factor = np.arange(0, 100)
        slice_factor_curve = slice_factor * np.sqrt(slice_factor).astype(int)
        slice_factor_curve[slice_factor_curve > 98] = 98
        
        out_amount_diff = (100 - slice_factor_curve)
        
        sns.lineplot(x=slice_factor, y=out_amount_diff, color='red', label='out_amount_diff_limit')
        ax.set_title(f'Swaps slice_factor/out_amount_diff scatterplot for {self.x_name}/{self.y_name} pool (split by status)')
        plt.grid(True, color='black', linestyle='--', linewidth=0.5)
        plt.show()
        
        
    def plot_reserves_with_and_without_mitigation(self, pure_df: pd.DataFrame, mitigated_df: pd.DataFrame):
        """plot reserves distribution without mitigation from the left and with from the right

        Args:
            pure_df (pd.DataFrame): original history
            mitigated_df (pd.DataFrame): mitigated dataframe
        """
        fig, ax = plt.subplots(1, 2,figsize=(15, 5))
        ax2 = ax[0].twinx()

        ax[0].plot(pure_df.transaction_timestamp, pure_df.reserve_X, label=f'reserve_X ({self.x_name})')
        ax2.plot(pure_df.transaction_timestamp, pure_df.reserve_Y, label=f'reserve_Y ({self.y_name})', color='orange')

        ax[0].set_xlabel('timestamp')
        ax[0].set_ylabel(self.x_name)
        ax2.set_ylabel(self.y_name)
        ax[0].set_title(f'Reserves for {self.x_name}/{self.y_name} pool (Volatility mitigator off)')
        plt.grid(True, color='black', linestyle='--', linewidth=0.5)

        ax2 = ax[1].twinx()

        ax[1].plot(mitigated_df.transaction_timestamp, mitigated_df.reserve_X)
        ax2.plot(mitigated_df.transaction_timestamp, mitigated_df.reserve_Y, color='orange')

        ax[1].set_xlabel('timestamp')
        ax[1].set_ylabel(self.x_name)
        ax2.set_ylabel(self.y_name)
        ax[1].set_title(f'Reserves for {self.x_name}/{self.y_name} pool (Volatility mitigator on)')

        fig.autofmt_xdate(rotation=25)
        fig.legend()
        fig.tight_layout()
        plt.grid(True, color='black', linestyle='--', linewidth=0.5)
        fig.show()
        
        
    def plot_cumulative_prices_with_and_without_mitigation(self, pure_df: pd.DataFrame, mitigated_df: pd.DataFrame,
                                                           makeBigNumConvert: bool=False):
        """plot cumulative price distribution without mitigation from the left and with from the right

        Args:
            pure_df (pd.DataFrame): [description]
            mitigated_df (pd.DataFrame): [description]
        """
        fig, ax = plt.subplots(1, 2,figsize=(15, 5))
        ax2 = ax[0].twinx()

        ax[0].plot(pure_df.transaction_timestamp, 
                   pure_df.price_X_cumulative if not makeBigNumConvert else pure_df.price_X_cumulative.to_numpy().astype(np.float64), 
                   label=f'reserve_X ({self.x_name})')
        ax2.plot(pure_df.transaction_timestamp, 
                 pure_df.price_Y_cumulative if not makeBigNumConvert else pure_df.price_Y_cumulative.to_numpy().astype(np.float64), 
                 label=f'reserve_Y ({self.y_name})', color='orange')

        ax[0].set_xlabel('time')
        ax[0].set_ylabel(f"{self.x_name} price * seconds")
        ax2.set_ylabel(f"{self.y_name} price * seconds")
        ax[0].set_title(f'Cumulative prices for {self.x_name}/{self.y_name} pool (Volatility mitigator off)')
        plt.grid(True, color='black', linestyle='--', linewidth=0.5)

        ax2 = ax[1].twinx()

        ax[1].plot(mitigated_df.transaction_timestamp, 
                   mitigated_df.price_X_cumulative if not makeBigNumConvert else mitigated_df.price_X_cumulative.to_numpy().astype(np.float64), 
                   label=f'reserve_X ({self.x_name})')
        ax2.plot(mitigated_df.transaction_timestamp, 
                 mitigated_df.price_Y_cumulative if not makeBigNumConvert else mitigated_df.price_Y_cumulative.to_numpy().astype(np.float64), 
                 label=f'reserve_Y ({self.y_name})', color='orange')

        ax[1].set_xlabel('time')
        ax[1].set_ylabel(f"{self.x_name} price * seconds")
        ax2.set_ylabel(f"{self.y_name} price * seconds")
        ax[1].set_title(f'Cumulative prices for {self.x_name}/{self.y_name} pool (Volatility mitigator on)')

        fig.autofmt_xdate(rotation=25)
        fig.legend()
        fig.tight_layout()
        plt.grid(True, color='black', linestyle='--', linewidth=0.5)
        fig.show()
        
    
    def plot_transactions_by_type(self, mitigated_df: pd.DataFrame, ignoreSuccess: bool=False, 
                                  width: int=5, height: int=5, ignoreBlocked: bool=False, 
                                  ignoreNotEnough: bool=False, separatePlots: bool=False):
        if separatePlots:
            fig, ax = plt.subplots(1, 2, figsize=(width, height))
            
            if not ignoreSuccess:
                success_df = mitigated_df[mitigated_df.status == 'SUCCESS']
                ax[0].plot(success_df.transaction_timestamp, success_df.reserve_X - success_df.reserve_X_before, 
                        label=f'transaction {self.x_name} value SUCCESS', color='red')
                ax[1].plot(success_df.transaction_timestamp, success_df.reserve_Y - success_df.reserve_Y_before, 
                        label=f'transaction {self.y_name} value SUCCESS', color='maroon', ls='--')
            
            if not ignoreBlocked:
                blocked_df = mitigated_df[mitigated_df.status == 'BLOCKED_BY_VOLATILITY_MITIGATION']
                ax[0].scatter(blocked_df[blocked_df.token_in == self.x_name].transaction_timestamp, 
                        blocked_df[blocked_df.token_in == self.x_name].token_in_amount, 
                        label=f'transaction {self.x_name} value BLOCKED', color='blue', marker='x')
                ax[1].scatter(blocked_df[blocked_df.token_in == self.y_name].transaction_timestamp, 
                            blocked_df[blocked_df.token_in == self.y_name].token_in_amount, 
                        label=f'transaction {self.y_name} value BLOCKED', color='navy')
            
            if not ignoreNotEnough:
                not_enough_df = mitigated_df[mitigated_df.status == 'NOT_ENOUGH_RESERVES']
                ax[0].scatter(not_enough_df[not_enough_df.token_in == self.x_name].transaction_timestamp, 
                        not_enough_df[not_enough_df.token_in == self.x_name].token_in_amount, 
                        label=f'transaction {self.x_name} value NOT_ENOUGH', color='green', marker='x')
                ax[1].scatter(not_enough_df[not_enough_df.token_in == self.y_name].transaction_timestamp, 
                            not_enough_df[not_enough_df.token_in == self.y_name].token_in_amount, 
                        label=f'transaction {self.y_name} value NOT_ENOUGH', color='darkolivegreen')

            ax[0].set_xlabel('time')
            ax[1].set_xlabel('time')
            ax[0].set_ylabel(f"{self.x_name} value")
            ax[1].set_ylabel(f"{self.y_name} value")
            ax[0].set_title(f'Transaction values for {self.x_name} side of {self.x_name}/{self.y_name} pool respective to statuses (Volatility mitigator on)')
            ax[1].set_title(f'Transaction values for {self.x_name} side of {self.x_name}/{self.y_name} pool respective to statuses (Volatility mitigator on)')
            
            fig.autofmt_xdate(rotation=25)
            fig.legend()
            fig.tight_layout()
            plt.grid(True, color='black', linestyle='--', linewidth=0.5)
            fig.show()
        
        else:
            fig, ax = plt.subplots(figsize=(width, height))
            ax2 = ax.twinx()
            
            if not ignoreSuccess:
                success_df = mitigated_df[mitigated_df.status == 'SUCCESS']
                ax.plot(success_df.transaction_timestamp, success_df.reserve_X - success_df.reserve_X_before, 
                        label=f'transaction {self.x_name} value SUCCESS', color='red')
                ax2.plot(success_df.transaction_timestamp, success_df.reserve_Y - success_df.reserve_Y_before, 
                        label=f'transaction {self.y_name} value SUCCESS', color='maroon', ls='--')
            
            if not ignoreBlocked:
                blocked_df = mitigated_df[mitigated_df.status == 'BLOCKED_BY_VOLATILITY_MITIGATION']
                ax.scatter(blocked_df[blocked_df.token_in == self.x_name].transaction_timestamp, 
                        blocked_df[blocked_df.token_in == self.x_name].token_in_amount, 
                        label=f'transaction {self.x_name} value BLOCKED', color='blue', marker='x')
                ax2.scatter(blocked_df[blocked_df.token_in == self.y_name].transaction_timestamp, 
                            blocked_df[blocked_df.token_in == self.y_name].token_in_amount, 
                        label=f'transaction {self.y_name} value BLOCKED', color='navy')
            
            if not ignoreNotEnough:
                not_enough_df = mitigated_df[mitigated_df.status == 'NOT_ENOUGH_RESERVES']
                ax.scatter(not_enough_df[not_enough_df.token_in == self.x_name].transaction_timestamp, 
                        not_enough_df[not_enough_df.token_in == self.x_name].token_in_amount, 
                        label=f'transaction {self.x_name} value NOT_ENOUGH', color='green', marker='x')
                ax2.scatter(not_enough_df[not_enough_df.token_in == self.y_name].transaction_timestamp, 
                            not_enough_df[not_enough_df.token_in == self.y_name].token_in_amount, 
                        label=f'transaction {self.y_name} value NOT_ENOUGH', color='darkolivegreen')

            ax.set_xlabel('time')
            ax.set_ylabel(f"{self.x_name} value")
            ax2.set_ylabel(f"{self.y_name} value")
            ax.set_title(f'Transaction values for {self.x_name}/{self.y_name} pool respective to statuses (Volatility mitigator on)')
            
            fig.autofmt_xdate(rotation=25)
            fig.legend()
            fig.tight_layout()
            plt.grid(True, color='black', linestyle='--', linewidth=0.5)
            fig.show()