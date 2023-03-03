import subprocess
import json
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


def get_smi_output() -> dict:
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


def main():
   
    # get output dict
    output = get_smi_output()



if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    main()
