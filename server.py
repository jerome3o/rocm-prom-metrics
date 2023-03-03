import subprocess
import json
import re
from typing import Dict
from prometheus_client import start_http_server, Gauge

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
    output_str = subprocess.check_output(
        [
            "rocm-smi",
            "--alldevices",
            "--json",
            *_flags,
        ]
    )
    return json.loads(output_str)


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


def _define_gauges(output: dict) -> Dict[str, Gauge]:

    # TODO(j.swannack): need to make guages+labels adhere 
    #   to prometheus naming conventions

    # card will be a label, so get unqiue metrics across all cards
    metric_info = list(set([
        (_get_prom_friendly_metric_name(metric_name), metric_name)
        for card in output.values()
        for metric_name in card.keys()
    ]))

    # define gauges from metric_info
    return {
        metric_name: Gauge(
            metric_name,
            raw_name,
            labelnames=["gpu"],
        )
        for metric_name, raw_name in metric_info
    }


def main():
   
    # get output dict
    output = get_smi_output()


    # start prometheus server
    start_http_server(8000)

    # define gauges
    gauges = _define_gauges(output)

    while True:
        # get new output
        output = get_smi_output()

        # update gauges
        for card_name, card_metrics in output.items():
            for metric_name, metric_value in card_metrics.items():
                prom_metric_name = _get_prom_friendly_metric_name(metric_name)
                gauges[prom_metric_name].labels(gpu=card_name).set(metric_value)

        # sleep for 1 second
        time.sleep(1)

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    main()
