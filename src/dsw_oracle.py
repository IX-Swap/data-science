import logging

from typing import List
import amm
from settings import WINDOW_SIZE, GRANULARITY
from safe_math import q_decode_144

logger = logging.getLogger(__name__)

class Observation:
    def __init__(self, timestamp: int, price_X_cumulative: int, price_Y_cumulative: int) -> None:
        self.timestamp = timestamp
        self.price_X_cumulative = price_X_cumulative
        self.price_Y_cumulative = price_Y_cumulative

        logger.debug(f"Observation created at {self.timestamp}, {self}")


    def __str__(self) -> str:
        return f"timestamp={self.timestamp}, price_X_cumulative={self.price_X_cumulative}, price_Y_cumulative={self.price_Y_cumulative}"


class DSWOracle:
    def __init__(self, window_size: int, granularity: int) -> None:
        self.window_size = window_size
        self.fallback_window_size = window_size * 2
        self.granularity = granularity
        self.period_size = window_size // granularity
        self.observations:List[Observation] = []

        assert window_size % granularity == 0, "ERROR: WINDOW_SIZE not divisible by GRANULARITY"

        print(window_size, granularity, self.period_size)

    def reset(self, window_size, period_size, granularity):
        self.window_size = window_size
        self.period_size = period_size
        self.granularity = granularity
        self.observations = []

        assert window_size % granularity == 0, "ERROR: WINDOW_SIZE not divisible by GRANULARITY"
        assert window_size // granularity == period_size, "ERROR: GRANULARITY, PERIOD_SIZE MISMATCH"

        print(self.window_size, self.period_size, self.granularity)


    def observation_index_of(self, timestamp: int):
        epoch_period = timestamp // self.period_size #

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
            observation.price_Y_cumulative = price_Y_cumulative

            logger.debug(f"Inside update, time_elapsed={time_elapsed}, updated observation: {observation}")


    def get_fallback_observation_offset_index(self, block_timestamp):
        reference_timestamp = block_timestamp
        boundary_timestamp = block_timestamp - self.fallback_window_size

        offset_index = 0

        for i in range(0, len(self.observations)):
            timestamp = self.observations[i].timestamp

            if timestamp >= boundary_timestamp and timestamp < reference_timestamp:
                reference_timestamp = timestamp
                offset_index = i+1

        return offset_index

    def get_fallback_observation(self, block_timestamp):
        offset_index = self.get_fallback_observation_offset_index(block_timestamp)

        assert offset_index > 0, 'Invalid offset'

        fallback_observation = self.observations[offset_index - 1]

        return fallback_observation

    def has_fallback_observation(self, block_timestamp):
        return self.get_fallback_observation_offset_index(block_timestamp) > 0

    
    def get_first_observation_in_window(self, block_timestamp: int) -> Observation:
        logger.debug(f"Inside get_first_observation_in_window, block_timestamp: {block_timestamp}")

        observation_index = self.observation_index_of(block_timestamp)
        first_observation_index = (observation_index + 1) % self.granularity
        first_observation = self.observations[first_observation_index]


        logger.debug(f"First observation: {first_observation}")

        return first_observation


    def compute_amount_out(self, price_comulative_start: int, price_comulative_end: int, time_elapsed: int, amount_in: int):
        price_average = (price_comulative_end - price_comulative_start) // time_elapsed
        amount_out = q_decode_144(price_average * amount_in)
        decoded_price_average = q_decode_144(price_average * 1000000000000000000)
        return amount_out, decoded_price_average


    def can_consult(self, block_timestamp):
        if len(self.observations) <= 0:
            return False

        first_observation = self.get_first_observation_in_window(block_timestamp)

        time_elapsed = block_timestamp - first_observation.timestamp
       # logger.info(f'{time_elapsed}, {self.window_size}, {block_timestamp}, {first_observation.timestamp}')

        return time_elapsed <= self.window_size or self.has_fallback_observation(block_timestamp)



    def consult(self, token_in: str, amount_in: int, token_out: str, block_timestamp: int):
        first_observation = self.get_first_observation_in_window(block_timestamp)

        _window_size = self.window_size 
        first_observation = self.get_first_observation_in_window(block_timestamp)
        time_elapsed = block_timestamp - first_observation.timestamp

        if time_elapsed > _window_size:
            first_observation = self.get_fallback_observation(block_timestamp)
            time_elapsed = block_timestamp - first_observation.timestamp
            _window_size = self.fallback_window_size


        # should never happen, assert
        assert time_elapsed <= _window_size, 'SlidingWindowOracle: MISSING_HISTORICAL_OBSERVATION, can`t consult'
        assert time_elapsed >= _window_size - self.period_size * 2 or _window_size == self.fallback_window_size, f'Unexpected TIME_ELAPSED = {time_elapsed}, min allowed: {_window_size - self.period_size * 2}'

        price_X_cumulative, price_Y_cumulative = amm.current_cumulative_prices(block_timestamp)

        if amm.X() == token_in:
            return self.compute_amount_out(first_observation.price_X_cumulative, price_X_cumulative, time_elapsed, amount_in)
        else:
            return self.compute_amount_out(first_observation.price_Y_cumulative, price_Y_cumulative, time_elapsed, amount_in)


_dsw_oracle = DSWOracle(WINDOW_SIZE, GRANULARITY)

update = _dsw_oracle.update
can_consult = _dsw_oracle.can_consult
consult = _dsw_oracle.consult
reset = lambda window_size, period_size, granularity: _dsw_oracle.reset(window_size, period_size, granularity)