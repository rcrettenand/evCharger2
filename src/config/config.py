# -*- coding: utf-8 -*-
import logging
import os
import sys

import yaml
import tarfile

# Settings folder name and path
SETTINGS_BASE_PATH = "../settings"

GATEWAY_CONFIG_DIR = "gateway-config"
DEVICE_MODEL_DIR = "device-model"
MAPPING_DIR = "mapping"
CLOUDIO_MODEL_DIR = "cloudio/data-model"
CLOUDIO_PROPERTIES_DIR = "cloudio"

# env var names
GATEWAY_CONFIG_ENV_VAR = 'GATEWAY_CONFIG'

IP_ADDRESS_ENV_VAR = 'IPADDR'

ENDPOINT_NAME_ENV_VAR = 'ENDPOINT_NAME'

CERTIFICATE_FILE_ENV_VAR = 'CERTIFICATE_FILE'
HOST_URI_ENV_VAR = 'HOST_URI'  # only when CERTIFICATE_FILE_ENV_VAR is used
SSL_VERSION_ENV_VAR = 'SSL_VERSION'  # only when CERTIFICATE_FILE_ENV_VAR is used

# logging
log = logging.getLogger(__name__)


def get_gateway_config(filepath):
    """get gateway config file and parse it
        * replace all ip addresses by the IPADDR env variable if it exists
    """

    try:
        with open(filepath) as f:
            gateway_config = yaml.load(f, Loader=yaml.FullLoader)  # yaml parsing
    except:
        log.error('Gateway config file not found')
        sys.exit(-1)

    # IPADDR env variable replacement
    if IP_ADDRESS_ENV_VAR in os.environ and os.environ[IP_ADDRESS_ENV_VAR]:
        ip_addr = os.environ[IP_ADDRESS_ENV_VAR]

        for protocol in gateway_config['comm-protocol']:
            if 'ip' in protocol:
                protocol['ip'] = ip_addr
        log.info(f'[ENV] change ip to : {ip_addr}')

    # TODO : check if error in file

    return gateway_config


def get_mapping(filepath):
    """get mapping config file and parse it"""
    with open(filepath) as f:
        mapping = yaml.load(f, Loader=yaml.FullLoader)  # yaml parsing

    # TODO : check if error in file

    return mapping


def get_device_description(filepath):
    """get device description file and parse it"""
    with open(filepath) as f:
        device_description = yaml.load(f, Loader=yaml.FullLoader)  # yaml parsing

    # TODO : check if error in file

    return device_description


def get_cloudio_properties(filepath):
    with open(filepath) as f:
        cloudio_properties = yaml.load(f, Loader=yaml.FullLoader)  # yaml parsing

    # cloudio properties (certificates informations) env variable replacement
    if CERTIFICATE_FILE_ENV_VAR in os.environ and os.environ[CERTIFICATE_FILE_ENV_VAR]:
        certificate_file = os.environ[CERTIFICATE_FILE_ENV_VAR]

        assert certificate_file.endswith('.tar.gz'), 'CERTIFICATE_FILE not ending by .tar.gz'

        log.info(f'[ENV] import certificate file : {certificate_file}')

        # set default properties
        cloudio_properties['ch.hevs.cloudio.endpoint.hostUri'] = 'vleiot.hevs.ch'
        cloudio_properties['username'] = None
        cloudio_properties['password'] = None
        cloudio_properties['ch.hevs.cloudio.endpoint.ssl.version'] = 'tlsv1.2'
        cloudio_properties['ch.hevs.cloudio.endpoint.persistence'] = 'memory'

        # override if env var is set
        if HOST_URI_ENV_VAR in os.environ and os.environ[HOST_URI_ENV_VAR]:
            cloudio_properties['ch.hevs.cloudio.endpoint.hostUri'] = os.environ[HOST_URI_ENV_VAR]
            log.info(f'[ENV] change HOST_URI : {os.environ[HOST_URI_ENV_VAR]}')

        if SSL_VERSION_ENV_VAR in os.environ and os.environ[SSL_VERSION_ENV_VAR]:
            cloudio_properties['ch.hevs.cloudio.endpoint.hostUri'] = os.environ[SSL_VERSION_ENV_VAR]
            log.info(f'[ENV] change SSL_VERSION : {os.environ[SSL_VERSION_ENV_VAR]}')

        # load information from tar.gz file

        # erase temp directory if existing (for dev)
        if os.path.isdir('../../../temp'):
            import shutil
            shutil.rmtree('../../../temp/')

        # extract and copy content to temp directory
        try:
            tar = tarfile.open(f'../../../{certificate_file}', "r:gz")
        except:
            log.error('Certificat file not found')
            sys.exit(-1)
        tar.extractall('../../../temp/')
        tar.close()

        # from certs file
        # search for the right uuid => the name of the client certificate without "-key"

        arr = os.listdir('../../../temp/Clients/')

        uuid = None

        for filename in arr:
            if filename.endswith('-key.pem'):
                uuid = filename[:-8]

        assert uuid is not None, 'no -key.pem file in certificate !'

        cloudio_properties['ch.hevs.cloudio.endpoint.ssl.authorityCert'] = f'../../../temp/Authority/ca-cert.pem'
        cloudio_properties['ch.hevs.cloudio.endpoint.ssl.clientCert'] = f'../../../temp/Clients/{uuid}-cert.pem'
        cloudio_properties['ch.hevs.cloudio.endpoint.ssl.clientKey'] = f'../../../temp/Clients/{uuid}-key.pem'

        cloudio_properties['uuid'] = uuid

    # override endpoint name
    if ENDPOINT_NAME_ENV_VAR in os.environ and os.environ[ENDPOINT_NAME_ENV_VAR]:
        cloudio_properties['uuid'] = os.environ[ENDPOINT_NAME_ENV_VAR]
        log.info(f'[ENV] overriding endpoint name : {cloudio_properties["uuid"]}')

    # TODO : check if error in file

    return cloudio_properties
