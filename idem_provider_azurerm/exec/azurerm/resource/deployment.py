# -*- coding: utf-8 -*-
'''
Azure Resource Manager (ARM) Resource Deployment Execution Module

.. versionadded:: 1.0.0

:maintainer: <devops@eitr.tech>
:maturity: new
:depends:
    * `azure <https://pypi.python.org/pypi/azure>`_ >= 4.0.0
    * `azure-common <https://pypi.python.org/pypi/azure-common>`_ >= 1.1.23
    * `azure-mgmt <https://pypi.python.org/pypi/azure-mgmt>`_ >= 4.0.0
    * `azure-mgmt-compute <https://pypi.python.org/pypi/azure-mgmt-compute>`_ >= 4.6.2
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
from json import loads, dumps
import logging

# Azure libs
HAS_LIBS = False
try:
    import azure.mgmt.resource.resources.models  # pylint: disable=unused-import
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError
    HAS_LIBS = True
except ImportError:
    pass

log = logging.getLogger(__name__)


async def operation_get(hub, operation, deployment, resource_group, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Get a deployment operation within a deployment.

    :param operation: The operation ID of the operation within the deployment.

    :param deployment: The name of the deployment containing the operation.

    :param resource_group: The resource group name assigned to the
        deployment.

    CLI Example:

    .. code-block:: bash

        azurearm_resource.deployment_operation_get XXXXX testdeploy testgroup

    '''
    resconn = await hub.exec.utils.azurerm.get_client('resource', **kwargs)
    try:
        operation = resconn.deployment_operations.get(
            resource_group_name=resource_group,
            deployment_name=deployment,
            operation_id=operation
        )

        result = operation.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('resource', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def operations_list(hub, name, resource_group, result_limit=10, **kwargs):
    '''
    .. versionadded:: 1.0.0

    List all deployment operations within a deployment.

    :param name: The name of the deployment to query.

    :param resource_group: The resource group name assigned to the
        deployment.

    :param result_limit: (Default: 10) The limit on the list of deployment
        operations.

    CLI Example:

    .. code-block:: bash

        azurearm_resource.deployment_operations_list testdeploy testgroup

    '''
    result = {}
    resconn = await hub.exec.utils.azurerm.get_client('resource', **kwargs)
    try:
        operations = await hub.exec.utils.azurerm.paged_object_to_list(
            resconn.deployment_operations.list(
                resource_group_name=resource_group,
                deployment_name=name,
                top=result_limit
            )
        )

        for oper in operations:
            result[oper['operation_id']] = oper
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('resource', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def delete(hub, name, resource_group, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Delete a deployment.

    :param name: The name of the deployment to delete.

    :param resource_group: The resource group name assigned to the
        deployment.

    CLI Example:

    .. code-block:: bash

        azurearm_resource.deployment_delete testdeploy testgroup

    '''
    result = False
    resconn = await hub.exec.utils.azurerm.get_client('resource', **kwargs)
    try:
        deploy = resconn.deployments.delete(
            deployment_name=name,
            resource_group_name=resource_group
        )
        deploy.wait()
        result = True
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('resource', str(exc), **kwargs)

    return result


async def check_existence(hub, name, resource_group, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Check the existence of a deployment.

    :param name: The name of the deployment to query.

    :param resource_group: The resource group name assigned to the
        deployment.

    CLI Example:

    .. code-block:: bash

        azurearm_resource.deployment_check_existence testdeploy testgroup

    '''
    result = False
    resconn = await hub.exec.utils.azurerm.get_client('resource', **kwargs)
    try:
        result = resconn.deployments.check_existence(
            deployment_name=name,
            resource_group_name=resource_group
        )
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('resource', str(exc), **kwargs)

    return result


async def create_or_update(hub, name, resource_group, deploy_mode='incremental',
                                debug_setting='none', deploy_params=None,
                                parameters_link=None, deploy_template=None,
                                template_link=None, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Deploys resources to a resource group.

    :param name: The name of the deployment to create or update.

    :param resource_group: The resource group name assigned to the
        deployment.

    :param deploy_mode: The mode that is used to deploy resources. This value can be either
        'incremental' or 'complete'. In Incremental mode, resources are deployed without deleting
        existing resources that are not included in the template. In Complete mode, resources
        are deployed and existing resources in the resource group that are not included in
        the template are deleted. Be careful when using Complete mode as you may
        unintentionally delete resources.

    :param debug_setting: The debug setting of the deployment. The permitted values are 'none',
        'requestContent', 'responseContent', or 'requestContent,responseContent'. By logging
        information about the request or response, you could potentially expose sensitive data
        that is retrieved through the deployment operations.

    :param deploy_params: JSON string containing name and value pairs that define the deployment
        parameters for the template. You use this element when you want to provide the parameter
        values directly in the request rather than link to an existing parameter file. Use either
        the parameters_link property or the deploy_params property, but not both.

    :param parameters_link: The URI of a parameters file. You use this element to link to an existing
        parameters file. Use either the parameters_link property or the deploy_params property, but not both.

    :param deploy_template: JSON string of template content. You use this element when you want to pass
        the template syntax directly in the request rather than link to an existing template. Use either
        the template_link property or the deploy_template property, but not both.

    :param template_link: The URI of the template. Use either the template_link property or the
        deploy_template property, but not both.

    CLI Example:

    .. code-block:: bash

        azurearm_resource.deployment_create_or_update testdeploy testgroup

    '''
    resconn = await hub.exec.utils.azurerm.get_client('resource', **kwargs)

    prop_kwargs = {'mode': deploy_mode}
    prop_kwargs['debug_setting'] = {'detail_level': debug_setting}

    if deploy_params:
        prop_kwargs['parameters'] = deploy_params
    else:
        if isinstance(parameters_link, dict):
            prop_kwargs['parameters_link'] = parameters_link
        else:
            prop_kwargs['parameters_link'] = {'uri': parameters_link}

    if deploy_template:
        prop_kwargs['template'] = deploy_template
    else:
        if isinstance(template_link, dict):
            prop_kwargs['template_link'] = template_link
        else:
            prop_kwargs['template_link'] = {'uri': template_link}

    deploy_kwargs = kwargs.copy()
    deploy_kwargs.update(prop_kwargs)

    try:
        deploy_model = await hub.exec.utils.azurerm.create_object_model(
            'resource',
            'DeploymentProperties',
            **deploy_kwargs
        )
    except TypeError as exc:
        result = {'error': 'The object model could not be built. ({0})'.format(str(exc))}
        return result

    try:
        validate = deployment_validate(
            name=name,
            resource_group=resource_group,
            **deploy_kwargs
        )
        if 'error' in validate:
            result = validate
        else:
            deploy = resconn.deployments.create_or_update(
                deployment_name=name,
                resource_group_name=resource_group,
                properties=deploy_model
            )
            deploy.wait()
            deploy_result = deploy.result()
            result = deploy_result.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('resource', str(exc), **kwargs)
        result = {'error': str(exc)}
    except SerializationError as exc:
        result = {'error': 'The object model could not be parsed. ({0})'.format(str(exc))}

    return result


async def get(hub, name, resource_group, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Get details about a specific deployment.

    :param name: The name of the deployment to query.

    :param resource_group: The resource group name assigned to the
        deployment.

    CLI Example:

    .. code-block:: bash

        azurearm_resource.deployment_get testdeploy testgroup

    '''
    resconn = await hub.exec.utils.azurerm.get_client('resource', **kwargs)
    try:
        deploy = resconn.deployments.get(
            deployment_name=name,
            resource_group_name=resource_group
        )
        result = deploy.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('resource', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def cancel(hub, name, resource_group, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Cancel a deployment if in 'Accepted' or 'Running' state.

    :param name: The name of the deployment to cancel.

    :param resource_group: The resource group name assigned to the
        deployment.

    CLI Example:

    .. code-block:: bash

        azurearm_resource.deployment_cancel testdeploy testgroup

    '''
    resconn = await hub.exec.utils.azurerm.get_client('resource', **kwargs)
    try:
        resconn.deployments.cancel(
            deployment_name=name,
            resource_group_name=resource_group
        )
        result = {'result': True}
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('resource', str(exc), **kwargs)
        result = {
            'error': str(exc),
            'result': False
        }

    return result


async def validate(hub, name, resource_group, deploy_mode=None,
                        debug_setting=None, deploy_params=None,
                        parameters_link=None, deploy_template=None,
                        template_link=None, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Validates whether the specified template is syntactically correct
    and will be accepted by Azure Resource Manager.

    :param name: The name of the deployment to validate.

    :param resource_group: The resource group name assigned to the
        deployment.

    :param deploy_mode: The mode that is used to deploy resources. This value can be either
        'incremental' or 'complete'. In Incremental mode, resources are deployed without deleting
        existing resources that are not included in the template. In Complete mode, resources
        are deployed and existing resources in the resource group that are not included in
        the template are deleted. Be careful when using Complete mode as you may
        unintentionally delete resources.

    :param debug_setting: The debug setting of the deployment. The permitted values are 'none',
        'requestContent', 'responseContent', or 'requestContent,responseContent'. By logging
        information about the request or response, you could potentially expose sensitive data
        that is retrieved through the deployment operations.

    :param deploy_params: JSON string containing name and value pairs that define the deployment
        parameters for the template. You use this element when you want to provide the parameter
        values directly in the request rather than link to an existing parameter file. Use either
        the parameters_link property or the deploy_params property, but not both.

    :param parameters_link: The URI of a parameters file. You use this element to link to an existing
        parameters file. Use either the parameters_link property or the deploy_params property, but not both.

    :param deploy_template: JSON string of template content. You use this element when you want to pass
        the template syntax directly in the request rather than link to an existing template. Use either
        the template_link property or the deploy_template property, but not both.

    :param template_link: The URI of the template. Use either the template_link property or the
        deploy_template property, but not both.

    CLI Example:

    .. code-block:: bash

        azurearm_resource.deployment_validate testdeploy testgroup

    '''
    resconn = await hub.exec.utils.azurerm.get_client('resource', **kwargs)

    prop_kwargs = {'mode': deploy_mode}
    prop_kwargs['debug_setting'] = {'detail_level': debug_setting}

    if deploy_params:
        prop_kwargs['parameters'] = deploy_params
    else:
        if isinstance(parameters_link, dict):
            prop_kwargs['parameters_link'] = parameters_link
        else:
            prop_kwargs['parameters_link'] = {'uri': parameters_link}

    if deploy_template:
        prop_kwargs['template'] = deploy_template
    else:
        if isinstance(template_link, dict):
            prop_kwargs['template_link'] = template_link
        else:
            prop_kwargs['template_link'] = {'uri': template_link}

    deploy_kwargs = kwargs.copy()
    deploy_kwargs.update(prop_kwargs)

    try:
        deploy_model = await hub.exec.utils.azurerm.create_object_model(
            'resource',
            'DeploymentProperties',
            **deploy_kwargs
        )
    except TypeError as exc:
        result = {'error': 'The object model could not be built. ({0})'.format(str(exc))}
        return result

    try:
        local_validation = deploy_model.validate()
        if local_validation:
            raise local_validation[0]

        deploy = resconn.deployments.validate(
            deployment_name=name,
            resource_group_name=resource_group,
            properties=deploy_model
        )
        result = deploy.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('resource', str(exc), **kwargs)
        result = {'error': str(exc)}
    except SerializationError as exc:
        result = {'error': 'The object model could not be parsed. ({0})'.format(str(exc))}

    return result


async def export_template(hub, name, resource_group, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Exports the template used for the specified deployment.

    :param name: The name of the deployment to query.

    :param resource_group: The resource group name assigned to the
        deployment.

    CLI Example:

    .. code-block:: bash

        azurearm_resource.deployment_export_template testdeploy testgroup

    '''
    resconn = await hub.exec.utils.azurerm.get_client('resource', **kwargs)
    try:
        deploy = resconn.deployments.export_template(
            deployment_name=name,
            resource_group_name=resource_group
        )
        result = deploy.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('resource', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def list_(hub, resource_group, **kwargs):
    '''
    .. versionadded:: 1.0.0

    List all deployments within a resource group.

    CLI Example:

    .. code-block:: bash

        azurearm_resource.deployments_list testgroup

    '''
    result = {}
    resconn = await hub.exec.utils.azurerm.get_client('resource', **kwargs)
    try:
        deployments = await hub.exec.utils.azurerm.paged_object_to_list(
            resconn.deployments.list_by_resource_group(
                resource_group_name=resource_group
            )
        )

        for deploy in deployments:
            result[deploy['name']] = deploy
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('resource', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result
