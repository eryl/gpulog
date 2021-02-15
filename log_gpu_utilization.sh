#!/usr/bin/env bash
nvidia-smi --query-gpu=timestamp,pci.bus_id,utilization.gpu,utilization.memory --format=csv -l 1 -f gpu_log_$(date +"%T").csv
