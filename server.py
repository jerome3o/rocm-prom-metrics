import subprocess
import json
import re
from typing import Dict, Union
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


def _can_cast_to_float(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def _define_gauges_and_labels(output: dict) -> Union[Dict[str, Gauge], Dict[str, str]]:

    # TODO(j.swannack): need to make guages+labels adhere
    #   to prometheus naming conventions

    # card will be a label, so get unqiue metrics across all cards
    metric_info = list(
        set(
            [
                (_get_prom_friendly_metric_name(name), name, value)
                for card in output.values()
                for name in card.keys()
            ]
        )
    )

    # metrics that can't be cast to float should be used as labels
    label_dict = {
        raw_name: name for name, raw_name, value in metric_info if not _can_cast_to_float(value)
    }

    # define gauges from metric_info
    return {
        metric_name: Gauge(
            metric_name,
            raw_name,
            labelnames=["gpu", *label_dict],
        )
        for metric_name, raw_name, _ in metric_info
    }, label_dict


def main():

    # get output dict
    output = get_smi_output()

    # start prometheus server
    start_http_server(8000)

    # define gauges
    gauges, label_dict = _define_gauges_and_labels(output)

    while True:
        # get new output
        output = get_smi_output()

        # update gauges
        for card_name, card_metrics in output.items():

            # get labels
            label_values = {
                label_name: card_metrics[raw_name] for raw_name, label_name in label_dict.items()
            }

            for metric_name, metric_value in card_metrics.items():
                # ignore labels
                if metric_name in label_dict:
                    continue

                prom_metric_name = _get_prom_friendly_metric_name(metric_name)
                gauges[prom_metric_name].labels(gpu=card_name, **label_values).set(metric_value)

        # sleep for 1 second
        time.sleep(1)


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)
    main()
