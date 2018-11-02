# JASMIN Cluster-as-a-Service Infrastructure

This role generates OpenStack infrastructure for Cluster-as-a-Service applications
using OpenStack Heat.

The Ansible in-memory inventory is updated with the generated infrastructure, which
can then be used in subsequent plays. As well as the user defined groups, all the
generated hosts are placed in a group called `cluster`.

For example:

```yaml
---
- hosts: localhost
  connection: local
  roles:
    - role: jasmin.cluster-infra
      vars:
        # Configure the groups expected by subsequent plays
        cluster_groups:
          - name: masters
            num_nodes: 1
            flavor: "{{ master_flavor }}"
          - name: workers
            num_nodes: "{{ num_workers }}"
            flavor: "{{ worker_flavor }}"

- hosts: cluster
  remote_user: user
  force_handlers: true
  tasks:
    - name: Contact hosts
      ping:
```

Inspiration was taken from the StackHPC cluster-infra role: https://github.com/stackhpc/ansible-role-cluster-infra.
