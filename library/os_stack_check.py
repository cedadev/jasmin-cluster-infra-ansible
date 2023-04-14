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
module: os_stack_check
short_description: Run a check on a Heat stack.
extends_documentation_fragment: openstack
author: Matt Pryor (STFC)
description:
  - Runs a check on an OpenStack Heat stack
requirements:
  - "python >= 2.7"
  - "openstacksdk"
options:
  name:
    description:
      - Name of the stack to run the check on
    required: true
  timeout:
    description:
      - Maximum number of seconds to wait for the check to run
    default: 3600
"""

EXAMPLES = """
---

- name: Run stack check
  os_stack_check:
    name: "{{ stack_name }}"
"""

RETURN = """
id:
  description: Stack ID
  type: str
  returned: always

stack:
  description: Stack information
  type: complex
  returned: always
"""

import time

from ansible.module_utils.basic import AnsibleModule
from openstack.cloud.plugins.module_utils.openstack import (
    openstack_cloud_from_module, openstack_full_argument_spec,
    openstack_module_kwargs)


class StackCheckTimeoutError(RuntimeError):
    """
    Raised if the stack check times out.
    """


def main():
    argument_spec = openstack_full_argument_spec(
        name=dict(required=True),
        timeout=dict(default=3600, type="int"),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        # First, try to fetch the stack
        # Make a missing stack cause an error
        stack = cloud.orchestration.find_stack(
            module.params["name"], ignore_missing=False
        )
        # Start the stack check
        cloud.orchestration.check_stack(stack)
        # Wait for the stack check to complete
        timeout = module.params["timeout"]
        start = time.time()
        while time.time() < start + timeout:
            stack = cloud.orchestration.get_stack(stack)
            if stack.status != "CHECK_IN_PROGRESS":
                break
        else:
            raise StackCheckTimeoutError("Timed out waiting for stack check.")
        if stack.status == "CHECK_COMPLETE":
            # Don't count what we've done as a change
            module.exit_json(changed=False, id=stack.id, stack=stack)
        else:
            module.fail_json(msg="Stack check failed")
    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
