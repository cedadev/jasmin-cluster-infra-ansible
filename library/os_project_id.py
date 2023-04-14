#!/usr/bin/env python

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: os_project_id
short_description: Get the current project id.
extends_documentation_fragment: openstack
author: Matt Pryor (STFC)
description:
  - Gets the current Openstack project ID.
requirements:
  - "python >= 2.7"
  - "openstacksdk"
options: {}
"""

EXAMPLES = """
---

- name: Get project ID
  os_project_id:

- debug: var=openstack_project_id
"""


import time

from ansible.module_utils.basic import AnsibleModule
from openstack.cloud.plugins.module_utils.openstack import (
    openstack_cloud_from_module, openstack_full_argument_spec,
    openstack_module_kwargs)


def main():
    argument_spec = openstack_full_argument_spec()
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    sdk, cloud = openstack_cloud_from_module(module)
    module.exit_json(
        changed=False, ansible_facts=dict(openstack_project_id=cloud.current_project.id)
    )


if __name__ == "__main__":
    main()
