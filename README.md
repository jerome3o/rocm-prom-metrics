# ROCm Prometheus Metrics Server

A Prometheus compatable metrics server that exposes information about AMD GPUs using the rocm-smi cli tool and some python


## Issues

### Memory useage always 0% in metrics

It appears that the VRAM % reading from the standard rocm-smi output (calling with no args) is not present in the JSON outputs?

I have "fixed" this with a patch to rocm-smi, so that it uses the same function for getting memory usage as it does for the VRAM in the "showAllConcise"/standard output. This isn't an amazing solution, and I'm sure I'm missing some nuance regarding different memory types in the GPU but this is ok for now.

#### Applying the fix

```sh
sudo cp ./smi_patch/rocm-smi-patched.py $(which rocm-smi)
sudo systemctl restart rocm-prom-metrics.service
```

### Power usage not telemetered

TODO:
* Add in power useage

## rocm-smi version

Only tested on version:
```
AMD ROCm System Management Interface | ROCM-SMI version: 1.4.1 | Kernel version: 5.18.13
```
