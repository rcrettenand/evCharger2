import logging
import time

from app.controller import Controller
from cloud.connector import Connector
from communication.protocol_creator import create_protocol
from config.config import SETTINGS_BASE_PATH, CLOUDIO_MODEL_DIR
from device.device import Device


# Singleton metaclass for singleton pattern
class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


# Gateway CLASS (singleton)
class Gateway(metaclass=Singleton):
    """Gateway class : representing the whole gateway => creating all instances and connecting them
        attributes:
        * devices : list of devices of the gateway
        * gateway-config : gateway config file content
        * protocols : list of protocols instances created by the gateway
        * controller : active part of the gateway (reading/writing)
    """
    log = logging.getLogger(__name__)

    def __init__(self):
        # create class attributes
        self.devices = []
        self.gateway_config = ''
        self.protocols = []
        self.controller = None
        self.start_time = 0

    def initialize(self, gateway_config):

        self.start_time = time.time()

        self.gateway_config = gateway_config

        # creating endpoint
        the_connector = Connector(self.gateway_config)
        self.cloudio_endpoint = the_connector.endpoint

        # Wait until connected to cloud.iO
        self.log.info('Waiting to connect endpoint to cloud.iO...')
        while not self.cloudio_endpoint.is_online():
            time.sleep(0.2)

        self.log.info('Creating cloud.iO model...')

        # read the files for the gateway config file
        node_content = ''  # cloudio model XML concatenated

        for device in gateway_config['devices']:
            file = open(f'{SETTINGS_BASE_PATH}/{CLOUDIO_MODEL_DIR}/{device["cloudio-model"]}.xml')

            # add name of the node from the gateway config file
            node_content += file.read().replace('<node>', f'<node name="{device["name"]}">')

        # create model from the different files !
        the_connector.create_model(node_content)

        # create different com protocol
        for com_protocol in gateway_config['comm-protocol']:
            self.protocols.append(create_protocol(com_protocol))

        # create device and add it to
        for device_config in gateway_config['devices']:
            d = Device(device_config, self.cloudio_endpoint, self.protocols)
            self.devices.append(d)

        self.controller = Controller(self.devices)

        self.log.info('Setup finished !')

        # controller
        self.controller.run()
