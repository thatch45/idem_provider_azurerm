# -*- coding: utf-8 -*-
'''
Azure Resource Manager (ARM) Network Execution Module

.. versionadded:: 1.0.0

:maintainer: <devops@eitr.tech>
:maturity: new
:depends:
    * `azure <https://pypi.python.org/pypi/azure>`_ >= 4.0.0
    * `azure-common <https://pypi.python.org/pypi/azure-common>`_ >= 1.1.23
    * `azure-mgmt <https://pypi.python.org/pypi/azure-mgmt>`_ >= 4.0.0
    * `azure-mgmt-compute <https://pypi.python.org/pypi/azure-mgmt-compute>`_ >= 4.6.2
    * `azure-mgmt-network <https://pypi.python.org/pypi/azure-mgmt-network>`_ >= 4.0.0
    * `azure-mgmt-resource <https://pypi.python.org/pypi/azure-mgmt-resource>`_ >= 2.2.0
    * `azure-mgmt-storage <https://pypi.python.org/pypi/azure-mgmt-storage>`_ >= 2.0.0
    * `azure-mgmt-web <https://pypi.python.org/pypi/azure-mgmt-web>`_ >= 0.35.0
    * `azure-storage <https://pypi.python.org/pypi/azure-storage>`_ >= 0.36.0
    * `msrestazure <https://pypi.python.org/pypi/msrestazure>`_ >= 0.6.1
:platform: linux

:configuration: This module requires Azure Resource Manager credentials to be passed as keyword arguments
    to every function in order to work properly.

    Required provider parameters:

    if using username and password:
      * ``subscription_id``
      * ``username``
      * ``password``

    if using a service principal:
      * ``subscription_id``
      * ``tenant``
      * ``client_id``
      * ``secret``

    Optional provider parameters:

**cloud_environment**: Used to point the cloud driver to different API endpoints, such as Azure GovCloud.
    Possible values:
      * ``AZURE_PUBLIC_CLOUD`` (default)
      * ``AZURE_CHINA_CLOUD``
      * ``AZURE_US_GOV_CLOUD``
      * ``AZURE_GERMAN_CLOUD``

'''

# Python libs
from __future__ import absolute_import
import logging

try:
    from six.moves import range as six_range
except ImportError:
    six_range = range

# Azure libs
HAS_LIBS = False
try:
    import azure.mgmt.network.models  # pylint: disable=unused-import
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError
    HAS_LIBS = True
except ImportError:
    pass

log = logging.getLogger(__name__)


async def check_dns_name_availability(hub, name, region, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Check whether a domain name in the current zone is available for use.

    :param name: The DNS name to query.

    :param region: The region to query for the DNS name in question.

    CLI Example:

    .. code-block:: bash

         azurerm.network.check_dns_name_availability testdnsname westus

    '''
    netconn = await hub.exec.utils.azurerm.get_client('network', **kwargs)
    try:
        check_dns_name = netconn.check_dns_name_availability(
            location=region,
            domain_name_label=name
        )
        result = check_dns_name.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('network', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def check_ip_address_availability(hub, ip_address, virtual_network, resource_group, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Check that a private ip address is available within the specified
    virtual network.

    :param ip_address: The ip_address to query.

    :param virtual_network: The virtual network to query for the IP address
        in question.

    :param resource_group: The resource group name assigned to the
        virtual network.

    CLI Example:

    .. code-block:: bash

         azurerm.network.check_ip_address_availability 10.0.0.4 testnet testgroup

    '''
    netconn = await hub.exec.utils.azurerm.get_client('network', **kwargs)
    try:
        check_ip = netconn.virtual_networks.check_ip_address_availability(
            resource_group_name=resource_group,
            virtual_network_name=virtual_network,
            ip_address=ip_address)
        result = check_ip.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('network', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def usages_list(hub, location, **kwargs):
    '''
    .. versionadded:: 1.0.0

    List subscription network usage for a location.

    :param location: The Azure location to query for network usage.

    CLI Example:

    .. code-block:: bash

         azurerm.network.usages_list westus

    '''
    netconn = await hub.exec.utils.azurerm.get_client('network', **kwargs)
    try:
        result = await hub.exec.utils.azurerm.paged_object_to_list(netconn.usages.list(location))
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('network', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result
