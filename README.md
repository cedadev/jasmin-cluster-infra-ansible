# JASMIN Cluster-as-a-Service Infrastructure

This role generates OpenStack infrastructure for Cluster-as-a-Service applications
using OpenStack Heat.

The Ansible in-memory inventory is updated with the generated infrastructure, which
can then be used in subsequent plays. By default, hosts are placed in the following
groups, which can be used to structure the following plays:

  * `cluster`
  * `cluster_{{ cluster_name }}`
  * `{{ group_name }}`
  * `{{ cluster_name }}_{{ group_name }}`

For example:

```yaml
---

- hosts: openstack
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

## Additional inventory groups

Additional inventory groups can be attached on a per-group basis using the `inventory_groups`
property, e.g.:

```yaml
- hosts: openstack
  roles:
    - role: jasmin.cluster-infra
      vars:
        cluster_groups:
          - name: masters
            # ...
            inventory_groups: [kube_hosts, kube_masters]
          - name: workers
            # ...
            inventory_groups: [kube_hosts, kube_workers]

- hosts: kube_hosts
  tasks:
    # ... Common operations for all hosts

- hosts: kube_masters
  tasks:
    # ... Master-only operations

- hosts: kube_workers
  tasks:
    # ... Worker-only operations
```

This is useful because the group name appears in the names of provisioned resources, so it
is useful to keep it concise.

## Configuration of per-group storage

### Root volume

In some cases, it is useful to have a larger root volume than those provided by the flavor.
This is possible by using a Cinder volume as the root volume. To do this, just specify
the `root_volume_size` for the group:

```yaml
- hosts: openstack
  roles:
    - role: jasmin.cluster-infra
      vars:
        cluster_groups:
          - name: servers
            # ...
            root_volume_size: 80
```

This will provision a Cinder volume for each node in the group and use it as the root
volume for that node.

### Additional volumes

Additional volumes can be specified on a per-group basis using the `additional_volumes`
property. This property is a list of dictionaries with `name` and `size` keys:

```yaml
- hosts: openstack
  roles:
    - role: jasmin.cluster-infra
      vars:
        cluster_groups:
          - name: servers
            # ...
            additional_volumes:
              - name: data
                size: 50
```

For each entry in `additional_volumes`, a Cinder volume is created and attached for
each node in the group.

## Per-group network configuration

The default network configuration is for a single port on the
designated virtual tenant network.  For nodes that must be externally
reachable, a floating IP is usually required.

To specify non-default network resources, set the `nodenet_resource` parameter.
These settings are valid:

  - `Cluster::NodeNet1` - the default configuration, with a single port on the
    designated tenant network.
  - `Cluster::NodeNet1WithPreallocatedFIP` - associate a floating IP with the
    compute nodes in this group.  The floating IP must be preallocated (and not
    currently associated anywhere else).  A list of dicts of pre-allocated
    floating IPs must be supplied in the parameter `nodenet_fips`.  The list
    entry for each floating IP must contain fields `uuid` and `ip`.


## Access to the cluster through a bastion host

For cluster deployments in which not all hosts are externally reachable,
it is possible to access the internal hosts via an SSH Proxy Jump.

### Using an externally-reachable host in the same cluster

The simplest way to configure a jump host is to use an externally-reachable host
in the same cluster.

To configure this, define a parameter `cluster_gw_group`, which names
one of the listed groups of the cluster that has been configured with an
externally-addressable IP.  One or more of the hosts in this group will be
used in a `ProxyCommand` for the rest of the hosts in the cluster.

### Using a pre-existing bastion host in the same project

If none of the hosts have an externally-addressable IP, it is possible to use a host
outside the cluster, but in the same project, by specifying `cluster_gw_ssh_proxy_command`.
This variable should contain the extra arguments that need to be added to the SSH command:

```yaml
- hosts: openstack
  roles:
    - role: jasmin.cluster-infra
      vars:
        cluster_groups:
          - name: servers
            # ...
            additional_volumes:
              - name: data
                size: 50
        cluster_gw_ssh_proxy_command: "-o ProxyCommand='ssh -i /path/to/ssh/key -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -W %h:%p <user>@<gatewayhost>'"
```

### Using another cluster in the same project

When `jasmin.cluster-infra` configures an SSH gateway, it sets the `cluster_gw_ssh_proxy_command`
variable. This means that by running `jasmin.cluster-infra` twice in succession, where the first
execution has a `cluster_gw_group`, it is possible to use a host from one cluster as the SSH
jump host for another cluster:

```yaml
- hosts: openstack
  tasks:
    # Use a pre-existing stack as the gateway
    - include_role:
        name: jasmin.cluster-infra
      vars:
        cluster_name: "{{ identity_stack_name }}"
        cluster_stack_update: false
        cluster_gw_group: "{{ identity_gw_group_name }}"

    # Provision the cluster infrastructure
    - include_role:
        name: jasmin.cluster-infra
      vars:
        cluster_groups:
          - name: servers
            # ...
```

## Categorising deployments using cluster tags

In an environment where multiple deployments are active, they can easily
be categorised according to type (or anything else) by specifying
a `cluster_tag`.  These tags translate to Heat stack tags, and all stacks
with a given tag can be listed together, for example using:

```
heat stack list --tags storage
```

## Bringing it all together

```yaml
- hosts: openstack
  roles:
    - role: jasmin.cluster-infra
      vars:
        cluster_name: test
        cluster_deploy_user: 'centos'
        cluster_network: "caastest-U-internal"
        cluster_groups:
          - name: "ext"
            flavor: "j1.small"
            image: "centos-7-20190104"
            num_nodes: 1
            nodenet_resource: "Cluster::NodeNet1WithPreallocatedFIP"
            nodenet_fips:
              - uuid: "fbd8781c-0917-41a3-8a66-ecaf0f05826a"
                ip: "192.171.139.250"
          - name: "int"
            flavor: "j1.small"
            image: "centos-7-20190104"
            num_nodes: 1
            nodenet_resource: "Cluster::NodeNet1"
        cluster_gw_group: "ext"
        cluster_tag: "test"
```

Inspiration was taken from the StackHPC cluster-infra role: https://github.com/stackhpc/ansible-role-cluster-infra.
