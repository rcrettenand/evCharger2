from communication.modbusTCP import ModbusTCP
from communication.modbusRTU import ModbusRTU
from communication.core import Core
from communication.defaultMode  import DefaultMode


def create_protocol(settings):
    protocol_type = settings['type']

    if protocol_type == 'core':
        return Core(settings)
    elif protocol_type == 'modbusTCP':
        return ModbusTCP(settings)
    elif protocol_type == 'modbusRTU':
        return ModbusRTU(settings)
    elif protocol_type == 'defaultMode':
        return DefaultMode(settings)
    # elif protocol_type == 'CAN':
    #   return CAN(settings)

    assert False, f'{protocol_type} is not a supported protocol'
