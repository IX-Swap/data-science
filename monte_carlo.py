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
    def __init__(self, id: int, timestamp: datetime, value: float):
        self.id = id
        self.timestamp = timestamp
        self.value = value
        
    
    def to_string(self) -> str:
        return str('Transaction {id = ' + str(self.id) + ', timestamp = "' + str(self.timestamp) + '", value = ' + str(self.value)) + '}'



class MonteCarloTransactionSimulator:
    """
    Monte Carlo transactions generator, that generates transactions frequency using Poisson 
    distribution and transaction values using normal distribution (time metrics - milliseconds)
    """
    def __init__(
        self, transaction_density_generator: PoissonGenerator, transaction_values_generator: NormalGenerator, 
        first_currency: str, second_currency: str
    ):
        """
        Create a Monte-Carlo transaction simulator
        
        Keyword_arguments:
        transaction_density_generator (PoissonGenerator) -- Poisson transaction distribution generator
        transaction_values_generator (NormalGenerator) -- Normal transaction distribution generator
        """
        self.transaction_density_generator = transaction_density_generator
        self.transaction_values_generator = transaction_values_generator
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
        self.transaction_density_generator.reset_params(mu, sigma)
        
        
    def clear_transaction_history(self):
        """
        Clear all records from transaction history
        """
        self.transaction_history.clear()
    
    
    def generate_transactions(self, current_timestamp: datetime):
        """
        Generates transactions list with timestamps and values assigned to 
        
        Keyword arguments:
        current_timestamp (datetime) -- initial datetime point from where cycle will be reviewed
        """
        # generate timestamps (and sort them) and generate transaction values
        timestamps = self.transaction_density_generator.generate_transactions(current_timestamp)
        timestamps.sort()
        values = self.transaction_values_generator.generate_transactions(len(timestamps))
        
        # create transactions, appending them to the transaction history
        for index in range(len(timestamps)):
            new_transaction = Transaction(index, timestamps[index], values[index])
            self.transaction_history.append(new_transaction)
            
            
    def transaction_history_to_csv(self, filename: str):
        """
        Write transaction history to specified .csv file
        
        Keyword arguments:
        filename (str) -- name of .csv file where to write data
        """
        # form empty dataframe
        transaction_history_dataframe = pd.DataFrame(columns=['id', 'FirstCurrency', 'SecondCurrency', 'Timestamp', 'Value'])
        
        # append all new records to the dataframe
        for index in range(len(self.transaction_history)):
            new_row = {
                'id': self.transaction_history[index].id, 
                'FirstCurrency': self.first_currency, 
                'SecondCurrency': self.second_currency, 
                'Timestamp': self.transaction_history[index].timestamp,
                'Value': self.transaction_history[index].value
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
    PoissonGenerator(cycle_size=60000, mean_occurencies=5), 
    NormalGenerator(mu=10, sigma=5), 'ETH', 'DAI'
)

#  set starting point to be as current timestamp and then start loop, where after each iteration 
# reviewable timestamp will be updated by shifting it further conform generator cycle size
current_iteration_timestamp = datetime.now()
for index in range(60*24*7):
    simulator.generate_transactions(current_iteration_timestamp)
    current_iteration_timestamp += timedelta(milliseconds=randrange(simulator.transaction_density_generator.cycle_size))

# show all generated transactions
for index in range(len(simulator.transaction_history)):
    print(simulator.transaction_history[index].to_string())
    
# write all generated transactions (entire generated transaction history) to csv file
simulator.transaction_history_to_csv('history.csv')