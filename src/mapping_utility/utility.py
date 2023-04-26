import struct


def to_unsigned(value, nb_bit):
    if value < 0:
        value = value + (1 << nb_bit)
    return value


def to_signed(value, nb_bit):
    """compute the 2's complement of int value val"""
    if (value & (1 << (nb_bit - 1))) != 0:  # if sign bit is set e.g., 8bit: 128-255
        value = value - (1 << nb_bit)  # compute negative value
    return value  # return positive value as is


def dec_to_ip(value):
    return '.'.join([str(value >> (i << 3) & 0xFF) for i in range(4)[::-1]])

def ip_to_dec(value):
    parts = value.split('.')
    soluce = (int(parts[0]) << 24) + (int(parts[1]) << 16) + (int(parts[2]) << 8) + int(parts[3])
    return soluce


def modbus_to_string(value):
    hex_string = hex(value)[2:]

    hex_tab = [hex_string[index:index + 2] for index in range(0, len(hex_string), 2)]

    char_tab = [chr(int(char_hex, 16)) for char_hex in hex_tab]

    return_val = ''.join(char_tab)

    # print(return_val)

    return return_val


# with IEEE 754 Single-precision floating-point norm
def to_float32(value):
    # Convert value from a 32 bit float modbus register to a float
    s = struct.pack('>L', value)
    return struct.unpack('>f', s)[0]


# with IEEE 754 Single-precision floating-point norm
def from_float32(value):
    # Convert float to a 32 bit float modbus register value
    s = struct.pack('>f', value)
    return struct.unpack('>L', s)[0]

