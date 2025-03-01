#!/usr/bin/python
# Copyright: (c) 2021, DellEMC

# Apache License version 2.0 (see MODULE-LICENSE or http://www.apache.org/licenses/LICENSE-2.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'
                    }

DOCUMENTATION = r'''
---
module: dellemc_powerscale_node
version_added: '1.2.0'

short_description: get node info of DellEMC PowerScale storage

description:
- Get information of a node belonging to the PowerScale cluster

extends_documentation_fragment:
  - dellemc.powerscale.dellemc_powerscale.powerscale

author:
- Ganesh Prabhu(@prabhg5) <ansible.team@dell.com>>

options:
  node_id:
    description:
    - The Logical node Number of a PowerScale cluster node
    required: true
    type: int
  state:
    description:
    - Defines whether the node should exist or not.
    required: true
    choices: [absent, present]
    type: str
  '''
EXAMPLES = r'''
- name: get node info of the PowerScale cluster node
  dellemc_powerscale_node:
    onefs_host: "{{onefs_host}}"
    verify_ssl: "{{verify_ssl}}"
    api_user: "{{api_user}}"
    api_password: "{{api_password}}"
    node_id: "{{cluster_node_id}}"
    state: "present"
   '''
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.dellemc.powerscale.plugins.module_utils.storage.dell \
    import dellemc_ansible_powerscale_utils as utils
import re

LOG = utils.get_logger('dellemc_powerscale_node')


class PowerScaleClusterNode(object):
    def __init__(self):
        """Define all the parameters required by this module"""

        self.module_params = utils.get_powerscale_management_host_parameters()
        self.module_params.update(get_powerscale_node_parameters())

        # initialize the Ansible module
        self.module = AnsibleModule(argument_spec=self.module_params,
                                    supports_check_mode=False
                                    )
        PREREQS_VALIDATE = utils.validate_module_pre_reqs(self.module.params)
        if PREREQS_VALIDATE \
                and not PREREQS_VALIDATE["all_packages_found"]:
            self.module.fail_json(
                msg=PREREQS_VALIDATE["error_message"])

        self.api_client = utils.get_powerscale_connection(self.module.params)
        self.isi_sdk = utils.get_powerscale_sdk()
        LOG.info('Got python SDK instance for provisioning on PowerScale ')
        self.cluster_api = self.isi_sdk.ClusterApi(self.api_client)

    def get_node_info(self, node_id):
        """get the specific cluster node information from PowerScale storage"""
        try:
            node_info = (self.cluster_api.get_cluster_node(node_id)).to_dict()
            LOG.info('Got node information from PowerScale cluster %s', self.module.params['onefs_host'])
            return node_info
        except Exception as e:
            error_msg = (
                'get node info for PowerScale cluster: {0} failed with'
                'error: {1} ' .format(
                    self.module.params['onefs_host'], utils.determine_error(error_obj=e)))
            LOG.error(error_msg)
            self.module.fail_json(msg=error_msg)

    def perform_module_operation(self):
        node_id = self.module.params['node_id']
        state = self.module.params['state']
        result = dict(
            changed=False
        )
        if state == 'absent':
            error_message = 'Deletion of node is not allowed through' \
                            ' Ansible module'
            LOG.error(error_message)
            self.module.fail_json(msg=error_message)
        if node_id and state == 'present':
            info_message = 'getting Cluster Node: ' \
                           '{0} info'.format(node_id)
            LOG.info(info_message)
            result['cluster_node_details'] = \
                self.get_node_info(node_id)
        else:
            error_message = 'Please provide a valid Node Id'
            LOG.error(error_message)
            self.module.fail_json(msg=error_message)
        # Finally update the module result!
        self.module.exit_json(**result)


def get_powerscale_node_parameters():
    """This method provides parameters required for the ansible cluster
                modules on PowerScale"""
    return dict(
        node_id=dict(required=True, type='int'),
        state=dict(required=True, type='str',
                   choices=['present', 'absent'])
    )


def main():
    """Create PowerScale cluster node object and perform action on it
        based on user input from playbook"""
    obj = PowerScaleClusterNode()
    obj.perform_module_operation()


if __name__ == '__main__':
    main()
