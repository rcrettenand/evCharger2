import asyncio
import logging

import cloudio
from cloudio.glue import Model2CloudConnector
from cloudio.glue import cloudio_attribute

from config.config import get_mapping, SETTINGS_BASE_PATH, MAPPING_DIR, \
    DEVICE_MODEL_DIR, get_device_description
from device.comdevice import ComDevice
from device.mappingdevice import MappingDevice

# logging.getLogger(__name__).setLevel(logging.INFO)


class Device:
    """Device class : one device
        attributes:
        * device_config : config from the gateway config file representing this device
        * node_name : name of the corresponding node
        *
        *
        *
    """
    log = logging.getLogger(__name__)

    def __init__(self, device_config, endpoint, protocol_list):
        self.device_config = device_config

        self.node_name = self.device_config['name']
        self.device_model_filename = self.device_config['device-model']
        self.comm_protocol = self.device_config['comm-protocol']
        self.mapping_filename = self.device_config['mapping']
        self.cloudio_model_filename = self.device_config['cloudio-model']

        self.comm_parameters = dict()

        # get extra comm parameters
        if 'comm-parameters' in self.device_config:
            self.comm_parameters = self.device_config['comm-parameters']

        # create the corresponding communication device model and add the right protocol
        device_model_path = f'{SETTINGS_BASE_PATH}/{DEVICE_MODEL_DIR}/{self.device_model_filename}.yaml'
        self.comm_device = ComDevice(get_device_description(device_model_path), self.comm_parameters)
        self.comm_device.add_protocol(self.get_protocol(protocol_list, self.comm_protocol))

        # create mapping device
        mapping_path = f'{SETTINGS_BASE_PATH}/{MAPPING_DIR}/{self.mapping_filename}.yaml'
        self.mapping_device = MappingDevice(self, self.node_name, get_mapping(mapping_path))
        self.mapping_device.initialize(endpoint)

    def get_protocol(self, protocol_list, protocol_name):
        """return the protocol needed if it is in the protocol list"""
        for protocol in protocol_list:
            if protocol.name == protocol_name:
                return protocol
        assert False, f'protocol {protocol_name} for device {self.node_name} not found'

