# ROCm Prometheus Metrics Server

A Prometheus compatable metrics server that exposes information about AMD GPUs using the rocm-smi cli tool and some python


## Issues

It appears that the VRAM % reading from the standard rocm-smi output (calling with no args) is not present in the JSON outputs?

## rocm-smi version

Only tested on version:
```
AMD ROCm System Management Interface | ROCM-SMI version: 1.4.1 | Kernel version: 5.18.13
```
