# Linux-HW-Info
## Supported HW
chassis, system, cpu, mainboard, dimm, gpu, psu, nic, transceiver
## Platform
linux / python3
## Requirements
- one of _nvidia-smi_ or _nvflash_ required to collect gpu meta info
- _lshw_ required to collect nic meta info
## Usage
import module
``` python
from hw_info_collector import HWInfoCollector
hw_info_collector = HWInfoCollector()
hw_info = hw_info_collector.get_hw_meta_info()  # json object returned
```
run directly
``` python
python hw_info_collector.py # display the result of json object
```