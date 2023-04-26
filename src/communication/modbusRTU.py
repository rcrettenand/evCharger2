import logging
from abc import ABC

from pymodbus.client.sync import ModbusSerialClient
from pymodbus.exceptions import ModbusIOException, ConnectionException
from pymodbus.transaction import ModbusSocketFramer, ModbusTlsFramer, ModbusRtuFramer, ModbusAsciiFramer, \
    ModbusBinaryFramer

from communication.com_protocol import ComProtocol, ComProtocolError, \
    ComProtocolValueError, ComProtocolConnectionError


class ModbusRTU(ComProtocol, ABC):
    log = logging.getLogger(__name__)

    def __init__(self, settings):
        super(ModbusRTU, self).__init__(settings['module-name'])

        # SETTINGS

        # needed - config: [
        #     port
        # ]
        #
        # optional - config: [
        #   stopbits, bytesize, parity, baudrate, method
        #
        #
        #

        # self.name = settings['module-name']

        port = settings['port']
        stopbits = settings.get('stopbits', 1)
        bytesize = settings.get('bytesize', 8)
        parity = settings.get('parity', 'N')
        baudrate = settings.get('baudrate', 9600)

        # framer = ModbusSocketFramer
        framer = ModbusRTU.get_framer(settings['framer'])
        timeout = float(settings['timeout']) if 'timeout' in settings else 0.2
        self.log.info(f'port : {port} stop : {stopbits} parity: {parity}  baudrate: {baudrate}')
        self._client = ModbusSerialClient(method=framer, port=port, stopbits=stopbits, bytesize=bytesize, parity=parity, baudrate=baudrate, timeout=timeout)
        self.log.info(f'{self.name} modbus connection to {port} and with {framer}')
        self.log.info(f'{self._client.connect()}')
        if self._client.connect():
            self.log.info(f'{self.name} modbus connected')
        else:
            self.log.info(f'{self.name} modbus failed to connect')

        self._last = False

    def close(self):
        self._client.close()

    @staticmethod
    def get_framer(str_framer):
        # available framer in serial pymodbus
        # "ModbusSocketFramer", "ModbusRtuFramer",
        # "ModbusAsciiFramer", "ModbusBinaryFramer",
        if str_framer == 'ModbusSocketFramer':
            return 'socket'
        elif str_framer == 'ModbusRtuFramer':
            return 'rtu'
        elif str_framer == 'ModbusAsciiFramer':
            return 'ascii'
        elif str_framer == 'ModbusBinaryFramer':
            return 'binary'
        assert False, 'not a supported Modbus Framer !'

    def write(self):
        # write coil => only boolean values
        self._last = not self._last

        self._client.write_coil(1, self._last)

    def write_holding(self):
        # write holding register => int16

        response = self._client.read_holding_registers(1)

        last_value = response.registers[0]

        self._client.write_register(1, last_value + 1)

    @staticmethod
    def get_coil_write_value(value, length):

        value_tab = []
        for i in reversed(range(0, length)):
            value_tab.append(((value >> i) & 0x01) == 1)

        return value_tab

    @staticmethod
    def get_register_write_value(value, length):

        value_tab = []
        for i in reversed(range(0, length)):
            value_tab.append((value >> (i * 16)) & 0xFFFF)
        return value_tab

    @staticmethod
    def get_coil_response(read_response):

        final_value = 0
        index = 0
        for bit in read_response.bits:
            final_value += bit << index
            index += 1

        return final_value

    @staticmethod
    def get_register_response(read_response):

        final_value = 0
        index = 16 * (len(read_response.registers) - 1)

        # for register in read_response.registers:
        #     final_value += register << index
        #     index += 16

        for register in read_response.registers:
            final_value += register << index
            index -= 16

        return final_value

    def read(self, address, length, register_type, unit=None):

        if unit is None:
            unit = 0  # default value

        # type : co, di, ir, hr
        try:
            if register_type == 'co':
                return ModbusRTU.get_coil_response(self._client.read_coils(address, length, unit=unit))
            elif register_type == 'di':
                return ModbusRTU.get_coil_response(self._client.read_discrete_inputs(address, length, unit=unit))
            elif register_type == 'ir':
                return ModbusRTU.get_register_response(self._client.read_input_registers(address, length, unit=unit))
            elif register_type == 'hr':
                return ModbusRTU.get_register_response(self._client.read_holding_registers(address, length, unit=unit))
        except ConnectionException:
            raise ComProtocolConnectionError('impossible to reconnect modbusRTU')
        except AttributeError:
            self._client.close()
            raise ComProtocolValueError('problem with modbusRTU transaction')
        else:
            assert False, f'{register_type} is not a register type'

    def write(self, value, address, length, register_type, unit=None):

        if unit is None:
            unit = 0  # default value

        # type : co, di, ir, hr
        try:
            if register_type == 'co':
                value_tab = self.get_coil_write_value(value, length)
                return self._client.write_coils(address, value_tab, unit=unit)
            elif register_type == 'di':
                raise ComProtocolValueError('di type is NOT writtable')
            elif register_type == 'ir':
                raise ComProtocolValueError('ir type is NOT writtable')
            elif register_type == 'hr':
                value_tab = self.get_register_write_value(value, length)
                return self._client.write_registers(address, value_tab, unit=unit)
        except ConnectionException:
            raise ComProtocolConnectionError('impossible to reconnect modbusRTU')
        except AttributeError:
            self._client.close()
            raise ComProtocolValueError('problem with modbusRTU transaction')
        else:
            assert False, f'{register_type} is not a register type'

    def is_online(self):
        return self._client.is_socket_open()

    def read_values(self, comm_parameters, attribute_list):

        result = {}


        for index in range(0, len(attribute_list)):
        # for attribute in attribute_list:
            result[index] = (self.read_value(comm_parameters, attribute_list[index]))

        return result

    def read_value(self, comm_parameters, attribute):
        # - {name: minutes, addr: 1000, length: 2, type: hr}
        self.log.info(f'Here when read = : { attribute}')
        # offset support
        if 'offset' in comm_parameters:
            offset = comm_parameters['offset']
        else:
            offset = 0
        address = attribute['addr'] + offset
        length = attribute['length']
        register_type = attribute['type']
        if 'unit' in comm_parameters:
            unit = attribute['unit']
        else:
            unit = 1
        self.log.debug(f'read value : {attribute}')

        if 'unit-identifier' in comm_parameters:
            val = self.read(address, length, register_type, comm_parameters['unit-identifier'])
            if val == 0 and address == 14:
                self.log.info(f'VALUE = 0')
            else:
                return val

        else:
            return self.read(address, length, register_type, unit)

    def write_values(self, comm_parameters, attribute_list, values_list):
        assert False, 'write_values method not implemented'

    def write_value(self, comm_parameters, attribute, value):
        # - {name: minutes, addr: 1000, length: 2, type: hr}
        address = attribute['addr']
        length = attribute['length']
        register_type = attribute['type']
        if 'unit' in comm_parameters:
            unit = attribute['unit']
        else:
            unit = 1

        self.log.debug(f'write value : {attribute}')

        if 'unit-identifier' in comm_parameters:
            return self.write(value, address, length, register_type, comm_parameters['unit-identifier'])
        else:
            return self.write(value, address, length, register_type, unit)
