#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
    auther : freeyssu@gmail.com
    purpose : collect hw meta info - chassis, system, cpu, mainboard, dimm, gpu, psu, nic, transceiver
    usage : python hw_info_collector.py
    todo : hw utilization, ipmi sensor info
'''

import os
import logging
import logging.handlers
import subprocess
import re
import traceback
import time
import sys
import json


class HWInfoCollector():
    def __init__(self, debug: bool = False):
        self._logger = logging.getLogger('HWInfoCollector')
        self._logger.setLevel(logging.DEBUG if debug else logging.INFO)
        self._logger_formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(funcName)s | %(message)s')
        self._logger_stream_handler = logging.StreamHandler()
        self._logger_stream_handler.setFormatter(self._logger_formatter)
        self._logger.addHandler(self._logger_stream_handler)

        if os.geteuid() != 0:
            self._logger.error('Root privileges required.')
            raise Exception('Root privileges required.')

        if sys.version_info[0] != 3:
            self._logger.error('Python version 3 required.')
            raise Exception('Python version 3 required.')

    def run_command(self, command: str):
        '''
            Return `CompletedProcess` object after completed run process
        '''
        self._logger.debug('cmd : {}'.format(command))
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        self._logger.debug('cmd result: {}'.format(result))
        return result

    def run_command_print_result(self, command: str):
        '''
            Display all stdout/stderr and wait for process exit\n
            Return process return code (`int`)
        '''
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        while True:
            output = process.stdout.readline().decode().strip()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output)
            time.sleep(0.01)
        return_code = process.poll()
        return return_code

    def get_multiple_items_from_stdout(self, regex: str, string: str, re_flag: re.RegexFlag = re.M):
        '''
            Return seached `list` of string by regex.\n
            "regex" arg has to include a group expression
        '''
        try:
            return [line for line in re.findall(regex, string, re_flag)]
        except Exception:
            self._logger.error('Cannot get multipe items with regex {}.\n{}'.format(regex, traceback.format_exc()))
        return []

    def get_single_item_from_stdout(self, regex: str, string: str, re_flag: re.RegexFlag = 0):
        '''
            "regex" arg has to include a group expression\n
            Return a seached `str` by regex.
        '''
        try:
            if re.search(regex, string, re_flag):
                return re.search(regex, string, re_flag).group(1).strip()
        except Exception:
            self._logger.error('Cannot get a single item with regex {}.\n{}'.format(regex, traceback.format_exc()))
        return 'N/A'

    def get_hw_meta_info(self):
        '''
            Collect all hw meta infomation
            Return `dict` object
        '''
        all_hw_info = {'exception': []}

        # chassis info
        target_component = 'chassis'
        try:
            cmd_result = self.run_command('dmidecode -t 3').stdout.decode().strip()
            component_info = {
                'brand': self.get_single_item_from_stdout(r'Manufacturer:\s*(.*)', cmd_result).strip(),
                'serial_number': self.get_single_item_from_stdout(r'Serial Number:\s*(.*)', cmd_result).strip()
            }
            all_hw_info[target_component] = component_info
        except Exception as e:
            all_hw_info['exception'].append({
                target_component: traceback.format_exc()
            })
            self._logger.error('Cannot collect {} info.\n{}'.format(target_component, traceback.format_exc()))

        # chassis/system info
        target_component = 'system'
        try:
            cmd_result = self.run_command('dmidecode -t 1').stdout.decode().strip()
            component_info = {
                'brand': self.get_single_item_from_stdout(r'Manufacturer:\s*(.*)', cmd_result).strip(),
                'model': self.get_single_item_from_stdout(r'Product Name:\s*(.*)', cmd_result).strip(),
                'serial_number': self.get_single_item_from_stdout(r'Serial Number:\s*(.*)', cmd_result).strip()
            }
            all_hw_info[target_component] = component_info
        except Exception as e:
            all_hw_info['exception'].append({
                target_component: traceback.format_exc()
            })
            self._logger.error('Cannot collect {} info.\n{}'.format(target_component, traceback.format_exc()))

        # cpu info
        target_component = 'cpu'
        try:
            cmd_result = self.run_command('dmidecode -t 4').stdout.decode().strip()
            component_info = {
                'brand': self.get_single_item_from_stdout(r'Manufacturer:\s*(.*)', cmd_result).strip(),
                'model': self.get_single_item_from_stdout(r'Version:\s*(.*)', cmd_result).strip(),
                'core': self.get_single_item_from_stdout(r'Core Count:\s*(.*)', cmd_result).strip(),
                'thread': self.get_single_item_from_stdout(r'Thread Count:\s*(.*)', cmd_result).strip()
            }
            all_hw_info[target_component] = component_info
        except Exception as e:
            all_hw_info['exception'].append({
                target_component: traceback.format_exc()
            })
            self._logger.error('Cannot collect {} info.\n{}'.format(target_component, traceback.format_exc()))

        # mainboard info
        target_component = 'mainboard'
        try:
            cmd_result = self.run_command('dmidecode -t 2').stdout.decode().strip()
            component_info = {
                'brand': self.get_single_item_from_stdout(r'Manufacturer:\s*(.*)', cmd_result).strip(),
                'model': self.get_single_item_from_stdout(r'Product Name:\s*(.*)', cmd_result).strip(),
                'serial_number': self.get_single_item_from_stdout(r'Serial Number:\s*(.*)', cmd_result).strip()
            }
            all_hw_info[target_component] = component_info
        except Exception as e:
            all_hw_info['exception'].append({
                target_component: traceback.format_exc()
            })
            self._logger.error('Cannot collect {} info.\n{}'.format(target_component, traceback.format_exc()))

        # dimmm info
        target_component = 'dimm'
        try:
            cmd_result = self.run_command('dmidecode -t 17 -q').stdout.decode().strip()
            component_info = {}
            for dimm_info in re.split('^\n', cmd_result, flags=re.M):
                if re.search(r'No Module Installed', dimm_info):
                    continue
                component_info.update({
                    self.get_single_item_from_stdout(r'^\s*Locator: (.*)', dimm_info, re.M): {
                        'size': self.get_single_item_from_stdout(r'Size: (.*)', dimm_info),
                        'brand': self.get_single_item_from_stdout(r'Manufacturer:\s*(.*)', dimm_info),
                        'model': self.get_single_item_from_stdout(r'Part Number:\s*(.*)', dimm_info),
                        'serial_number': self.get_single_item_from_stdout(r'Serial Number:\s*(.*)', dimm_info)
                    }
                })
            all_hw_info[target_component] = component_info
        except Exception as e:
            all_hw_info['exception'].append({
                target_component: traceback.format_exc()
            })
            self._logger.error('Cannot collect {} info.\n{}'.format(target_component, traceback.format_exc()))

        # gpu info
        # one of nvidia-smi or nvflash must be available
        target_component = 'gpu'
        try:
            component_info = {}
            gpu_util = None
            if self.run_command('nvflash --list').returncode == 0:
                self._logger.info('nvflash is available.')
                cmd_result = self.run_command('nvflash --list').stdout.decode().strip()
                gpu_pci_list = self.get_multiple_items_from_stdout(r'S:.*,B:(.*),D:(.*),F:.*', cmd_result)
                for gpu_pci in gpu_pci_list:
                    pci_id = '{}:{}'.format(gpu_pci[0], gpu_pci[1])
                    cmd_result = self.run_command(
                        './nvflash --rdobd --pcisegbus={}'.format(pci_id)).stdout.decode().strip()
                    component_info.update({
                        pci_id: {
                            'model': self.get_single_item_from_stdout(r'MarketingName:\s*(.*)', cmd_result).strip(),
                            'serial_number':
                                self.get_single_item_from_stdout(r'BoardSerialNumber:\s*(.*)', cmd_result).strip()
                        }
                    })
                    cmd_result = self.run_command(
                        './nvflash --version --pcisegbus={}:{}'.format(gpu_pci[0], gpu_pci[1])).stdout.decode().strip()
                    component_info[pci_id].update({
                        'vbios': self.get_single_item_from_stdout(r'Version\s*:\s*(.*)', cmd_result).strip(),
                        'inforom': self.get_single_item_from_stdout(r'InfoROM Version\s*:\s*(.*)', cmd_result).strip()
                    })
            elif self.run_command('nvidia-smi --list-gpus').returncode == 0:
                self._logger.info('nvidia-smi is available.')
                cmd_result = self.run_command(
                    'nvidia-smi --query-gpu=name,serial,pci.bus_id,vbios_version,inforom.img,memory.total '
                    '--format=csv,noheader').stdout.decode().strip()
                gpu_info_list = self.get_multiple_items_from_stdout(
                    r'(.*), (.*), 00000000:(.*)\.0, (.*), (.*), (.*)', cmd_result)
                for gpu_info in gpu_info_list:
                    component_info.update({
                        gpu_info[2]: {
                            'model': gpu_info[0],
                            'serial_number': gpu_info[1],
                            'vbios': gpu_info[3],
                            'inforom': gpu_info[4],
                            'memory': gpu_info[5]
                        }
                    })
            else:
                raise Exception('One of nvidia-smi or nvflash must be available.')
            all_hw_info[target_component] = component_info
        except Exception as e:
            all_hw_info['exception'].append({
                target_component: traceback.format_exc()
            })
            self._logger.error('Cannot collect {} info.\n{}'.format(target_component, traceback.format_exc()))

        # psu info
        target_component = 'psu'
        try:
            cmd_result = self.run_command('dmidecode -t 39 -q').stdout.decode().strip()
            component_info = {}
            for dimm_info in re.split('^\n', cmd_result, flags=re.M):
                component_info.update({
                    self.get_single_item_from_stdout(r'Location: (.*)', dimm_info): {
                        'brand': self.get_single_item_from_stdout(r'Manufacturer:\s*(.*)', dimm_info),
                        'model': self.get_single_item_from_stdout(r'Name:\s*(.*)', dimm_info),
                        'power': self.get_single_item_from_stdout(r'Max Power Capacity:\s*(.*)', dimm_info),
                        'serial_number': self.get_single_item_from_stdout(r'Serial Number:\s*(.*)', dimm_info)
                    }
                })
            all_hw_info[target_component] = component_info
        except Exception as e:
            all_hw_info['exception'].append({
                target_component: traceback.format_exc()
            })
            self._logger.error('Cannot collect {} info.\n{}'.format(target_component, traceback.format_exc()))

        # nic info
        # lshw package required
        target_component = 'nic'
        try:
            if self.run_command('lshw -version').returncode != 0:
                raise Exception('lshw package required to collect NIC info.')
            cmd_result = self.run_command('lshw -c network').stdout.decode().strip()
            component_info = {}
            for nic_info in re.split(r'\*\-network:.*', cmd_result)[1:]:
                if re.search(r'virtual', self.get_single_item_from_stdout(r'product: (.*)', nic_info), re.I):
                    continue
                nic_name = self.get_single_item_from_stdout(r'logical name: (.*)', nic_info)
                pci_id = self.get_single_item_from_stdout(r'bus info: pci@0000:(.*)', nic_info)
                component_info.update({
                    nic_name: {
                        'brand': self.get_single_item_from_stdout(r'vendor:\s*(.*)', nic_info),
                        'model': self.get_single_item_from_stdout(r'product:\s*(.*)', nic_info),
                        'mac': self.get_single_item_from_stdout(r'serial:\s*(.*)', nic_info),
                        'pci_id': pci_id,
                        'firmware': self.get_single_item_from_stdout(r'firmware=(\S*)', nic_info)
                    }
                })
                cmd_result = self.run_command('lspci -vv -s {}'.format(pci_id)).stdout.decode().strip()
                component_info[nic_name]['serial_number'] = self.get_single_item_from_stdout(
                    r'Serial number:\s*(.*)', cmd_result)
                if self.get_single_item_from_stdout(r'Part number:\s*(.*)', cmd_result) != 'N/A':
                    component_info[nic_name]['model'] = self.get_single_item_from_stdout(
                        r'Part number: (.*)', cmd_result)
                cmd_result = self.run_command('ethtool -m {}'.format(nic_name)).stdout.decode().strip()
                if self.get_single_item_from_stdout(r'Vendor name\s*:\s*(.*)', cmd_result) != 'N/A':
                    component_info[nic_name]['transceiver_brand'] = self.get_single_item_from_stdout(
                        r'Vendor name\s*:\s*(.*)', cmd_result)
                    component_info[nic_name]['transceiver_model'] = self.get_single_item_from_stdout(
                        r'Vendor PN\s*:\s*(.*)', cmd_result)
                    component_info[nic_name]['transceiver_type'] = self.get_single_item_from_stdout(
                        r'Transceiver type\s*:\s*(.*)', cmd_result)
            all_hw_info[target_component] = component_info
        except Exception as e:
            all_hw_info['exception'].append({
                target_component: traceback.format_exc()
            })
            self._logger.error('Cannot collect {} info.\n{}'.format(target_component, traceback.format_exc()))

        return all_hw_info


if __name__ == '__main__':
    hw_info_collector = HWInfoCollector()
    hw_info = hw_info_collector.get_hw_meta_info()
    print(json.dumps(hw_info, indent=2))
