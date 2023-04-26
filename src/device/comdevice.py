import logging


class DeviceModelErrorException(Exception):
    """ComProtocolError class for protocol exceptions"""

    def __init__(self, message='Error with a device com error'):
        self.message = message
        super().__init__(self.message)


class ComDevice:
    """ComDevice class : one device model => how to com to the device
        attributes:
        * comm_parameters : config for the corresponding com protocol (config only for this device e.g. device id)
        * protocol : protocol to use with this device for reading or writing
        *
        *
        *
    """
    log = logging.getLogger(__name__)

    def __init__(self, device_description, comm_parameters):

        # init attributes

        self.comm_parameters = comm_parameters

        if device_description['type'] == 'device_description':
            self.device_description = device_description

            self.version = self.device_description['version']
            self.name = self.device_description['name']
            self.fullname = self.device_description['fullname']
            self.communication = self.device_description['communication']
            self.data = self.device_description['data']

            self.protocol = None

    def add_protocol(self, protocol):
        """Adding protocol for writing and reading the corresponding device"""
        self.protocol = protocol

    def read_value(self, value_name):
        """Read value from the device"""

        for attribute in self.data:

            assert attribute is not None, 'One attribute of the device model is equal to None, the file is not valid !'

            if attribute['name'] == value_name:
                return self.protocol.read_value(self.comm_parameters, attribute)

        # mapping error if no attribute finded
        raise DeviceModelErrorException(f'{value_name} not found in {self.name} device model file')

    def read_values(self, value_name_list):
        """Read multiple values at the same time"""

        output = []

        # todo : better support of multiple reading!

        for value_name in value_name_list:
            output.append(
                self.read_value(value_name)
            )

        return output

    def write_value(self, value_name, value):
        """Write value to the device"""

        for attribute in self.data:
            if attribute['name'] == value_name:
                return self.protocol.write_value(self.comm_parameters, attribute, value)

        # mapping error if no attribute finded
        raise DeviceModelErrorException(f'{value_name} not found in {self.name} device model file')

    def write_values(self, value_name_list, value_list):
        """Write multiple values at the same time"""

        # todo : better support of multiple writing!

        return self.protocol.write_values(self.comm_parameters, value_name_list, value_list)
