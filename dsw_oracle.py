import logging

from typing import List
import amm
from settings import WINDOW_SIZE, GRANULARITY


logger = logging.getLogger(__name__)

class Observation:
    def __init__(self, timestamp: int, price_X_cumulative: float, price_Y_cumulative: float) -> None:
        self.timestamp = timestamp
        self.price_X_cumulative = price_X_cumulative
        self.price_Y_cumulative = price_Y_cumulative

        logger.debug(f"Observation created at {self.timestamp}, {self}")


    def __str__(self) -> str:
        return f"timestamp={self.timestamp}, price_X_cumulative={self.price_X_cumulative}, price_Y_cumulative={self.price_Y_cumulative}"


class DSWOracle:
    def __init__(self, window_size: int, granularity: int) -> None:
        self.window_size = window_size
        self.granularity = granularity
        self.period_size = window_size // granularity
        self.observations:List[Observation] = []

        assert window_size % granularity == 0, "ERROR: WINDOW_SIZE not divisible by GRANULARITY"


    def observation_index_of(self, timestamp: int):
        epoch_period = timestamp // self.period_size #?

        return epoch_period % self.granularity


    # updates on the first call per block price accumulators
    def update(self, block_timestamp: int):
        for i in range(len(self.observations), self.granularity):
            self.observations.append(Observation(0, 0, 0))

        observation_index = self.observation_index_of(block_timestamp)
        observation = self.observations[observation_index]

        time_elapsed = block_timestamp - observation.timestamp

        if time_elapsed > self.period_size:
            price_X_cumulative, price_Y_cumulative = amm.current_cumulative_prices(block_timestamp)
            observation.timestamp = block_timestamp
            observation.price_X_cumulative = price_X_cumulative
            observation.price_X_cumulative = price_Y_cumulative

            logger.debug(f"Inside update, time_elapsed={time_elapsed}, updated observation: {observation}")


    
    def get_first_observation_in_window(self, block_timestamp: int) -> Observation:
        logger.debug(f"Inside get_first_observation_in_window, block_timestamp: {block_timestamp}")

        observation_index = self.observation_index_of(block_timestamp)
        first_observation_index = (observation_index + 1) % self.granularity
      #  print(first_observation_index, len(self.observations))
        first_observation = self.observations[first_observation_index]

        logger.debug(f"First observation: {first_observation}")

        return first_observation


    def compute_amount_out(self, price_comulative_start: float, price_comulative_end: float, time_elapsed: int, amount_in: float):
        price_average = (price_comulative_end - price_comulative_start) / time_elapsed
        amount_out = price_average * amount_in

        return amount_out


    def consult(self, token_in: str, amount_in: float, token_out: str, block_timestamp: int):
        first_observation = self.get_first_observation_in_window(block_timestamp)

        time_elapsed = block_timestamp - first_observation.timestamp
        price_X_cumulative, price_Y_cumulative = amm.current_cumulative_prices(block_timestamp)

        if amm.X() == token_in:
            return self.compute_amount_out(first_observation.price_X_cumulative, price_X_cumulative, time_elapsed, amount_in)
        else:
            return self.compute_amount_out(first_observation.price_Y_cumulative, price_Y_cumulative, time_elapsed, amount_in)


_dsw_oracle = DSWOracle(WINDOW_SIZE, GRANULARITY)

update = _dsw_oracle.update
consult = _dsw_oracle.consult