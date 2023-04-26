from abc import ABC, abstractmethod


# define Python user-defined exceptions
class ComProtocolError(Exception):
    """ComProtocolError class for protocol exceptions"""

    def __init__(self, message='Error from a protocol'):
        self.message = message
        super().__init__(self.message)


class ComProtocolConnectionError(ComProtocolError):
    """ComProtocolError class for protocol exceptions"""

    def __init__(self, message='Error from a protocol'):
        self.message = message
        super().__init__(self.message)


class ComProtocolValueError(ComProtocolError):
    """ComProtocolError class for protocol exceptions"""

    def __init__(self, message='Error from a protocol'):
        self.message = message
        super().__init__(self.message)


class ComProtocol(ABC):
    def __init__(self, name):
        super().__init__()

        self._name = name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, x):
        self._name = x

    @abstractmethod
    def is_online(self):
        assert False, 'is_online method not implemented'

    @abstractmethod
    def read_values(self, comm_parameters, attribute_list):
        assert False, 'read_values method not implemented'

    @abstractmethod
    def read_value(self, comm_parameters, attribute):
        assert False, 'read_value method not implemented'

    @abstractmethod
    def write_values(self, comm_parameters, attribute_list, values_list):
        assert False, 'write_values method not implemented'

    @abstractmethod
    def write_value(self, comm_parameters, attribute, value):
        assert False, 'write_value method not implemented'
