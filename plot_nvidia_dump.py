import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('statfile', type=Path)
    args = parser.parse_args()

    stats = pd.read_csv(args.statfile, parse_dates=True, skipinitialspace=True, index_col=0)
    for col_name in ('utilization.gpu [%]', 'utilization.memory [%]'):
        stats[col_name] = stats[col_name].str.rstrip(' %').astype(float) / 100

    fig, (ax_compute, ax_mem) = plt.subplots(2, 1, sharex='col')
    stats.groupby('pci.bus_id')['utilization.gpu [%]'].plot(ax=ax_compute)
    stats.groupby('pci.bus_id')['utilization.memory [%]'].plot(ax=ax_mem)
    ax_compute.set_ylim(0, 1)
    ax_mem.set_ylim(0, 1)
    plt.show()

if __name__ == '__main__':
    main()