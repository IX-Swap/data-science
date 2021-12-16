import random
import numpy as np
import matplotlib.pyplot as plt
import math
from datetime import datetime, timedelta
from scipy.stats import poisson, truncnorm
from random import randrange
import pandas as pd
from scipy.stats import halfcauchy 
import seaborn as sns
import warnings
warnings.filterwarnings("ignore",category=UserWarning)


class PoissonGenerator:
    """
    Generate transactions timestamps list. Current version works with milliseconds.
    """
    
    def __init__(self, cycle_size: int, mean_occurencies: float):
        """
        Create a Poisson generator
        
        Keyword_arguments:
        cycle_size (int) -- reviewable cycle size in milliseconds
        mean_occurencies (float) -- mean amount of transactions
            happening in given cycle size
        """
        self.cycle_size = cycle_size
        self.mean_occurencies = mean_occurencies
        
        
    def __generate_poisson_outcome__(self) -> int:
        """
        Generate how many transactions will happen, considering cycle size 
        and mean transaction amount
        """
        return np.random.poisson(self.mean_occurencies, 1)[0]
    
    
    def generate_transactions(self, current_timestamp: datetime) -> list:
        """
        Generate array of transactions timestamps, considering Poisson distribution and
        random distribution of timestamps in given cycle size
        
        Keyword_arguments:
        current_timestamp (datetime) -- reviewable cycle starting point
        """
        transactions_timestamps = []
        current_transaction_count = self.__generate_poisson_outcome__()
        
        for i in range(current_transaction_count):
            transactions_timestamps.append(current_timestamp + timedelta(milliseconds=randrange(self.cycle_size)))
        
        return transactions_timestamps



