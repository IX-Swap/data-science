from datetime import datetime, timedelta
from scipy.stats import weibull_min
from random import randrange

import pandas as pd
import numpy as np
import warnings
import scipy

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




class WeibullGenerator:
    def __init__(self, shape: float, loc: float, scale: float):
        self.shape = shape
        self.loc = loc
        self.scale = scale

    def reset_params(self, shape: float, loc: float, scale: float):
        self.shape = shape
        self.loc = loc
        self.scale = scale

    def generate_transactions(self, count: int) -> list:
        values = weibull_min.rvs(size=count, c=self.shape, loc=self.loc, scale=self.scale)

        return values


class Transaction:
    """
    Class with information regarding swapping transaction
    """
    def __init__(self, timestamp: datetime, 
                token_in_amount: float, token_in: str, 
                token_out: str, 
                txd:str=None, sender=None, to=None, desired_token_in_amount=None, sequence_swap_cnt=None, attempt_cnt=None):
        self.datetime_timestamp = timestamp
        self.token_in = token_in
        self.token_in_amount = token_in_amount
        self.token_out = token_out
        self.token_out_amount = None
        self.txd = txd
        self.sender = sender
        self.to = to
        self.desired_token_in_amount = desired_token_in_amount or token_in_amount
        self.sequence_swap_cnt = sequence_swap_cnt or 0
        self.attempt_cnt = attempt_cnt or 0


    def set_token_out_amount(self, token_out_amount: float):
        self.token_out_amount = token_out_amount
        
    
    def to_string(self) -> str:
        return str(
            'Transaction {datetime timestamp = ' + str(self.datetime_timestamp) + 
            ', token in amount = "' + str(self.token_in_amount) + 
            '", token in name = ' + str(self.token_in) + 
            ', token out amount = ' + str(self.token_out_amount) + 
            ', token out name = ' + str(self.token_out)
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
        ])

    
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
    
    def get_timestamps(self, start_time, periods, freq):
        time_between_events = []
        time_elapsed = 0

        while (True):
            values = scipy.stats.expon.rvs(size=1000, scale=1/freq)

            for i in range(len(values)):
                time_elapsed += values[i]

                if (time_elapsed + values[i] > periods):
                    timestamps = [start_time]
                    
                    for x in time_between_events:
                        timestamps.append(timestamps[-1] + timedelta(hours=x))
                        
                    return timestamps

                time_between_events.append(values[i])
            #  print(time_elapsed)


    def get_transactions(self, start_time, periods): 
        timestamps = self.get_timestamps(start_time, periods/60, self.frequency_generator.mean_occurencies*60) # periods - hours
        token_in_values = self.token_in_generator.generate_transactions(len(timestamps))

        self.transaction_history.extend(
            list(zip(timestamps, [self.first_currency]*len(timestamps), token_in_values, [self.second_currency]*len(timestamps)))
        )

        print(len(self.transaction_history), len(self.transaction_history[0]))
    #    print(self.transaction_history)
     #   exit(0)
        if (len(timestamps)):
            return timestamps[-1]
        return start_time


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
            self.transaction_history.append([
                    timestamps[index], self.first_currency, token_in_values[index], self.second_currency
                ]
            )


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
        transactions_matrix = np.array([transaction for transaction in self.transaction_history])
        transaction_history_df = pd.DataFrame(data=transactions_matrix, columns=[
            'datetime_timestamp', 'token_in', 'token_in_amount', 'token_out'
        ])
        

        # fix transformation of numerical features into string at numpy stage to numerical again
        transaction_history_df['token_in_amount'] = pd.to_numeric(transaction_history_df['token_in_amount']) 
        
        # either append new records to the existing file, or create a new one from existing table
        try:
            with open(filename) as f:
                transaction_history_df.to_csv(filename, mode='a', header=False)
        except IOError:
            transaction_history_df.to_csv(filename)


    def get_dataframe(self) -> pd.DataFrame:
        # vectorize all transactions into numpy matrix and then make dataframe out of it
        transactions_matrix = np.array([transaction for transaction in self.transaction_history])
        transaction_history_df = pd.DataFrame(data=transactions_matrix, columns=[
            'datetime_timestamp', 'token_in', 'token_in_amount', 'token_out'
        ])

        # fix transformation of numerical features into string at numpy stage to numerical again
        transaction_history_df['token_in_amount'] = pd.to_numeric(transaction_history_df['token_in_amount'])

        return transaction_history_df