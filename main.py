import logging
import pandas as pd
import amm
import numpy as np
from monte_carlo import simulator

logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(name)s:%(message)s', datefmt="%m/%d/%Y %I:%M:%S %p")
logger = logging.getLogger(__name__)


def main():
    cnt = 0

    for transaction in simulator.generate_transactions():
        amm.create_swap(int(transaction.timestamp.timestamp()), transaction.value)
        cnt += 1

if __name__ == '__main__':
    main()