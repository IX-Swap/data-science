import logging
import math
import dsw_oracle

logger = logging.getLogger(__name__)


class VolatilityMitigator:
    def __init__(self, price_tollerance_threshold) -> None:
        self.price_tollerance_threshold = price_tollerance_threshold


    def mitigate(self, token_in: str, token_out: str, amount_in:float, amount_out:float, reserve_out:float, block_timestamp: int):
        # Which is the % of amount out relative to the remaining reserve of the token after the swap
        slice_factor = 100 * amount_out / reserve_out if reserve_out > amount_out else 100

        oracle_amount_out = dsw_oracle.consult(token_in, amount_in, token_out, block_timestamp)

        if oracle_amount_out == amount_out:
            out_amounts_diff = 0
        else:
            bigger_amount = max(amount_out, oracle_amount_out)
            smaller_amount = min(amount_out, oracle_amount_out)

            out_amounts_diff = 100 * (bigger_amount - smaller_amount) / ((bigger_amount + smaller_amount)/2)

        if out_amounts_diff <= 0:
            return False

        slice_factor_curve = slice_factor * math.sqrt(slice_factor)

        if slice_factor_curve > self.price_tollerance_threshold:
            slice_factor_curve = self.price_tollerance_threshold

        if out_amounts_diff > 100 - slice_factor_curve:
            logger.warn("TWAPBasedVIMV1: IL_RISK")

        return out_amounts_diff > 100 - slice_factor_curve

