import random
import numpy as np
import matplotlib.pyplot as plt
import math
from datetime import datetime, timedelta
from scipy.stats import poisson, truncnorm
from random import randrange
import pandas as pd
from scipy.stats import halfcauchy


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
        self.cumulative_probabilities = 0
        
        
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
        elif mu < lower_bound:
            raise ValueError("creation: mean value (mu) can't be lower than lower bound")
        elif mu > upper_bound:
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
        elif mu > self.upper_bound:
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
        elif self.mu < lower_bound:
            raise ValueError("bounds editing: mean value (mu) can't be lower than lower bound")
        elif self.mu > upper_bound:
            raise ValueError("bounds editing: mean value (mu) can't be bigger than upper bound")
        
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        
    
    def generate_transactions(self, transactions_count: int) -> list:
        """
        Generate transaction prices list considering mu and sigma
        
        Keyword_arguments:
        transactions_count (int) -- required transactions count
        """

        x = np.random.pareto(0.258, size=transactions_count * 20)
        x = x[x<2000000][:transactions_count]

        # print("shape:", x.shape, transactions_count)

        return x
        
        # truncnorm.rvs(
        #     (self.lower_bound - self.mu)/self.sigma, 
        #     (self.upper_bound - self.mu)/self.sigma, 
        #     loc=self.mu, scale=self.sigma, size=transactions_count
        # )

