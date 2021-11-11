from enum import Enum

import logging
import math
import dsw_oracle
import safe_math

logger = logging.getLogger(__name__)

class VolatilityMitigatorCheckStatus(Enum):
    CANT_CONSULT_ORACLE = 0
    CHECKED = 1
    MITIGATOR_OFF = 2
    NOT_REACHED = 3


class VolatilityMitigator:
    def __init__(self, price_tollerance_threshold) -> None:
        self.price_tollerance_threshold = price_tollerance_threshold

    def mitigate(self, token_in: str, token_out: str, amount_in: int, amount_out: int, reserve_out: int, block_timestamp: int, transaction):
        if not dsw_oracle.can_consult(block_timestamp):
            transaction.mitigator_check_status = VolatilityMitigatorCheckStatus.CANT_CONSULT_ORACLE
            
            return False
        else:
            transaction.mitigator_check_status = VolatilityMitigatorCheckStatus.CHECKED

            return self.__mitigate(token_in, token_out, amount_in, amount_out, reserve_out, block_timestamp, transaction)


    def __mitigate(self, token_in: str, token_out: str, amount_in:int, amount_out:int, reserve_out:int, block_timestamp: int, transaction):
        # Which is the % of amount out relative to the remaining reserve of the token after the swap
      #  slice_factor = 100 * amount_out / reserve_out if reserve_out > amount_out else 100
        slice_factor = 100 - 100 * (reserve_out - amount_out) // reserve_out if reserve_out > amount_out else 100

        oracle_amount_out = dsw_oracle.consult(token_in, amount_in, token_out, block_timestamp)
        transaction.oracle_amount_out = oracle_amount_out # TODO: move in another place

        if oracle_amount_out == amount_out:
            out_amounts_diff = 0
        else:
            bigger_amount = max(amount_out, oracle_amount_out)
            smaller_amount = min(amount_out, oracle_amount_out)

            out_amounts_diff = 100 * (bigger_amount - smaller_amount) // ((bigger_amount + smaller_amount)//2)

        if out_amounts_diff <= 0:
            return False

        slice_factor_curve = slice_factor * safe_math.sqrt(slice_factor)

        if slice_factor_curve > self.price_tollerance_threshold:
            slice_factor_curve = self.price_tollerance_threshold

        transaction.slice_factor = slice_factor
        transaction.slice_factor_curve = slice_factor_curve
        transaction.out_amounts_diff = out_amounts_diff
      #  if out_amounts_diff > 100 - slice_factor_curve:
      #      logger.warn("TWAPBasedVIMV1: IL_RISK")

        return out_amounts_diff > 100 - slice_factor_curve

