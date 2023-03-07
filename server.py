import subprocess
import json
import re
import os
import time
from typing import Dict, Union
from prometheus_client import start_http_server, Gauge


# get development flag
DEV = os.environ.get("DEV", False)
PORT = os.environ.get("PORT", 9101)

_flags = [
    # HW related
    "--showfan",
    "--showpower",
    "--showtemp",
    "--showuse",
    "--showmemuse",
    "--showvoltage",
    # This hopefully covers everything
    "--showallinfo",
    # See ./other_rocm_smi_options.txt for more options
]

_metrics = [
    "Temperature (Sensor edge) (C)",  # "52.0",
    "Temperature (Sensor junction) (C)",  # "56.0",
    "Temperature (Sensor memory) (C)",  # "52.0",
    "GPU OverDrive value (%)",  # "0",
    "GPU Memory OverDrive value (%)",  # "0",
    "Max Graphics Package Power (W)",  # "203.0",
    "Average Graphics Package Power (W)",  # "35.0",
    "GPU use (%)",  # "99",
    "GPU memory use (%)",  # "0",
    "PCIe Replay Count",  # "0",
    "Voltage (mV)",  # "1018",
    "Energy counter",  # "3436801806",
    "Accumulated Energy (uJ)",  # "52583068287.32"
]

_labels = [
    "Serial Number",  # "ac1b58f8c066790f",
    "GPU ID",  # "0x73bf",
    "Unique ID",  # "0xac1b58f8c066790f",
    "PCI Bus",  # "0000:03:00.0",
    "Card series",  # "0x73bf",
    "Card model",  # "0x2407",
    "Card vendor",  # "Advanced Micro Devices, Inc. [AMD/ATI]",
    "Card SKU",  # "D4140E",
    # "Memory Activity", # "N/A",
    # "GPU memory vendor", # "samsung",
    # "pcie clock level", # "1 (8.0GT/s x8)",
    # "Performance Level", # "auto",
    # "dcefclk clock speed:", # "(417Mhz)",
    # "dcefclk clock level:", # "0",
    # "fclk clock speed:", # "(1251Mhz)",
    # "fclk clock level:", # "1",
    # "mclk clock speed:", # "(96Mhz)",
    # "mclk clock level:", # "0",
    # "sclk clock speed:", # "(2270Mhz)",
    # "sclk clock level:", # "1",
    # "socclk clock speed:", # "(800Mhz)",
    # "socclk clock level:", # "1",
    # "VBIOS version", # "113-D4140EXL-XL",
    # "ASD firmware version", # "0x21000095",
    # "CE firmware version", # "37",
    # "DMCU firmware version", # "0",
    # "MC firmware version", # "0",
    # "ME firmware version", # "64",
    # "MEC firmware version", # "104",
    # "MEC2 firmware version", # "104",
    # "PFP firmware version", # "95",
    # "RLC firmware version", # "95",
    # "RLC SRLC firmware version", # "0",
    # "RLC SRLG firmware version", # "0",
    # "RLC SRLS firmware version", # "0",
    # "SDMA firmware version", # "81",
    # "SDMA2 firmware version", # "81",
    # "SMC firmware version", # "00.58.86.00",
    # "SOS firmware version", # "0x00210864",
    # "TA RAS firmware version", # "27.00.01.62",
    # "TA XGMI firmware version", # "32.00.00.13",
    # "UVD firmware version", # "0x00000000",
    # "VCE firmware version", # "0x00000000",
    # "VCN firmware version", # "0x0211a000",
]


def get_smi_output() -> Dict[str, Dict[str, str]]:
    """
    Example output:
    {
        "card0": {
            "GPU ID": "0x73bf",
            "Unique ID": "0xac1b58f8c066790f",
            "VBIOS version": "113-D4140EXL-XL",
            "Temperature (Sensor edge) (C)": "52.0",
            ...
        },
        "card1": {
            ...
        },
        ...
        "system": {
            "Driver version": "5.18.13"
        }
    }
    """
    if not DEV:
        output_str = subprocess.check_output(
            [
                "rocm-smi",
                "--alldevices",
                "--json",
                *_flags,
            ]
        )
        return json.loads(output_str)

    # for dev read in example.json
    with open("example.json", "r") as f:
        return json.load(f)


def _get_prom_friendly_metric_name(metric_name: str) -> str:
    """
    Convert metric names to prometheus friendly names
    """
    metric_name = re.sub(r"[^a-zA-Z0-9_]", "_", metric_name).lower()

    # remove trailing/leading underscores
    metric_name = metric_name.strip("_")

    # remove double underscores
    metric_name = re.sub(r"__+", "_", metric_name)

    return metric_name


def _try_cast_float(value: str) -> Union[float, str]:
    """
    Try to cast value to float, if not return original value
    """
    try:
        return float(value)
    except ValueError:
        return value


def _get_label_dict() -> Dict[str, str]:
    return {label: _get_prom_friendly_metric_name(label) for label in _labels}


def _define_gauges(output: dict) -> Union[Dict[str, Gauge], Dict[str, str]]:

    # TODO(j.swannack): need to make guages+labels adhere
    #   to prometheus naming conventions

    # card will be a label, so get unqiue metrics across all cards
    labels = _get_label_dict()

    # define gauges from metric_info
    return {
        metric_name: Gauge(
            _get_prom_friendly_metric_name(metric_name),
            metric_name,
            labelnames=["gpu", *labels.values()],
        )
        for metric_name in _metrics
    }


def main():

    # get output dict
    output = get_smi_output()

    # start prometheus server
    start_http_server(PORT)

    # define gauges
    gauges = _define_gauges(output)

    labels = _get_label_dict()

    while True:
        # get new output
        output = get_smi_output()

        # update gauges
        for card_name, card_metrics in output.items():
            
            # ignore system
            if card_name == "system":
                continue

            # get label values
            label_values = {label: card_metrics[label_raw] for label_raw, label in labels.items()}

            for metric_name, metric_value in card_metrics.items():
                
                if metric_name not in _metrics:
                    continue

                prom_metric_name = _get_prom_friendly_metric_name(metric_name)
                gauges[metric_name].labels(gpu=card_name, **label_values).set(metric_value)

        # sleep for 1 second
        time.sleep(1)


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)

    if DEV:
        import ipdb

        with ipdb.launch_ipdb_on_exception():
            main()
    else:
        main()
