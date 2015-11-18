Problem description
===================

Sometimes workload is not distributed optimally among hosts and some nodes are underloaded. In this case these nodes can be suspended and their VMs can be migrated to other nodes to achieve optimal cluster load.

Use Cases
---------
As a cloud operator I can start the overload algorithm in a cluster and if any nodes are underloaded they will be suspended and VMs will be migrated from them.
As a developer I can implement my own algorithms for detecting underload in a cluster.
As an end user I'm not affected by this change and won't notice any difference.

Proposed change
===============
We are going to propose creating a new algorithm for detecting underload in a cluster and suspending unnecessary nodes. Сommunicates with nova-conductor, nova-scheduler and nova-compute while balancing VMs among compute-nodes.
The underload algorithm checks all nodes in a cluster that haven’t been prohibited by rules for underload every minute. If a node is loaded less than the threshold value allows, all instances are migrated from underloaded host and it is transferred to ACPIS3 state. We have created a filter that doesn’t allow migrations to a host that is in ‘suspended’ or ‘suspending’ state.
There are three possible values for the field suspend_state of VM:
«Active» – the node is not suspended
«Suspending» – all VMs are migrating from this node and it will be suspended when they successfully finish
«Suspended» – the node is suspended

Input:
A list of active compute nodes
Acceptable lower threshold values of CPU and RAM

Algorithm description:

* Create an overall list of VMs on all active nodes
* Aggregate values for CPU and RAM on each node
     * If CPU or RAM value on any host is less than the threshold value, make a decision to suspend it

      * Field suspend_state in table compute_nodes is changed from «active» to «suspending».

      * Method «migrate_all_vms_from_host» is called in order to migrate all VMs from the host
      * A method checking if all VMs have been migrated from the host is run every minute

       1. Load information about suspending compute nodes
       2. Look through all these nodes and create a list of active migrations from them

        3.1 If all migrations of turned off VMs are in ‘finished' state, confirm the migration by calling “confirm_migration()” method

        3.2 If there are no more active migrations on nodes:

         3.2.1. and the host is empty, store the MAC-address of the interface, that will be used when the node is transferred into ‘active’ state to database, suspend the host and store ‘suspended’ state to database

         3.2.2. and there are VMs on the host, that cannot be migrated, store ‘active’ state to database

    Program Netifaces is used for getting MAC-address.

    Description of Netifaces:

    It looks for the IP-address among all interfaces. If the right interface is found, the program gets its MAC-address and sends a ‘suspend’ call to the host.

* The state is changed from «suspending» to «suspended».

      * If the mean of CPU or RAM load in the cluster is greater than the configuration parameters «unsuspend_cpu» or «unsuspend_memory», the algorithm of checking for overload is run

       * If there is an overload, the first suspended node in the list is woken by «ether-wake» command, that gets MAC-address of the node from «mac_to_wake» field as a parameter

Alternatives
------------
None

Data model impact
=================

Create compute_node_stats table with the following columns:

* ‘id' - type: Integer, primary key;
* ‘compute_id' - type: Integer, references to compute_nodes(id), not null;
* 'memory_total' - type: Integer;
* 'cpu_used_percent' type: Integer;
* ‘updated_at' - type: DateTime
* 'deleted_at' - type: DateTime;
* 'created_at' - type: DateTime;
* 'deleted' - type: Integer;
* ‘memory_used' - type: Integer.

Create instance_stats table with the following columns:

* ‘id' - type: Integer, primary key;
* ‘instance_uuid' - type: Text, references to instances(uuid), not null;
* ‘libvirt_id' - type: Integer;
* ‘cpu_time' - type: BigInteger;
* ‘prev_cpu_time' - type: BigInteger;
* ‘mem' - type: Integer;
* ‘prev_updated_at' - type: DateTime;
* ‘updated_at' - type: DateTime;
* ‘deleted_at' - type: DateTime;
* ‘created_at' - type: DateTime;
* ‘deleted' - type: Integer;
* ‘block_dev_iops' - type: BigInteger;
* ‘prev_block_dev_iops' - type: BigInteger.

Add the following columns to compute_nodes table:

* ‘suspend_state' - type: Text
* ‘mac_to_wake' - type: Text

REST API impact
---------------

There are new API methods to handle:

‘Suspend node’:

Method: POST
PATH: /v2/{project_id}/loadbalancer/action
Request body:

{
    "suspend_host":

{

        "host": "compute3"

    }

}

‘Unsuspend node’:

Method: POST

PATH: /v2/{project_id}/loadbalancer/action

Request body:

{

    "unsuspend_host":

    {

        "host": "compute3"

    }

}

‘LB Get nodes stats’:

Method: GET

PATH: /v2/{project_id}/loadbalancer

Security impact
---------------
None

Notifications impact
--------------------

None

Other end user impact
---------------------

None

Performance Impact
------------------

There are new methods in Conductor API and Nova API, that do not affect performance of the system. We cannot say that workload of Conductor increases proportionally to the number of nodes, because we have methods of getting statistics from instances and methods related to rules. There is also a method responsible for deleting statistics of nodes for the last n seconds.

Other deployer impact
---------------------

None

Developer impact
----------------
None

Implementation
==============

Assignee(s)

Primary assignees:

Alexander Chadin (joker946)

https://launchpad.net/~joker946

Alexander Stavitskiy (alexstav)

https://launchpad.net/~alexstav

Other contributors:

None (but highly welcomed)

Work Items
==========
**Before starting LoadBalancer service make sure to perform the following actions:**

* Add executable file nova-loadbalancer.py:

File contents:

*#!/usr/bin/python*

*# PBR Generated from u'console_scripts'*

*import sys*

*from nova.cmd.loadbalancer import main*

