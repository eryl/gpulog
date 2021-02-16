import time
import argparse

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from pynvml import (nvmlInit,
                     nvmlDeviceGetCount,
                     nvmlDeviceGetHandleByIndex,
                     nvmlDeviceGetUtilizationRates,
                     nvmlDeviceGetHandleByPciBusId,
                     nvmlDeviceGetPciInfo,
                     nvmlDeviceGetName)


def live_utilization_plot(filter_ids):
    nvmlInit()
    device_count = nvmlDeviceGetCount()
    if filter_ids is None:
        filter_ids = list(range(device_count))

    bus_ids = []
    for i in range(device_count):
        handle = nvmlDeviceGetHandleByIndex(i)
        pci_info = nvmlDeviceGetPciInfo(handle)
        bus_id = pci_info.busId
        bus_ids.append(bus_id)

    handles = {i: nvmlDeviceGetHandleByPciBusId(bus_id) for i,bus_id in enumerate(sorted(bus_ids)) if i in filter_ids}

    gpu_utils = {i:[] for i in range(device_count)}
    mem_utils = {i:[] for i in range(device_count)}
    dt_0 = time.time()
    dts = {i: [0] for i in range(device_count)}

    for i in range(device_count):
        handle = handles[i]
        util = nvmlDeviceGetUtilizationRates(handle)
        gpu_utils[i].append(util.gpu)
        mem_utils[i].append(util.memory)

    fig, (ax_gpu, ax_mem) = plt.subplots(nrows=2, ncols=1, sharex='col')
    ax_gpu.set_ylabel('GPU utilzation [%]')
    ax_mem.set_ylabel('Memory utilzation [%]')

    gpu_lines = {i: ax_gpu.plot(dts[i], gpu_utils[i], label=f'{i}')[0] for i in range(device_count)}
    mem_lines = {i: ax_mem.plot(dts[i], gpu_utils[i], label=f'{i}')[0] for i in range(device_count)}

    def init():
        ax_gpu.set_ylim(0, 105)
        ax_gpu.set_xlim(0, 10)
        ax_mem.set_ylim(0, 105)
        ax_mem.set_xlim(0, 10)
        return list(gpu_lines.values()) + list(mem_lines.values())

    def update(dt):
        xlim_low, xlim_high = ax_gpu.get_xlim()
        if xlim_high < dt*1.01:
            ax_gpu.set_xlim(0, dt * 1.2)
            ax_mem.set_xlim(0, dt * 1.2)
            fig.canvas.resize_event()

        for i in range(device_count):
            handle = handles[i]
            util = nvmlDeviceGetUtilizationRates(handle)
            xdata = dts[i]

            gpu_ydata = gpu_utils[i]
            mem_ydata = mem_utils[i]

            gpu_ydata.append(util.gpu)
            mem_ydata.append(util.memory)
            xdata.append(dt)
            gpu_lines[i].set_data(xdata, gpu_ydata)
            mem_lines[i].set_data(xdata, mem_ydata)

        return list(gpu_lines.values()) + list(mem_lines.values())

    def time_pump():
        while True:
            yield time.time() - dt_0

    ani = FuncAnimation(fig, update, frames=time_pump,
                        init_func=init, blit=False, interval=500)
    plt.legend()
    plt.show()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--filter-ids', help="If given, only display GPU's with these ids (numbered after bus id).",
                        type=int, nargs='+')
    args = parser.parse_args()

    live_utilization_plot(args.filter_ids)


if __name__ == '__main__':
    main()