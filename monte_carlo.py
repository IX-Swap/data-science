import random
import numpy as np
import matplotlib.pyplot as plt
import math
from datetime import datetime, timedelta
from scipy.stats import poisson
from random import randrange
import pandas as pd


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
    
    def __init__(self, mu: float=0, sigma: float=0):
        """
        Create a normal distribution generator
        
        Keyword_arguments:
        mu (float) -- mean transaction price (default 0.0)
        sigma (float) -- standard deviation of transaction price (default 0.0)
        """
        self.mu = mu
        self.sigma = sigma
      
    
    def reset_params(self, mu: float, sigma: float):
        """
        Change parameters of existing generator
        
        Keyword_arguments:
        mu (float) -- mean transaction price (default 0.0)
        sigma (float) -- standard deviation of transaction price (default 0.0)
        """
        self.mu = mu
        self.sigma = sigma
    

    def generate_transactions(self, transactions_count: int) -> list:
        """
        Generate transaction prices list considering mu and sigma
        
        Keyword_arguments:
        transactions_count (int) -- required transactions count
        """
        return np.random.normal(self.mu, self.sigma, transactions_count)



class Transaction:
    def __init__(self, timestamp: datetime, 
                token_in_amount: float, token_in: str, 
                token_out_amount: float, token_out: str, 
                slope: float=0.05):
        self.datetime_timestamp = timestamp
        self.token_in = token_in
        self.token_in_amount = token_in_amount
        self.token_out = token_out
        self.token_out_amount = token_out_amount
        self.slope = slope
        
    
    def to_string(self) -> str:
        return str(
            'Transaction {datetime timestamp = ' + str(self.datetime_timestamp) + 
            ', token in amount = "' + str(self.token_in_amount) + 
            '", token in name = ' + str(self.token_in) + 
            ', token out amount = ' + str(self.token_out_amount) + 
            ', token out name = ' + str(self.token_out) + 
            ', slope = ' + str(self.slope) + '}'
        )
    
    

class MonteCarloTransactionSimulator:
    """
    Monte Carlo transactions generator, that generates transactions frequency using Poisson 
    distribution and transaction values using normal distribution (time metrics - milliseconds)
    """
    def __init__(
        self, frequency_generator: PoissonGenerator, token_in_generator: NormalGenerator, 
        first_currency: str, second_currency: str
    ):
        """
        Create a Monte-Carlo transaction simulator
        
        Keyword_arguments:
        frequency_generator (PoissonGenerator) -- Poisson transaction distribution generator
        token_in_generator (NormalGenerator) -- Normal transaction distribution generator
        """
        self.frequency_generator = frequency_generator
        self.token_in_generator = token_in_generator
        self.first_currency = first_currency
        self.second_currency = second_currency
        self.transaction_history = []
        
    
    def reset_values_generator_params(self, mu: float, sigma: float):
        """
        Change parameters of existing values (normal distribution) generator
        
        Keyword_arguments:
        mu (float) -- mean transaction price (default 0.0)
        sigma (float) -- standard deviation of transaction price (default 0.0)
        """
        self.frequency_generator.reset_params(mu, sigma)
        
        
    def clear_transaction_history(self):
        """
        Clear all records from transaction history
        """
        self.transaction_history.clear()
    
    
    def generate_transactions(self, current_timestamp: datetime, current_amm_coef: float):
        """
        Generates transactions list with timestamps and values assigned to 
        
        Keyword arguments:
        current_timestamp (datetime) -- initial datetime point from where cycle will be reviewed
        current_amm_coef (float) -- current AMM market coefficient that defines price of out
            token relative to in token
        """
        # generate timestamps and token in values
        timestamps = self.frequency_generator.generate_transactions(current_timestamp)
        timestamps.sort()
        token_in_values = self.token_in_generator.generate_transactions(len(timestamps))
        
        # create transactions and form history with giving current new transaction
        for index in range(len(timestamps)):
            token_out_value = token_in_values[index] * current_amm_coef
            new_transaction = Transaction(
                timestamp=timestamps[index], 
                token_in_amount=token_in_values[index], 
                token_in=self.first_currency,
                token_out_amount=token_out_value,
                token_out=self.second_currency
            )
            self.transaction_history.append(new_transaction)


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
        # form empty dataframe
        transaction_history_dataframe = pd.DataFrame(columns=['datetime_timestamp', 'TokenIn', 'TokenInAmount', 'TokenOut', 'TokenOutAmount', 'Slope'])
        
        # append all new records to the dataframe
        for index in range(len(self.transaction_history)):
            new_row = {
                'datetime_timestamp': self.transaction_history[index].datetime_timestamp,
                'TokenIn': self.transaction_history[index].token_in,
                'TokenInAmount': self.transaction_history[index].token_in_amount, 
                'TokenOut': self.transaction_history[index].token_out,
                'TokenOutAmount': self.transaction_history[index].token_out_amount,
                'Slope': self.transaction_history[index].slope
            }
            transaction_history_dataframe = transaction_history_dataframe.append(new_row, ignore_index=True)
        
        # if there is such file -> append new records to it, otherwise create a new file from existing table
        try:
            with open(filename) as f:
                transaction_history_dataframe.to_csv(filename, mode='a', header=False)
        except IOError:
            transaction_history_dataframe.to_csv(filename)
            
            

# example of creating simulation
simulator = MonteCarloTransactionSimulator(
    PoissonGenerator(cycle_size=60000, mean_occurencies=500), 
    NormalGenerator(mu=10, sigma=5), 'ETH', 'DAI'
)

#  set starting point to be as current timestamp and then start loop, where after each iteration 
# reviewable timestamp will be updated by shifting it further conform generator cycle size
current_iteration_timestamp = datetime.now()
for index in range(60*24*7):
    simulator.generate_transactions(current_iteration_timestamp, current_amm_coef=0.15)
    current_iteration_timestamp += timedelta(milliseconds=randrange(simulator.frequency_generator.cycle_size))

# show all generated transactions
# for index in range(len(simulator.transaction_history)):
#     print(simulator.transaction_history[index].to_string())
    
# write all generated transactions (entire generated transaction history) to csv file
# simulator.transaction_history_to_csv('history.csv')