*if __name__ == "__main__":*
* sys.exit(main())*

This file should be added to folder usr/bin/

* And provide the following privileges to user root:

*root@vm:~# chmod 775 /usr/bin/nova-loadbalancer*

* Specify password for user nova in file /usr/lib/python2.7/site-packages/nova/loadbalancer/utils.py

The following files on the compute node should be updated:

* nova/compute/manager.py

* nova/compute/resource_tracker.py

* nova/virt/libvirt/driver.py

**Turn on  VM live migration support:**

On NFS server/controller follow these steps:

1. Install NFS server (using package manager of your operating system, in this case apt-get):

*root@vm:~# apt-get install nfs-kernel-server*

2. IDMAPD extends functionality of NFSv4 core for client and server, converting user and group id into their names and back. File /etc/default/nfs-kernel-server should be edited and the specified parameter should be assigned value yes. This file needs to be the same on client and on NFS server:

*NEED_IDMAPD=yes # only needed for Ubuntu 11.10 and earlier*

3. File /etc/idmapd.conf should include the following lines:

*[Mapping]*

*Nobody-User = nobody*

*Nobody-Group = nogroup*

4. To provide controller with general access to nodes /var/lib/nova/instances, the following line should be added to /etc/exports:

*192.168.122.0/24(rw,fsid=0,insecure,no_subtree_check,async,no_root_squash)*

Where 192.168.122.0/24 – network address of the node, on which nfs-server is launched in your OpenStack cluster.

5. Execution rights should be given to your shared catalog so that qemu could use images from directories that have been exported to compute nodes:

*root@vm:~# chmod o+x /var/lib/nova/instances*

6. Services should be reloaded:

*root@vm:~# service nfs-kernel-server restart*

*root@vm:~# /etc/init.d/idmapd restart*

**The following actions should be performed on each compute node:**

1. Make sure there is SSH access between hosts without password or Strict Host Key Checking. Direct access between hosts is required for sending files between VMs.

2. Install NFS client services:

*root@vm:~#apt-get install nfs-common*

3. In file /etc/default/nfs-common the specified parameter should be assigned value yes:

*NEED_IDMAPD=yes # only needed for Ubuntu 11.10 or earlier*

4. Plug in the remote folder from NFS server:

*root@vm:~#mount NFS-SERVER:/var/lib/nova/instances /var/lib/nova/instances*

Where NFS-SERVER is the hostname/ip-address of the NFS server

5. In order to avoid repeating these steps after every restart, add the following line to /etc/fstab:

*nfs-server:/ /var/lib/nova/instances nfs auto 0 0*

6. Make sure that privileges are provided as shown below on all nodes. This means that the right permissions are given on controller using chmod+X command:

*root@vm:~# ls -ld /var/lib/nova/instances/*

*drwxr-xr-x 8 nova nova 4096 Oct 3 12:41 /var/lib/nova/instances/*

6. Make sure that exported directory can be connected and verify that it has been plugged in:

*root@vm:# mount –a -v*

*root@vm:~# df -k*

*Filesystem 1K-blocks Used Available Use% Mounted on*

*/dev/vda1 6192704 1732332 4145800 30% /*

*udev 1991628 4 1991624 1% /dev*

*tmpfs 800176 284 799892 1% /run*

*none 5120 0 5120 0% /run/lock*

*none 2000432 0 2000432 0% /run/shm*

*cgroup 2000432 0 2000432 0% /sys/fs/cgroup*

*vm:/var/lib/nova/instances 6192896 2773760 3104512 48%/var/lib/nova/instances*

**The last line is necessary.** It shows that /var/lib/nova/instances has been successfully exported from NFS server. If it's not there, your NFS may be working incorrectly and it should be fixed before carrying on.

8. Libvirt configuration should be changed by updating or adding the following lines in file /etc/libvirt/libvirtd.conf:

*before : #listen_tls = 0*

*after : listen_tls = 0*

*before : #listen_tcp = 1*

*after : listen_tcp = 1*

*add: auth_tcp = "none"*

9. The following lines should be updated or added in /etc/init/libvirt-bin.conf:

*before : exec /usr/sbin/libvirtd -d*

*after : exec /usr/sbin/libvirtd -d -l*

10. The following lines should be updated or added in /etc/default/libvirt-bin:

*before :libvirtd_opts=" -d"*

*after :libvirtd_opts=" -d -l"*

11. Libvirt should be restarted. After that make sure that restart was successful:

*root@vm# stop libvirt-bin && start libvirt-bin*

*root@vm# ps -ef | grep libvirt*

Verify that the following commands work:

* live-migration

* migrate

* resize

* resize-confirm

You can see instruction for working with any of those commands using

*root@vm:~# nova help <COMMAND>*

where COMMAND is one of the commands from the list above.

Dependencies
------------

Libraries:

* Psutil
* Dateutil

Testing
=======
Description of the situation and steps for achieving expected result
Description of the expected result
There are two nodes with several VMs on each of them.
The node can be in one of three states:
«Active» – the node is not suspended
«Suspending» – the node is being suspended
«Suspended» – the node is suspended
When LB service is running, suspend one of the nodes:

root@vm:~# nova lb-suspend <hostname>

VMs have been successfully migrated to the second node, the first node is suspended

root@vm:~# nova list --fields name,host - to list VMs on this node

There are two nodes, one of them contains several VMs (slight load). The other node is empty. LB service is running.
The empty node should be suspended if the the other node is slightly loaded (Underload algorithm)

Documentation Impact
====================
None

References
==========
https://launchpad.net/nova-loadbalancer – home page.
https://github.com/joker946/nova/commits/drs – juno tree
https://github.com/Stavitsky/nova/commits/loadbalancer-client – kilo tree