import logging
import traceback
import time
from xml.dom import minidom

from cloudio.endpoint.attribute import CloudioAttributeConstraint
from cloudio.endpoint.endpoint import CloudioEndpoint
from cloudio.endpoint.runtime.node import CloudioRuntimeNode
from cloudio.endpoint.runtime.object import CloudioRuntimeObject
from cloudio.endpoint.properties_endpoint_configuration import PropertiesEndpointConfiguration


from config.config import get_cloudio_properties, SETTINGS_BASE_PATH, \
    CLOUDIO_PROPERTIES_DIR


class Connector(object):
    """Connector class : create cloudio connection and cloudio model
        attributes:
        * _endpoint : endpoint of the gateway
        * protocol : protocol to use with this device for reading or writing
        *
        *
        *
    """

    log = logging.getLogger(__name__)

    def __init__(self, gateway_config):
        super(Connector, self).__init__()

        # cloudio config
        properties = get_cloudio_properties(f'{SETTINGS_BASE_PATH}/{CLOUDIO_PROPERTIES_DIR}/{gateway_config["cloudio"]["config-file-name"]}.yaml')

        # if not set by the env var => read it in the gateway config file
        if 'uuid' not in properties:
            properties['uuid'] = gateway_config['cloudio']['endpoint']

        # create a configuration object from a dict()
        configuration = PropertiesEndpointConfiguration(properties)

        self.log.info(f'creating cloudio endpoint with endpoint name : {properties["uuid"]}')

        # create an endpoint with properties['uuid'] and the configuration
        self._endpoint = CloudioEndpoint(properties['uuid'], configuration)
        # print("ENDPOINT", self._endpoint.is_online())


    def get_endpoint_name(self):
        """ get the endpoint name """
        return self._endpoint.get_name()

    # getter
    @property
    def endpoint(self):
        return self._endpoint

    def wait_endpoint_online(self, timeout):
        """ wait while the endpoint is online """
        while timeout > 0:
            if self._endpoint.is_online():
                break
            timeout -= 0.2
            time.sleep(0.2)

    def create_model(self, xml_string):
        """ create cloudio model from xml concatened file """

        try:
            # root tag is mandatory for parsing more than one node !
            xmlConfigFile = minidom.parseString(f'<root>{xml_string}</root>')

            nodeList = xmlConfigFile.getElementsByTagName(u'node')
            """:type : list of minidom.Element"""

            for node in nodeList:
                """:type : list of minidom.Element"""
                self.log.info(u'Parsing elements for device: ' + node.getAttribute('name'))
                self._parseCloudioNodeFromXmlDomElement(node)

        except Exception as e:
            traceback.print_exc()

        # Wait until endpoint is connected to the cloud
        while not self._endpoint.is_online():
            time.sleep(0.5)

        # After the endpoint is fully created the presents can be announced
        self.endpoint.announce()

    def _parseCloudioNodeFromXmlDomElement(self, node, nodeAttributeName=u'name', objectAttributeName=u'name'):
        """Parses a node from an xml dom element

        :param node:
        :type node: minidom.Element
        :return:
        """
        assert node.tagName in u'node', u'Wrong DOM element name'

        nodeName = node.getAttribute(nodeAttributeName)
        cloudioRuntimeNode = CloudioRuntimeNode()
        cloudioRuntimeNode.declare_implemented_interface(u'NodeInterface')
        # cloudioRuntimeNode.declareImplementedInterface(u'NodeInterface')

        # Parse all objects and attributes for this node
        self._parseObjectFromXmlDomElement(cloudioRuntimeNode, node)

        assert nodeName, u'No node name given!'
        assert cloudioRuntimeNode, u'No cloud.iO node object given!'
        self.endpoint.add_node(nodeName, cloudioRuntimeNode)

    @classmethod
    def _parseObjectFromXmlDomElement(cls, cloudioParentObject, parentObject, objectAttributeName=u'name'):
        """Searches for the given XML parentObject all child objects and adds them to cloudioParentObject.

        :param cloudioParentObject:
        :type cloudioParentObject: CloudioRuntimeObject
        :param parentObject:
        :type parentObject: minidom.Element
        :param objectAttributeName:
        :return:
        """

        assert parentObject.tagName in (u'node', u'object'), u'Wrong DOM element name'

        objectList = parentObject.getElementsByTagName(u'object')
        """:type : list of minidom.Element"""
        for obj in objectList:
            # Take only child objects (non-recursive)
            if obj.parentNode is parentObject:
                objectName = obj.getAttribute(objectAttributeName)
                # Create cloud.iO object
                cloudioRuntimeObject = CloudioRuntimeObject()
                # Add object to the node
                cloudioParentObject.add_object(objectName, cloudioRuntimeObject)

                # Get attributes
                attributeList = obj.getElementsByTagName(u'attribute')
                for attribute in attributeList:
                    # Take only child attributes (non-recursive)
                    if attribute.parentNode is obj:
                        cls._parseAttributeFromXmlDomElement(cloudioRuntimeObject, attribute)

                # Get child objects
                cls._parseObjectFromXmlDomElement(cloudioRuntimeObject, obj)

    @classmethod
    def _parseAttributeFromXmlDomElement(cls, cloudioRuntimeObject, attributeElement):
        """Parses an attribute from an xml dom element

        :parame cloudioRuntimeObject:
        :type cloudioRuntimeObject: CloudioRuntimeObject
        :param attributeElement:
        :type attributeElement: minidom.Element
        :return:
        """
        assert attributeElement.tagName == u'attribute', u'Wrong DOM element name'
        assert attributeElement.hasAttribute(u'name'), u'Wrong attribute format'

        theName = attributeElement.getAttribute(u'name')
        strType = attributeElement.getAttribute(u'type')
        strConstraint = attributeElement.getAttribute(u'constraint')

        # TODO Get options

        # Convert constraint from 'string' to CloudioAttributeConstraint
        constraint = CloudioAttributeConstraint(strConstraint)

        theType = None

        if strType.lower() == 'bool' or strType.lower() == 'boolean':
            theType = bool
        elif strType.lower() in ('short', 'long', 'integer'):
            theType = int
        elif strType.lower() == 'float' or strType.lower() == 'double' or strType.lower() == 'number':
            theType = float
        elif strType.lower() == 'str' or strType.lower() == 'string':
            theType = str

        assert theType, u'Attribute type unknown or not set!'

        cloudioRuntimeObject.add_attribute(theName, theType, constraint)
