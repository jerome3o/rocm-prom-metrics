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

    # Other values, to be sorted
    # "--showhw",
    # "--showallinfo",
    # "--showid",
    # "--showvbios",
    # "--showdriverversion",
    # "--showfwinfo",
    # "--showmclkrange",
    # "--showmemvendor",
    # "--showsclkrange",
    # "--showproductname",
    # "--showserial",
    # "--showuniqueid",
    # "--showvoltagerange",
    # "--showbus",
    # "--showpagesinfo",
    # "--showpendingpages",
    # "--showretiredpages",
    # "--showunreservablepages",
    # "--showbw",
    # "--showclocks",
    # "--showgpuclocks",
    # "--showprofile",
    # "--showmaxpower",
    # "--showmemoverdrive",
    # "--showoverdrive",
    # "--showperflevel",
    # "--showclkvolt",
    # "--showclkfrq",
    # "--showmeminfo",
    # "--showpids",
    # "--showpidgpus",
    # "--showreplaycount",
    # "--showrasinfo",
    # "--showvc",
    # "--showxgmierr",
    # "--showtopo",
    # "--showtopoaccess",
    # "--showtopoweight",
    # "--showtopohops",
    # "--showtopotype",
    # "--showtoponuma",
    # "--showenergycounter",
    # "--shownodesbw",
]

output_str = subprocess.check_output(["rocm-smi", "--alldevices", "--json"] + _flags)
output = json.loads(output_str)
print(json.dumps(output, indent=4))

