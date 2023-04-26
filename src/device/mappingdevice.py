import asyncio
import json
import logging
import traceback

import cloudio.endpoint
from cloudio.glue import Model2CloudConnector

from mapping_utility.utility import *  # mandatory for eval function (do not del !)

class MappingDevice(Model2CloudConnector):
    """MappingDevice class : mapping between cloudio representation and device representation
        attributes:
        * device : reference to the device object
        * node_name : name of the corresponding node
        * add_to_sched_callback : callback function for updating a value from the cloud to cloud
        * attributes : dict of device attributes and corresponding values
        *
    """

    log = logging.getLogger(__name__)

    def __init__(self, device, node_name, mapping):
        super(MappingDevice, self).__init__()

        # init class attributes
        self.device = device

        self.CLOUDIO_NODE_NAME = node_name
        self.CLOUDIO_NODE_TOPIC_PREFIX = self.CLOUDIO_NODE_NAME + '.'

        self.add_to_sched_callback = None

        if mapping['type'] == 'mapping':
            self.mapping = mapping

            self.version = self.mapping['version']
            self.name = self.mapping['name']
            self.fullname = self.mapping['fullname']
            self.refresh_rate = self.mapping['refresh-rate']
            self.force_update_rate = self.refresh_rate[self.mapping['force-update']]
            self.map = self.mapping['map']

            assert self.map, 'map must contains at least one element'

        else:
            assert False, 'mapping is false'

        self.attributes = {}

        self.create_attributes()

    def set_add_to_sched_callback(self, callback):
        """Set the callback for adding the updated value to the sched queue"""
        self.add_to_sched_callback = callback

    def initialize(self, endpoint: cloudio.endpoint):
        # Assuming that one of the cloud.iO nodes have the same name as the target hardware
        cloudio_node = endpoint.get_node(self.CLOUDIO_NODE_NAME)
        if cloudio_node:
            self.set_cloudio_buddy(cloudio_node)

            # Create attribute mapping needed by Model2CloudConnector using the mapping config file
            attribute_mapping = self._create_cloudio_attribute_mapping()

            # Assig attribute mapping to Model2CloudConnector
            self.set_attribute_mapping(attribute_mapping)
        else:
            self.log.error('Could not find cloud.iO node \'%s\' in Endpoint' % self.CLOUDIO_NODE_NAME)

    def _create_cloudio_attribute_mapping(self):
        """Creates attribute mapping structure needed by Model2CloudConnector.setAttributeMapping()
            from the informations contained in the mapping file
        """
        mapping = {}

        if self.map:
            for map_object in self.map:

                # test if the comm-name is a normal attribute or a multi-attribute
                # multi-attribute are when its needed to read 2 differents attributes to build up 1 cloudio attribute
                if type(map_object['comm-name']) == list:
                    # multi-attribute
                    comm_name = self.CLOUDIO_NODE_TOPIC_PREFIX + json.dumps(map_object['comm-name'])
                else:
                    # normal attribute
                    comm_name = self.CLOUDIO_NODE_TOPIC_PREFIX + map_object['comm-name']

                constraint = self._guess_attribute_constraint(map_object['permission'])

                topic = map_object['cloudio-name']
                assert not isinstance(topic, list), 'value must be a simple type'

                # Mapping entry example:
                # {'objectName': 'properties',
                #  'attributeName': 'soc',
                #  'attributeType': int,
                #  'constraints': ('read', 'write')}

                mapping_entry = dict()
                mapping_entry['topic'] = topic
                mapping_entry['attributeType'] = map_object['type']
                mapping_entry['constraints'] = constraint

                # comm-name
                mapping[comm_name] = mapping_entry
        else:
            self.log.warning("No 'cloudio-mapping' section in config found!")

        return mapping

    def create_attributes(self):
        """Fill attributes dict from the mapping file and init all the values"""

        for map_object in self.map:
            if type(map_object['comm-name']) == list:
                self.create_attribute(json.dumps(map_object['comm-name']), map_object['type'])
            else:
                self.create_attribute(map_object['comm-name'], map_object['type'])

    def create_attribute(self, name, attribute_type):
        """Adds an attribute using name and type.
                """
        if attribute_type == 'bool':
            self.attributes[name] = False
        elif attribute_type == 'int':
            self.attributes[name] = 0
        elif attribute_type == 'float':
            self.attributes[name] = 0.0
        elif attribute_type == 'string' or attribute_type == 'str':
            self.attributes[name] = ''
        else:
            self.log.warning(f'Attribute type {attribute_type} not known')

    @staticmethod
    def _guess_attribute_constraint(attribute_name: str) -> tuple:
        """Checks if attribute can be written from the cloud. If yes 'write' constraint is given.
        """
        if attribute_name == 'RW':
            return 'read', 'write'
        elif attribute_name == 'W':
            return 'write',
        else:
            return 'read',

    def update_parameter(self, parameter, value, force=False):
        """Called after app.Controller read a target parameter value.
        """
        # get mapping name
        map_with_attr = [param for param in self.map if param['comm-name'] == parameter]

        # support multi-attribute mapping
        # convert list parameter to standard attribute
        if type(parameter) == list:
            parameter = json.dumps(parameter)

        if parameter in self.attributes:
            # Update attribute
            self.attributes[parameter] = value

            for map_object in map_with_attr:
                mapping_parameter = self.CLOUDIO_NODE_TOPIC_PREFIX + parameter

                if 'out' in map_object:
                    # the value need to be modified before sending to cloud

                    val = value  # val is unused because it's used by the eval function

                    try:
                        value_updated = eval(map_object['out'])  # evaluating a expression writted in the mapping file
                    except:
                        self.log.error(f'out function error for {mapping_parameter}')
                        return
                else:
                    value_updated = value

                # update to the cloud
                self._update_cloudio_attribute(mapping_parameter, value_updated, force=force)

        else:
            self.log.warning('Parameter \'%s\' not found!', parameter)

    def on_attribute_set_from_cloud(self, attribute_name, cloudio_attribute):
        """Called after a change from the cloud"""

        if not attribute_name.startswith(self.CLOUDIO_NODE_TOPIC_PREFIX):
            # Attribute not for this node. Leave
            return

        self.log.info('Change from cloud: %s' % attribute_name)

        target_parameter_name = attribute_name[len(self.CLOUDIO_NODE_TOPIC_PREFIX):]  # remove node name

        # if target_parameter_name in known attributes:
        if target_parameter_name in self.attributes:
            # Get the value from the attribute which was changed from the cloud
            value = cloudio_attribute.get_value()

            map_with_attr = [param for param in self.map if param['comm-name'] == target_parameter_name]

            for map_object in map_with_attr:

                if 'in' in map_object:
                    # the value need to be modified before sending to the device

                    val = value  # val is unused because it's used by the eval function

                    try:
                        value_updated = eval(map_object['in'])  # evaluating a expression writted in the mapping file
                    except:
                        self.log.error(f'in function error for {target_parameter_name}')
                        return
                else:
                    value_updated = value

                # Set new value to the attributes dict
                self.attributes[target_parameter_name] = value_updated

                # Notify components => app.Controller

                if self.add_to_sched_callback is not None:
                    self.add_to_sched_callback(self.device, target_parameter_name, value_updated)
        else:
            self.log.warning('Parameter \'%s\' cannot be set (is read only)!' % attribute_name)

