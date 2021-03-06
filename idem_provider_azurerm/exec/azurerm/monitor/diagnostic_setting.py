# -*- coding: utf-8 -*-
'''
Azure (ARM) Monitor Diagnostic Setting Execution Module

.. versionadded:: 1.0.0

:maintainer: <devops@eitr.tech>
:maturity: new
:depends:
    * `azure <https://pypi.python.org/pypi/azure>`_ >= 4.0.0
    * `azure-common <https://pypi.python.org/pypi/azure-common>`_ >= 1.1.23
    * `azure-mgmt <https://pypi.python.org/pypi/azure-mgmt>`_ >= 4.0.0
    * `azure-mgmt-compute <https://pypi.python.org/pypi/azure-mgmt-compute>`_ >= 4.6.2
    * `azure-mgmt-monitor <https://pypi.org/project/azure-mgmt-monitor>`_ >= 0.5.2
    * `azure-mgmt-network <https://pypi.python.org/pypi/azure-mgmt-network>`_ >= 2.7.0
    * `azure-mgmt-resource <https://pypi.python.org/pypi/azure-mgmt-resource>`_ >= 2.2.0
    * `azure-mgmt-storage <https://pypi.python.org/pypi/azure-mgmt-storage>`_ >= 2.0.0
    * `azure-mgmt-web <https://pypi.python.org/pypi/azure-mgmt-web>`_ >= 0.35.0
    * `azure-storage <https://pypi.python.org/pypi/azure-storage>`_ >= 0.34.3
    * `msrestazure <https://pypi.python.org/pypi/msrestazure>`_ >= 0.6.2
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

# Azure libs
HAS_LIBS = False
try:
    import azure.mgmt.monitor.models  # pylint: disable=unused-import
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError
    HAS_LIBS = True
except ImportError:
    pass

log = logging.getLogger(__name__)


async def create_or_update(hub, name, resource_uri, metrics, logs, workspace_id=None, storage_account_id=None,
                           service_bus_rule_id=None, event_hub_authorization_rule_id=None, event_hub_name=None,
                           **kwargs):
    '''
    .. versionadded:: 1.0.0

    Create or update diagnostic settings for the specified resource. At least one destination for the diagnostic
        setting is required. The three possible destinations for the diagnostic settings are as follows:
            1. Archive the diagnostic settings to a stroage account. This would require the storage_account_id param.
            2. Stream the diagnostic settings to an event hub. This would require the event_hub_name and
               event_hub_authorization_rule_id params.
            3. Send the diagnostic settings to Log Analytics. This would require the workspace_id param.
        Any combination of these destinations is acceptable.

    :param name: The name of the diagnostic setting.

    :param resource_uri: The identifier of the resource.

    :param metrics: The list of metric settings. This is a list of dictionaries representing MetricSettings objects.

    :param logs: The list of logs settings. This is a list of dictionaries representing LogSettings objects.

    :param workspace_id: The workspace ID (resource ID of a Log Analytics workspace) for a Log Analytics workspace to
        which you would like to send Diagnostic Logs.

    :param storage_account_id: The resource ID of the storage account to which you would like to send Diagnostic Logs.

    :param service_bus_rule_id: The service bus rule ID of the diagnostic setting.
        This is here to maintain backwards compatibility.

    :param event_hub_authorization_rule_id: The resource ID for the event hub authorization rule.

    :param event_hub_name: The name of the event hub. If none is specified, the default event hub will be selected.

    CLI Example:

    .. code-block:: bash

        azurerm.monitor.diagnostic_setting.create_or_update testname testuri testmetrics testlogs \
                  testdestination

    '''
    result = {}
    moniconn = await hub.exec.utils.azurerm.get_client('monitor', **kwargs)

    try:
        diagmodel = await hub.exec.utils.azurerm.create_object_model(
            'monitor',
            'DiagnosticSettingsResource',
            metrics=metrics,
            logs=logs,
            workspace_id=workspace_id,
            storage_account_id=storage_account_id,
            service_bus_rule_id=service_bus_rule_id,
            event_hub_authorization_rule_id=event_hub_authorization_rule_id,
            event_hub_name=event_hub_name,
            **kwargs
        )
    except TypeError as exc:
        result = {'error': 'The object model could not be built. ({0})'.format(str(exc))}
        return result

    try:
        diag = moniconn.diagnostic_settings.create_or_update(
            name=name,
            resource_uri=resource_uri,
            parameters=diagmodel
        )

        result = diag.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('monitor', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def delete(hub, name, resource_uri, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Deletes existing diagnostic settings for the specified resource.

    :param name: The name of the diagnostic setting.

    :param resource_uri: The identifier of the resource.

    CLI Example:

    .. code-block:: bash

        azurerm.monitor.diagnostic_setting.delete testname testuri

    '''
    result = False
    moniconn = await hub.exec.utils.azurerm.get_client('monitor', **kwargs)
    try:
        diag = moniconn.diagnostic_settings.delete(
            name=name,
            resource_uri=resource_uri,
            **kwargs
        )

        result = True
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('monitor', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def get(hub, name, resource_uri, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Gets the active diagnostic settings for the specified resource.

    :param name: The name of the diagnostic setting.

    :param resource_uri: The identifier of the resource.

    CLI Example:

    .. code-block:: bash

        azurerm.monitor.diagnostic_setting.get testname testuri

    '''
    result = {}
    moniconn = await hub.exec.utils.azurerm.get_client('monitor', **kwargs)
    try:
        diag = moniconn.diagnostic_settings.get(
            name=name,
            resource_uri=resource_uri,
            **kwargs
        )
        result = diag.as_dict()

    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('monitor', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def list_(hub, resource_uri, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Gets the active diagnostic settings list for the specified resource.

    :param resource_uri: The identifier of the resource.

    CLI Example:

    .. code-block:: bash

        azurerm.monitor.diagnostic_setting.get testname testuri

    '''
    result = {}
    moniconn = await hub.exec.utils.azurerm.get_client('monitor', **kwargs)
    try:
        diag = moniconn.diagnostic_settings.list(
            resource_uri=resource_uri,
            **kwargs
        )

        result = diag.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('monitor', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result
