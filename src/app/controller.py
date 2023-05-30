import logging
import sys
import time
import sched
import traceback
import paho.mqtt.client as mqtt

from communication.com_protocol import ComProtocolError, ComProtocolConnectionError,\
    ComProtocolValueError
from device.comdevice import DeviceModelErrorException
from cloudio.common.mqtt.helpers import MqttAsyncClient
class Controller:
    """Controller class : active part of the gateway (reading/writing) run by a scheduler
        attributes:
        * devices : list of devices of the gateway
        * s : the scheduler
        * protocols : list of protocols instances created by the gateway
        * controller : active part of the gateway (reading/writing)
        *
    """
    log = logging.getLogger(__name__)

    def __init__(self, devices, endpoint):
        self.devices = devices
        self.endpoint = endpoint
        self.s = sched.scheduler(time.monotonic, time.sleep)
        # force update all device
        for device in self.devices:
            self.force_update_all(device.mapping_device.force_update_rate, device)
        # schedule all mapped attributes in groups
        self.devices_update = []

        for device in self.devices:
            device_update = self.separate_update_rate(device.mapping_device.map,
                                                      device.mapping_device.refresh_rate)
            self.devices_update.append(device_update)

            device.mapping_device.set_add_to_sched_callback(self.add_to_sched)

            for update_group in device_update:
                self.s.enter(update_group, 2, self.update, argument=(update_group, device, device_update[update_group]))

            self.s.enter(1,2,self.test_connection)

    def update(self, update_rate, device, attribute_list):
        self.s.enter(update_rate, 2, self.update, argument=(update_rate, device, attribute_list))
        self.log.info(f"Reading from scheduler every {update_rate}s {len(attribute_list)} attributes")

        # last_val = time.perf_counter_ns()
        for attribute in attribute_list:
            if type(attribute) == list:
                try:
                    value = device.comm_device.read_values(attribute)
                    self.log.info(f'This value = {value}')
                except ComProtocolConnectionError as e:
                    self.log.warning(f'Connection error : {e}')
                    return
                except ComProtocolValueError as e:
                    self.log.warning(f'Value error : {e} for {attribute}')
                except DeviceModelErrorException as e:
                    self.log.warning(f'Device Model error : {e} for {attribute}')
                else:
                    # device.mapping_device.update_parameter(attribute, value, force=True)
                    device.mapping_device.update_parameter(attribute, value)
            else:
                try:
                    value = device.comm_device.read_value(attribute)
                except ComProtocolConnectionError as e:
                    self.log.warning(f'Connection error : {e}')
                    return
                except ComProtocolValueError as e:
                    self.log.warning(f'Value error : {e} for {attribute}')
                except DeviceModelErrorException as e:
                    self.log.warning(f'Device Model error : {e} for {attribute}')
                else:
                    # device.mapping_device.update_parameter(attribute, value, force=True)
                    device.mapping_device.update_parameter(attribute, value)

        # now = time.perf_counter_ns()

        # self.log.debug(f"time elapsed for {len(attribute_list)} attributes : {(now-last_val) / 1000000000}")

    def add_to_sched(self, device, attribute, value):
        """ add to scheduler the writing command"""
        self.s.enter(0, 1, self.write_attribute, argument=(device, attribute, value))

    def write_attribute(self, device, attribute, value):
        """ executing when an attribute has to be writted from the cloud """

        self.log.debug( f'trying to set {attribute} to {value}')
        try:
            device.comm_device.write_value(attribute, value)
            value_read = device.comm_device.read_value(attribute)
            device.mapping_device.update_parameter(attribute, value_read, force=True)
            if value_read == value:
                self.log.info(f'{attribute} set to {value}')
            else:
                self.log.warning(f'value writted and value readed are not the same ! for {attribute} : {value} != {value_read}')
        except:
            exc_type, exc_value, exc_tb = sys.exc_info()
            self.log.error(f'failed writing of {attribute} : {exc_value}')

    def force_update_all(self, update_rate, device):
        self.s.enter(update_rate, 1, self.force_update_all, argument=(update_rate, device))

        self.log.info(f"Force updating all attributes every {update_rate}s")

        for attribute in device.mapping_device.map:
            # print(f'Attribute: {attribute}')
            if type(attribute['comm-name']) == list:
                try:
                    value = device.comm_device.read_values(attribute['comm-name'])
                except ComProtocolConnectionError as e:
                    self.log.warning(f'Connection error : {e}')
                    return
                except ComProtocolValueError as e:
                    self.log.warning(f'Value error : {e} for {attribute["comm-name"]}')
                except DeviceModelErrorException as e:
                    self.log.warning(f'Device Model error : {e} for {attribute["comm-name"]}')
                else:
                    device.mapping_device.update_parameter(attribute['comm-name'], value, True)
            else:
                try:
                    value = device.comm_device.read_value(attribute['comm-name'])

                except ComProtocolConnectionError as e:
                    self.log.warning(f'Connection error : {e}')
                    return
                except ComProtocolValueError as e:
                    self.log.warning(f'Value error : {e} for {attribute["comm-name"]}')
                except DeviceModelErrorException as e:
                    self.log.warning(f'Device Model error : {e} for {attribute["comm-name"]}')
                else:
                    device.mapping_device.update_parameter(attribute['comm-name'], value, True)

    def separate_update_rate(self, mapping_list, refresh_rate):

        temp = {}
        result = {}

        # - {cloudio-name: DC-test.current, comm-name: max-rms-current-L1, type: int, permission: R,refresh-rate: fast}

        for attribute in mapping_list:
            if attribute['refresh-rate'] not in temp:
                temp[attribute['refresh-rate']] = [attribute['comm-name'], ]
            else:
                temp[attribute['refresh-rate']].append(attribute['comm-name'])

        # replace rate by real value (seconds)

        # TODO don't replace => only one key by dict !
        for update_rate in temp:
            result[refresh_rate[update_rate]] = temp[update_rate]

        return result

    def test_minutes(self):
        self.s.enter(2, 1, self.test_minutes)
        self.log.info("Reading from controller and scheduler")
        value = self.devices[1].comm_device.read_value('max-rms-current-L1')
        # print(value)
        self.devices[1].mapping_device.update_parameter('max-rms-current-L1', value)


    # Threads that ensure the connection between the Pi and the Cloud.
    def test_connection(self):
        while True:
            if not self.endpoint.is_online():
                self.log.info('WRITING DEFAULT VALUES')
            time.sleep(10)

    def run(self):
        self.log.info('Running')
        while True:
            # print("HELLO")
            if not self.endpoint.is_online():
                self.log.info('TEST WORKS')
            self.s.run(blocking=True)





