# JASMIN Cluster-as-a-Service Infrastructure

This role generates OpenStack infrastructure for Cluster-as-a-Service applications
using OpenStack Heat.

The Ansible in-memory inventory is updated with the generated infrastructure, which
can then be used in subsequent plays. As well as the user defined groups, all the
generated hosts are placed in a group called `cluster`.

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

## Configuration of Per-group Storage

Different node resources can be specified for different groups.
This can be used to build specific nodes with additional resources,
such as Cinder volumes for cluster storage nodes.

To specify non-default node resources, set the `node_resource` parameter.
These settings are valid:

- `Cluster::Node` - the default configuration
- `Cluster::NodeWithVolume` - include a Cinder volume which is allocated
  as part of the cluster deployment and deallocated when the deployment
  is deleted.  The size of the volume (in gigabytes) is set using the parameter
  `root_volume_size`.


## Per-group Network Configuration

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


## Access to the Cluster through a Bastion Host

For cluster deployments in which not all hosts are externally reachable,
it is possible to access the internal hosts via an SSH Proxy Jump through
one of the externally-reachable hosts.

To configure for this, define a parameter `cluster_gw_group`, which names
one of the listed groups of the cluster that has been configured with an
externally-addressible IP.  One or more of the hosts in this group will be
used as `ProxyJump` hosts for the rest of the cluster.

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
            node_resource: "Cluster::Node" 
            nodenet_resource: "Cluster::NodeNet1WithPreallocatedFIP" 
            nodenet_fips:
              - uuid: "fbd8781c-0917-41a3-8a66-ecaf0f05826a"
                ip: "192.171.139.250"
          - name: "int"
            flavor: "j1.small"
            image: "centos-7-20190104"
            num_nodes: 1
            node_resource: "Cluster::Node" 
            nodenet_resource: "Cluster::NodeNet1" 
        cluster_gw_group: "ext"
        cluster_tag: "test"
```

Inspiration was taken from the StackHPC cluster-infra role: https://github.com/stackhpc/ansible-role-cluster-infra.