class CauchyGenerator:
    """
    Generate transaction values conform Cauchy distribution
    """
    def __init__(self, loc: float, scale: float, limit: int):
        """
        Create Cauchy generator with initial parameters
        
        Keyword_arguments:
        loc (float) -- locational parameter that defines where distribution
            will be centered
        scale (float) -- how far will tales (distribution) go
        """
        self.loc = loc
        self.scale = scale
        self.limit = limit
      
    
    def reset_params(self, loc: float, scale: float, limit: int):
        """
        Change mean and standard deviation parameters of existing generator
        
        Keyword_arguments:
        loc (float) -- locational parameter that defines where distribution
            will be centered
        scale (float) -- how far will tales (distribution) go
        """
        self.loc = loc
        self.scale = scale
        self.limit = limit
        
    
    def generate_transactions(self, transactions_count: int) -> list:
        """
        Generate transaction prices list considering mu and sigma
        
        Keyword_arguments:
        transactions_count (int) -- required transactions count
        """
        value = halfcauchy.rvs(size=transactions_count, loc=self.loc, scale=self.scale)
        return value / ((value // self.limit) + 1)



class LognormalGenerator:
    """
    Generate transaction values conform Lognormal distribution
    """
    def __init__(self, mean: float, sigma: float, limit: float):
        """
        Create Log-normal generator with initial parameters
        
        Keyword_arguments:
        mean (float) -- mean distribution value
        sigma (float) -- standard deviation
        limit (float) -- limit of the distribution
        """
        self.mean = mean
        self.sigma = sigma
        self.limit = limit

    
    def reset_params(self, mean: float, sigma: float, limit: float):
        """
        Change log-normal generator parameters
        
        Keyword_arguments:
        mean (float) -- mean distribution value
        sigma (float) -- standard deviation
        limit (float) -- limit of the distribution
        """
        self.mean = mean
        self.sigma = sigma
        self.limit = limit
        
    
    def generate_transactions(self, transactions_count: int) -> list:
        """
        Generate transaction prices list considering mu and sigma
        
        Keyword_arguments:
        transactions_count (int) -- required transactions count
        """
        value = np.random.lognormal(mean=self.mean, sigma=self.sigma, size=transactions_count)
        return value / ((value // self.limit) + 1)

    

class ParetoGenerator:
    """
    Generate transaction values conform Pareto distribution
    """
    def __init__(self, shape: float):
        """
        Create Cauchy generator with initial parameters
        
        Keyword_arguments:
        shape (float) -- shape of distribution
        """
        self.shape = shape
      
    
    def reset_params(self, shape: float):
        """
        Change distribution shape

        Keyword arguments:
        shape (float) -- distribution shape
        """
        self.shape = shape
        
    
    def generate_transactions(self, transactions_count: int) -> list:
        """
        Generate transaction prices list considering params
        
        Keyword_arguments:
        transactions_count (int) -- required transactions count
        """
        return np.random.pareto(self.shape, size=transactions_count)



class NormalGenerator:
    """
    Generate transaction values conform normal distribution
    """
    
    def __init__(self, mu: float, sigma: float, lower_bound: float, upper_bound: float):
        """
        Create a normal distribution generator
        
        Keyword_arguments:
        mu (float) -- mean transaction price
        sigma (float) -- standard deviation of transaction price
        lower_bound (float) -- distribution lower bound
        upper_bound (float) -- distribution upper bound
        """
        if lower_bound > upper_bound:
            raise ValueError("creation: lower bound value can't be bigger than upper bound")
        if mu < lower_bound:
            raise ValueError("creation: mean value (mu) can't be lower than lower bound")
        if mu > upper_bound:
            raise ValueError("creation: mean value (mu) can't be bigger than upper bound")
        
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.mu = mu
        self.sigma = sigma
      
    
    def reset_mean_and_dev(self, mu: float, sigma: float):
        """
        Change mean and standard deviation parameters of existing generator
        
        Keyword_arguments:
        mu (float) -- mean transaction price
        sigma (float) -- standard deviation of transaction price
        """
        if mu < self.lower_bound:
            raise ValueError("editing mu and sigma: mean value (mu) can't be lower than lower bound")
        if mu > self.upper_bound:
            raise ValueError("editing mu and sigma: mean value (mu) can't be bigger than upper bound")
        
        self.mu = mu
        self.sigma = sigma
        
        
    def reset_lower_and_upper_bound(self, lower_bound: float, upper_bound: float):
        """
        Change distribution lower and upper bounds
        
        Keyword arguments:
        lower_bound (float) -- distribution lower bound
        upper_bound (float) -- distribution upper bound
        """
        if lower_bound > upper_bound:
            raise ValueError("bounds editing: lower bound value can't be bigger than upper bound")
        if self.mu < lower_bound:
            raise ValueError("bounds editing: mean value (mu) can't be lower than lower bound")
        if self.mu > upper_bound:
            raise ValueError("bounds editing: mean value (mu) can't be bigger than upper bound")
        
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        
    
    def generate_transactions(self, transactions_count: int) -> list:
        """
        Generate transaction prices list considering mu and sigma
        
        Keyword_arguments:
        transactions_count (int) -- required transactions count
        """
        return truncnorm.rvs((self.lower_bound - self.mu)/self.sigma, 
                            (self.upper_bound - self.mu)/self.sigma, 
                            loc=self.mu, scale=self.sigma, size=transactions_count)



class Transaction:
    """
    Class with information regarding swapping transaction
    """
    def __init__(self, timestamp: datetime, token_in_amount: float, token_in: str, 
                token_out: str, slope: float=0.05):
        self.datetime_timestamp = timestamp
        self.token_in = token_in
        self.token_in_amount = token_in_amount
        self.token_out = token_out
        self.token_out_amount = None
        self.slope = slope


    def set_token_out_amount(self, token_out_amount: float):
        self.token_out_amount = token_out_amount
        
    
    def to_string(self) -> str:
        return str('Transaction {datetime timestamp = ' + str(self.datetime_timestamp) + 
                    ', token in amount = "' + str(self.token_in_amount) + 
                    '", token in name = ' + str(self.token_in) + 
                    ', token out amount = ' + str(self.token_out_amount) + 
                    ', token out name = ' + str(self.token_out) + 
                    ', slope = ' + str(self.slope) + '}')

    
    def to_record(self) -> np.array:
        """
        Transform transaction data into numpy array of data
        """
        return np.array([self.datetime_timestamp, self.token_in, self.token_in_amount,
                        self.token_out, self.token_out_amount, self.slope])

    

class MonteCarloTransactionSimulator:
    """
    Monte Carlo transactions generator, that generates transactions frequency using Poisson 
    distribution and transaction values using normal distribution (time metrics - milliseconds)
    """
    def __init__(
        self, frequency_generator: PoissonGenerator, token_in_generator, first_currency: str, second_currency: str
    ):
        """
        Create a Monte-Carlo transaction simulator
        
        Keyword_arguments:
        frequency_generator (PoissonGenerator) -- Poisson transaction distribution generator
        token_in_generator -- transaction distribution generator (accepts normal, Cauchy and 
            Pareto)
        first_currency -- name of the first token in transaction
        second_currency -- name of the second token in transaction
        """
        self.frequency_generator = frequency_generator
        self.token_in_generator = token_in_generator
        self.first_currency = first_currency
        self.second_currency = second_currency
        self.transaction_history = []
        
    
    def get_token_in_generator(self):
        """
        Get transactions distribution generator (can be normal, Cauchy and Pareto)
        """
        return self.token_in_generator
        
        
    def clear_transaction_history(self):
        """
        Clear all records from transaction history
        """
        self.transaction_history.clear()
    
    
    def generate_transactions(self, current_timestamp: datetime):
        """
        Generates transactions list with timestamps and token_in values. All transactions are recorded
        to the 'transaction_history' variable.
        
        Keyword arguments:
        current_timestamp (datetime) -- initial datetime point from where cycle will be reviewed
        current_amm_coef (float) -- current AMM market coefficient that defines price of out
            token relative to in token
        """
        # generate timestamps and token_in values
        timestamps = self.frequency_generator.generate_transactions(current_timestamp)
        token_in_values = self.token_in_generator.generate_transactions(len(timestamps))
        
        # form new transactions and record them into 'transaction history' variable
        for index in range(len(timestamps)):
            self.transaction_history.append(Transaction(timestamp=timestamps[index], 
                                                        token_in_amount=token_in_values[index], 
                                                        token_in=self.first_currency,
                                                        token_out=self.second_currency))


    def get_history(self) -> list:
        """
        Get transaction history
        """
        return self.transaction_history
            
            
    def transaction_history_to_csv(self, filename: str):
        """
        Write transaction history to specified .csv file
        
        Keyword arguments:
        filename (str) -- name of .csv file where to write data
        """
        # vectorize all transactions into numpy matrix and then make dataframe out of it
        transactions_matrix = np.array([transaction.to_record() for transaction in self.transaction_history])
        transaction_history_df = pd.DataFrame(data=transactions_matrix, columns=['datetime_timestamp', 'TokenIn', 'TokenInAmount', 
                                                                                 'TokenOut', 'TokenOutAmount', 'Slope'])

        # fix transformation of numerical features into string at numpy stage to numerical again
        transaction_history_df['TokenInAmount'] = pd.to_numeric(transaction_history_df['TokenInAmount'])
        transaction_history_df['TokenOutAmount'] = pd.to_numeric(transaction_history_df['TokenOutAmount'])
        
        # either append new records to the existing file, or create a new one from existing table
        try:
            with open(filename) as f:
                transaction_history_df.to_csv(filename, mode='a', header=False)
        except IOError:
            transaction_history_df.to_csv(filename)


    def get_dataframe(self) -> pd.DataFrame:
        # vectorize all transactions into numpy matrix and then make dataframe out of it
        transactions_matrix = np.array([transaction.to_record() for transaction in self.transaction_history])
        transaction_history_df = pd.DataFrame(data=transactions_matrix, columns=['datetime_timestamp', 'TokenIn', 'TokenInAmount', 
                                                                                 'TokenOut', 'TokenOutAmount', 'Slope'])

        # fix transformation of numerical features into string at numpy stage to numerical again
        transaction_history_df['TokenInAmount'] = pd.to_numeric(transaction_history_df['TokenInAmount'])
        transaction_history_df['TokenOutAmount'] = pd.to_numeric(transaction_history_df['TokenOutAmount'])

        return transaction_history_df            
            


class CauchyParameterSearcher:
    """
    Class responsible for performing search of the best 'scale' parameter of the Cauchy generator
    to imitate real-life distribution
    """

    def __init__(self, value_generator: CauchyGenerator, target_df: pd.DataFrame, token_symbol: str):
        """
        create new cauchy parameter searcher

        Keyword arguments:
        value_generator (CauchyGenerator) -- cauchy value generator
        target_df (pandas.DataFrame) -- pandas dataframe that has real-life data
        token_symbol (str) -- choose for which token is required to analyze distribution
        """
        self.value_generator = value_generator
        self.target_list = target_df[target_df.TokenSymbol == token_symbol].Value

    
    def search_parameters(self, initial_scale: float, step: float, final_scale: float, title: str, acc: int=100, x_size: int=10, y_size: int=10):
        """
        pick best scale parameter for cauchy distribution

        Keyword arguments:
        initial_scale (float) -- starting point to tune scale
        step (float) -- step value for incrementing scale for iteration
        final_scale (float) -- final scale point
        acc (int) -- how many cauchy generations are required to test each scale value, higher it is - more precise
            will be final result (default 100)
        x_size (int) -- plot x axis size
        y_size (int) -- plot y axis size
        """
        # get real life percentiles
        quartile = np.percentile(self.target_list, 25)
        median = np.percentile(self.target_list, 50)

        # set starting value for scale
        self.value_generator.scale = initial_scale

        # generate transactions for initial scales many times, calculate for each generation percentiles
        generated_table = [self.value_generator.generate_transactions(len(self.target_list)) for i in range(0, acc)]

        # find mean percentiles values
        generated_quartile = np.mean(np.apply_along_axis(lambda row: np.percentile(row, 25), 0, generated_table))
        generated_median = np.mean(np.apply_along_axis(lambda row: np.percentile(row, 50), 0, generated_table))

        # find error between real-life distribution and generated ones
        harmonic_mean_error = 2 * abs(quartile - generated_quartile) * abs(median - generated_median) / (
                                    abs(quartile - generated_quartile) + abs(median - generated_median))

        # form initial "best value", set table of scales with respective mean harmonic error, set lambda to pick best result
        best_match_tuple = (harmonic_mean_error, initial_scale)
        final_np_array = np.array([harmonic_mean_error, initial_scale])
        harmonic_mean_test = lambda cur_e, prev_e, cur_s, prev_s: (cur_e, cur_s) if cur_e < prev_e else (prev_e, prev_s)

        for current_scale in np.arange(initial_scale + step, final_scale, step):
            self.value_generator.scale = current_scale

            # find mean percentiles from many generations of cauchy
            generated_table = [self.value_generator.generate_transactions(len(self.target_list)) for i in range(0, acc)]
            generated_quartile = np.mean(np.apply_along_axis(lambda row: np.percentile(row, 25), 0, generated_table))
            generated_median = np.mean(np.apply_along_axis(lambda row: np.percentile(row, 50), 0, generated_table))

            # find best match conform harmonic mean and append current result to history of scales with errors
            harmonic_mean_error = 2 * abs(quartile - generated_quartile) * abs(median - generated_median) / (
                                        abs(quartile - generated_quartile) + abs(median - generated_median))
            final_np_array = np.vstack([final_np_array, [harmonic_mean_error, current_scale]])
            best_match_tuple = harmonic_mean_test(harmonic_mean_error, best_match_tuple[0], current_scale, best_match_tuple[1])

        # show best results
        print(best_match_tuple)

        # plot scales with respective errors
        plt.figure(figsize=(x_size, y_size))
        ax = sns.lineplot(x=final_np_array[:, 1], y=final_np_array[:, 0])
        ax.set_title(title)
        ax.set_xlabel("scale")
        ax.set_ylabel("harmonic error")
        plt.show()



class LognormalParameterSearcher:
    def __init__(self, value_generator: LognormalGenerator, target_df: pd.DataFrame, token_symbol: str):
        self.value_generator = value_generator
        self.target_list = target_df[target_df.TokenSymbol == token_symbol].Value
        
        
    def show_mean_and_std(self):
        print("mean value = " + str(np.mean(self.target_list)))
        print("standard deviation value = " + str(np.std(self.target_list)))

    
    def search_parameters(self, initial_sigma: float, sigma_step: float, final_sigma: float, title: str, acc: int=100, x_size: int=10, y_size: int=10):
        #  considering that original distribution can contain outliers it will be correct to set as mean lognormal value a median of the
        # real-life distribution
        self.value_generator.mean = np.mean(self.target_list)
        self.value_generator.sigma = initial_sigma

        original_25_percentile = np.percentile(self.target_list, 25)
        original_50_percentile = np.percentile(self.target_list, 50)

        # generate transactions for initial scales many times, calculate for each generation percentiles (25-th and 50-th)
        generated_table = [self.value_generator.generate_transactions(len(self.target_list)) for i in range(0, acc)]

        # find mean percentiles values
        generated_25_quartile_mean = np.mean(np.apply_along_axis(lambda row: np.percentile(row, 25), 0, generated_table))
        generated_50_quartile_mean = np.mean(np.apply_along_axis(lambda row: np.percentile(row, 50), 0, generated_table))

        # find error between real-life distribution and generated ones
        harmonic_mean_error = 2 * abs(original_25_percentile - generated_25_quartile_mean) * abs(original_50_percentile - generated_50_quartile_mean) / (
                                    abs(original_25_percentile - generated_25_quartile_mean) + abs(original_50_percentile - generated_50_quartile_mean))

        # form initial "best value", set table of scales with respective mean harmonic error, set lambda to pick best result
        best_match_tuple = (harmonic_mean_error, initial_sigma)
        final_np_array = np.array([harmonic_mean_error, initial_sigma])
        harmonic_mean_test = lambda cur_e, prev_e, cur_s, prev_s: (cur_e, cur_s) if cur_e < prev_e else (prev_e, prev_s)

        for current_sigma in np.arange(initial_sigma + sigma_step, final_sigma, sigma_step):
            self.value_generator.sigma = current_sigma

            # find mean percentiles from many generations of lognormal
            generated_table = [self.value_generator.generate_transactions(len(self.target_list)) for i in range(0, acc)]
            generated_25_quartile_mean = np.mean(np.apply_along_axis(lambda row: np.percentile(row, 25), 0, generated_table))
            generated_50_quartile_mean = np.mean(np.apply_along_axis(lambda row: np.percentile(row, 50), 0, generated_table))

            # find error between real-life distribution and generated ones
            harmonic_mean_error = 2 * abs(original_25_percentile - generated_25_quartile_mean) * abs(original_50_percentile - generated_50_quartile_mean) / (
                                        abs(original_25_percentile - generated_25_quartile_mean) + abs(original_50_percentile - generated_50_quartile_mean))
            final_np_array = np.vstack([final_np_array, [harmonic_mean_error, current_sigma]])
            best_match_tuple = harmonic_mean_test(harmonic_mean_error, best_match_tuple[0], current_sigma, best_match_tuple[1])

        # show best results
        print(best_match_tuple)
        print("chosen mean value is " + str(self.value_generator.mean))

        # plot scales with respective errors
        plt.figure(figsize=(x_size, y_size))
        ax = sns.lineplot(x=final_np_array[:, 1], y=final_np_array[:, 0])
        ax.set_title(title)
        ax.set_xlabel("scale")
        ax.set_ylabel("harmonic error")
        plt.show()
