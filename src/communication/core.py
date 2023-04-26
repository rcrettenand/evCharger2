import logging
import time
from abc import ABC

import version
from communication.com_protocol import ComProtocol


class Core(ComProtocol, ABC):
    log = logging.getLogger(__name__)

    def __init__(self, settings):
        super(Core, self).__init__(settings['module-name'])

        from app.gateway import Gateway
        self._gw_name = Gateway().gateway_config['gateway']['name']
        self._description = Gateway().gateway_config['gateway']['description']

    def read_values(self, comm_parameters, attribute_list):
        assert False, 'read_values method not implemented'
        return 0

    def is_online(self):
        return True  # core is always online !

    def read_value(self, comm_parameters, attribute):
        self.log.debug(f'reading {attribute["name"]}')
        command = f'self.{attribute["method"]}()'
        return eval(command)

    def write_values(self, comm_parameters, attribute_list, values_list):
        assert False, 'write_values method not implemented'

    def write_value(self, comm_parameters, attribute, value):
        assert False, 'write_value method not implemented'

    def seconds(self):
        from src.app.gateway import Gateway
        start_time = Gateway().start_time

        elapsed_time = time.time() - start_time

        return int(elapsed_time) % 60

    def minutes(self):
        from src.app.gateway import Gateway
        start_time = Gateway().start_time

        elapsed_time = time.time() - start_time

        return (int(elapsed_time) / 60) % 60

    def hours(self):
        from src.app.gateway import Gateway
        start_time = Gateway().start_time

        elapsed_time = time.time() - start_time

        return (int(elapsed_time) / 3600) % 24

    def days(self):
        from src.app.gateway import Gateway
        start_time = Gateway().start_time

        elapsed_time = time.time() - start_time

        return int(elapsed_time) / 86400

    def gw_name(self):
        return self._gw_name

    def description(self):
        return self._description

    def version(self):
        return version.__version__

    def online_nbr(self):
        from src.app.gateway import Gateway

        online_protocols = [protocol for protocol in Gateway().protocols if protocol.is_online()]

        return len(online_protocols)

    def protocol_nbr(self):
        from src.app.gateway import Gateway

        return len(Gateway().protocols)

    def error_protocol_names(self):
        from src.app.gateway import Gateway

        offline_protocols_name = [protocol.name for protocol in Gateway().protocols if not protocol.is_online()]

        result = ', '.join(offline_protocols_name)

        if len(offline_protocols_name) == 0:
            result = '-'

        return result