class CauchyGenerator:
    """
    Generate transaction values conform Cauchy distribution
    """
    def __init__(self, loc: float, scale: float):
        """
        Create Cauchy generator with initial parameters
        
        Keyword_arguments:
        loc (float) -- locational parameter that defines where distribution
            will be centered
        scale (float) -- how far will tales (distribution) go
        """
        self.loc = loc
        self.scale = scale
      
    
    def reset_params(self, loc: float, scale: float):
        """
        Change mean and standard deviation parameters of existing generator
        
        Keyword_arguments:
        loc (float) -- locational parameter that defines where distribution
            will be centered
        scale (float) -- how far will tales (distribution) go
        """
        self.loc = loc
        self.scale = scale
        
    
    def generate_transactions(self, transactions_count: int, factor: int) -> list:
        """
        Generate transaction prices list considering mu and sigma
        
        Keyword_arguments:
        transactions_count (int) -- required transactions count
        """
        factor = 1
        return halfcauchy.rvs(size=transactions_count, loc=self.loc, scale=self.scale // factor)



class Transaction:
    """
    Class with information regarding swapping transaction
    """
    def __init__(self, timestamp: datetime, 
                token_in_amount: float, token_in: str, 
                token_out: str, 
                slope: int=5, txd:str=None):
        self.datetime_timestamp = timestamp
        self.token_in = token_in
        self.token_in_amount = token_in_amount
        self.token_out = token_out
        self.token_out_amount = None
        self.slope = slope
        self.txd = txd


    def set_token_out_amount(self, token_out_amount: float):
        self.token_out_amount = token_out_amount
        
    
    def to_string(self) -> str:
        return str(
            'Transaction {datetime timestamp = ' + str(self.datetime_timestamp) + 
            ', token in amount = "' + str(self.token_in_amount) + 
            '", token in name = ' + str(self.token_in) + 
            ', token out amount = ' + str(self.token_out_amount) + 
            ', token out name = ' + str(self.token_out) + 
            ', slope = ' + str(self.slope) + '}'
        )

    
    def to_record(self) -> np.array:
        """
        Transform transaction data into numpy array of data
        """
        return np.array([
            self.datetime_timestamp,
            self.token_in,
            self.token_in_amount,
            self.token_out,
            self.token_out_amount,
            self.slope
        ])
    

class MonteCarloTransactionSimulator:
    """
    Monte Carlo transactions generator, that generates transactions frequency using Poisson 
    distribution and transaction values using normal distribution (time metrics - milliseconds)
    """
    def __init__(
        self, frequency_generator: PoissonGenerator, token_in_generator, 
        first_currency: str, second_currency: str
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

        self.start_time = None
        
    
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
        if self.start_time is None:
            self.start_time = current_timestamp

        timestamps = self.frequency_generator.generate_transactions(current_timestamp)
        timestamps.sort()

        if current_timestamp - self.start_time <= timedelta(days=1):
            token_in_values = self.token_in_generator.generate_transactions(len(timestamps), 250)
        else:
            token_in_values = self.token_in_generator.generate_transactions(len(timestamps), 1)

        # form new transactions and record them into 'transaction history' variable
        for index in range(len(timestamps)):
            new_transaction = Transaction(
                timestamp=timestamps[index], 
                token_in_amount=token_in_values[index], 
                token_in=self.first_currency,
                token_out=self.second_currency
            )
            self.transaction_history.append(new_transaction)


    def get_history(self) -> list:
        """
        Get transaction history
        """
        return self.transaction_history
            
            
    def transaction_history_to_csv(self, filename: str, ratio):
        """
        Write transaction history to specified .csv file
        
        Keyword arguments:
        filename (str) -- name of .csv file where to write data
        """
        # vectorize all transactions into numpy matrix and then make dataframe out of it
        transactions_matrix = np.array([transaction.to_record() for transaction in self.transaction_history])
        transaction_history_df = pd.DataFrame(data=transactions_matrix, columns=[
            'datetime_timestamp', 'token_in', 'token_in_amount', 'token_out', 'token_out_amount', 'slope'
        ])
        

        # fix transformation of numerical features into string at numpy stage to numerical again
        transaction_history_df['token_in_amount'] = pd.to_numeric(transaction_history_df['token_in_amount']) / ratio
        transaction_history_df['token_out_amount'] = pd.to_numeric(transaction_history_df['token_out_amount'])
        
        # either append new records to the existing file, or create a new one from existing table
        try:
            with open(filename) as f:
                transaction_history_df.to_csv(filename, mode='a', header=False)
        except IOError:
            transaction_history_df.to_csv(filename)


    def get_dataframe(self) -> pd.DataFrame:
        # vectorize all transactions into numpy matrix and then make dataframe out of it
        transactions_matrix = np.array([transaction.to_record() for transaction in self.transaction_history])
        transaction_history_df = pd.DataFrame(data=transactions_matrix, columns=[
            'datetime_timestamp', 'token_in', 'token_in_amount', 'token_out', 'slope'
        ])

        # fix transformation of numerical features into string at numpy stage to numerical again
        transaction_history_df['token_in_amount'] = pd.to_numeric(transaction_history_df['token_in_amount'])

        return transaction_history_df
            
#            ['datetime_timestamp', 'token_in', 'token_in_amount', 'token_out',  'slope'])

# # create simulator with specifying parameters of the normal distribution for token_in
# # value estimation and Poisson distribution for transaction frequency estimation
# simulator = MonteCarloTransactionSimulator(
#     PoissonGenerator(cycle_size=60000, mean_occurencies=500), 
#     NormalGenerator(mu=10, sigma=5, lower_bound=5, upper_bound=15), 'ETH', 'DAI'
# )

# # set current timestamp as starting point and start loop, where each iteration shifts reviewable
# # timestamp further conform simulator cycle size
# current_iteration_timestamp = datetime.now()
# for index in range(60*24*7):
#     simulator.generate_transactions(current_iteration_timestamp)
#     current_iteration_timestamp += timedelta(milliseconds=randrange(simulator.frequency_generator.cycle_size))

# show generated transactions history
# for index in range(len(simulator.transaction_history)):
#     print(simulator.transaction_history[index].to_string())
    
# write generated transactions history to csv file
# simulator.transaction_history_to_csv('history.csv')

# # show generated transactions history
# for index in range(int(len(simulator.transaction_history) / 10)):
#     print(simulator.transaction_history[index].to_string())