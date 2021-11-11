from decimal import *
from typing import Union

def expand_to_18_decimals(n: Union[int, float, str]):
    return int(Decimal(str(n)) * Decimal('1000000000000000000'))


# todo: check function
def contract_18_decimals_to_float(n: str):
    if n is None:
        return None

    return float(Decimal(n) / Decimal('1000000000000000000'))
