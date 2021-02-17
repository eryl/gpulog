import datetime
import time
import argparse
from collections import deque

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from pynvml import (nvmlInit,
                     nvmlDeviceGetCount,
                     nvmlDeviceGetHandleByIndex,
                     nvmlDeviceGetUtilizationRates,
                     nvmlDeviceGetHandleByPciBusId,
                     nvmlDeviceGetPciInfo,
                     nvmlDeviceGetName)


def live_utilization_plot(filter_ids, log_interval=0.5, limit_window=None):
    max_samples = None
    if limit_window:
        max_samples = int(limit_window/log_interval)*2  # Use *2 here so that we will not slide the line inside the visible window

    nvmlInit()
    device_count = nvmlDeviceGetCount()
    if not filter_ids:
        filter_ids = list(range(device_count))

    bus_ids = []
    for i in range(device_count):
        handle = nvmlDeviceGetHandleByIndex(i)
        pci_info = nvmlDeviceGetPciInfo(handle)
        bus_id = pci_info.busId
        bus_ids.append(bus_id)

    handles = {i: nvmlDeviceGetHandleByPciBusId(bus_id) for i, bus_id in enumerate(sorted(bus_ids)) if i in filter_ids}

    if max_samples is not None:
        gpu_utils = {i: deque(maxlen=max_samples) for i in handles.keys()}
        mem_utils = {i: deque(maxlen=max_samples) for i in handles.keys()}
    else:
        gpu_utils = {i:[] for i in handles.keys()}
        mem_utils = {i:[] for i in handles.keys()}
    dt_0 = time.time()

    dts = [0]
    if max_samples is not None:
        dts = deque(dts, maxlen=max_samples)

    for i in handles.keys():
        handle = handles[i]
        util = nvmlDeviceGetUtilizationRates(handle)
        gpu_utils[i].append(util.gpu)
        mem_utils[i].append(util.memory)

    fig, (ax_gpu, ax_mem) = plt.subplots(nrows=2, ncols=1, sharex='col')
    ax_gpu.set_ylabel('GPU utilzation [%]')
    ax_mem.set_ylabel('Memory utilzation [%]')
    formatted_date = datetime.datetime.fromtimestamp(time.time()).strftime('%D-%T')
    ax_mem.set_xlabel(f'Seconds since {formatted_date}')
    gpu_lines = {i: ax_gpu.plot(dts, gpu_utils[i], label=f'{i}')[0] for i in handles.keys()}
    mem_lines = {i: ax_mem.plot(dts, gpu_utils[i], label=f'{i}')[0] for i in handles.keys()}

    window_scale = 1.2
    def init():
        if limit_window:
            ax_gpu.set_ylim(0, 105)
            ax_gpu.set_xlim(0, limit_window*window_scale)
            ax_mem.set_ylim(0, 105)
            ax_mem.set_xlim(0, limit_window*window_scale)
        else:
            ax_gpu.set_ylim(0, 105)
            ax_gpu.set_xlim(0, 10)
            ax_mem.set_ylim(0, 105)
            ax_mem.set_xlim(0, 10)
        return list(gpu_lines.values()) + list(mem_lines.values())

    def update(dt):
        dts.append(dt)

        for i in handles.keys():
            handle = handles[i]
            util = nvmlDeviceGetUtilizationRates(handle)

            gpu_ydata = gpu_utils[i]
            mem_ydata = mem_utils[i]

            gpu_ydata.append(util.gpu)
            mem_ydata.append(util.memory)
            gpu_lines[i].set_data(dts, gpu_ydata)
            mem_lines[i].set_data(dts, mem_ydata)

        xlim_low, xlim_high = ax_gpu.get_xlim()

        if xlim_high < dt * 1.01:
            if limit_window:
                window_start = dt - limit_window
                window_end = window_start + limit_window*window_scale
                ax_gpu.set_xlim(window_start, window_end)
                ax_mem.set_xlim(window_start, window_end)

            else:
                ax_gpu.set_xlim(0, dt * window_scale)
                ax_mem.set_xlim(0, dt * window_scale)
            fig.canvas.resize_event()

        return list(gpu_lines.values()) + list(mem_lines.values())

    def time_pump():
        while True:
            yield time.time() - dt_0

    log_interval = int(1000*log_interval)
    ani = FuncAnimation(fig, update, frames=time_pump,
                        init_func=init, blit=False, interval=log_interval)
    plt.legend()
    plt.show()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filter_ids', help="If given, only display GPU's with these ids (numbered after bus id).",
                        type=int, nargs='*', default=None)
    parser.add_argument('-l', help="Log at this  interval in seconds", type=float, default=0.5)
    parser.add_argument('--limit-window',
                        help="Only display this many seconds of the most recent utlization data, "
                             "will make the utilization a sliding window", type=int)
    args = parser.parse_args()

    live_utilization_plot(args.filter_ids, args.l, args.limit_window)


if __name__ == '__main__':
    main()