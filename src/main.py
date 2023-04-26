import logging
import os
import sys

from app.gateway import Gateway
from config.config import get_gateway_config, SETTINGS_BASE_PATH, \
                                                             GATEWAY_CONFIG_DIR, GATEWAY_CONFIG_ENV_VAR
for path in sys.path:
    print(path)

os.environ['GATEWAY_CONFIG'] = "green_motion_config"
# logging format
logging.basicConfig(format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger().setLevel(logging.INFO)


def main():
    log = logging.getLogger(__name__)

    # read env var (GATEWAY_CONFIG) for gateway config file => this env var is mandatory !
    if GATEWAY_CONFIG_ENV_VAR in os.environ and os.environ[GATEWAY_CONFIG_ENV_VAR]:
        gateway_config = os.environ[GATEWAY_CONFIG_ENV_VAR]

        gateway_config_filename = gateway_config

        log.info(f'[ENV] Use gateway-config : {gateway_config}')
    else:
        assert False, f'{GATEWAY_CONFIG_ENV_VAR} is not set in ENV variables'

    # get gateway config from yaml file
    gateway_config_path = f'{SETTINGS_BASE_PATH}/{GATEWAY_CONFIG_DIR}/{gateway_config_filename}.yaml'
    gateway_config = get_gateway_config(gateway_config_path)

    # create gateway singleton and initialize it with the gateway-config file content
    Gateway().initialize(gateway_config)


def print_version():
    """print version and git hash"""
    import version
    app_name = 'modular-cloudio-gateway'
    logging.getLogger(app_name).setLevel(logging.INFO)
    logging.getLogger(app_name).info(f'version: {version.__version__}, git hash: {version.githash()}')


if __name__ == '__main__':
    print_version()
    main()
