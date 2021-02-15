import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('statfile', type=Path)
    parser.add_argument('--filter-ids', help="If given, only display GPU's with these ids (numbered after bus id).", type=int, nargs='+')
    args = parser.parse_args()

    stats = pd.read_csv(args.statfile, parse_dates=True, skipinitialspace=True, index_col=0)
    for col_name in ('utilization.gpu [%]', 'utilization.memory [%]'):
        stats[col_name] = stats[col_name].str.rstrip(' %').astype(float) / 100

    bus_ids = {bus_id:i for i,bus_id in enumerate(sorted(stats['pci.bus_id'].unique()))}

    stats['gpu_id'] = [bus_ids[bus_id] for bus_id in stats['pci.bus_id']]
    if args.filter_ids:
        to_drop = set(bus_ids.values()) - set(args.filter_ids)
        for i in to_drop:
            stats = stats.drop(stats[stats['gpu_id'] == i].index)

    if len(stats) < 1:
        raise RuntimeError("No values to display, did you filter out all GPU ids?")

    fig, (ax_compute, ax_mem) = plt.subplots(2, 1, sharex='col')
    plt.suptitle(f'Utilization statistics from {args.statfile.name}')

    stats.groupby('gpu_id')['utilization.gpu [%]'].plot(ax=ax_compute)
    ax_compute.set_ylim(0, 1.05)
    ax_compute.set_ylabel('GPU utilization')
    stats.groupby('gpu_id')['utilization.memory [%]'].plot(ax=ax_mem)
    ax_mem.set_ylim(0, 1.05)
    ax_mem.set_ylabel('Memory utilization')

    # Are we sure the order of the plots are the same so that the legend is correct for both subplots?
    plt.legend(title="gpu_id")
    plt.tight_layout()
    plt.subplots_adjust(top=0.9)
    plt.show()

if __name__ == '__main__':
    main()