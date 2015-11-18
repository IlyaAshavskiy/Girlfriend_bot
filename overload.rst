=============
Overload spec
=============
Problem description
===================
Sometimes one of the nodes gets overloaded on cpu or ram because of high libvirt workload. In this case cloud operator should migrate some virtual machines from the overloaded node to the others. OpenStack Compute Load Balancer is developed to optimize resource usage in compute nodes, reduce response time and energy usage.
Use Cases
----------
As a cloud operator I can start the overload algorithm in a cluster and its workload will be distributed.
As a developer I can implement my own algorithms for detecting overload in a cluster.
As an end user I'm not affected by this change and won't notice any difference.
Proposed change
===============
We are going to propose creating a new algorithm for detecting overload in a cluster and distributing workload in case of overload. It will communicate with nova-conductor, nova-scheduler and nova-compute while balancing VMs among compute-nodes.

Algorithm for computing standard deviation
Input:
A list of active compute nodes
Acceptable standard deviations of CPU and RAM
Algorithm description:
For each active compute node get a list of VMs
Create an overall list of VMs on active nodes
Create a dictionary, its keys are hostnames and values are dictionaries containing two pairs: RAM and CPU
Values CPU and RAM are summed values of CPU and RAM for all VMs on the host
Compute the ratio between occupied resources and total resources for each node

Example:
    {
        'compute1': {'cpu': 0.13, 'ram': 0.38},
        'compute2': {'cpu': 0.15, 'ram': 0.48}'
    }

Compute the mean of CPU and RAM among hosts
For each parameter compute standard deviation according to the formula:
i∈H(xi−mean)2n
Is any value greater than the acceptable standard deviation?
If it is, we have found the overloaded host
If CPU is greater than the acceptable value, add CPU_overload key to extra_info, which means that  minRAM maxCPU algorithm should be used
Output of standard deviation algorithm:
The node that VMs should be migrated from.


.. list-table:: Summary
   :header-rows: 1

   * - Advantages
     - Disadvantages
   * - High adaptability to workload changes in a cluster
     - Harder to implement as compared with the threshold algorithm
     - Perspectively can provide an opportunity to dynamically scale the cluster
     - Requires additional computation of acceptable standard deviations, based on the number of compute nodes in the cluster


After any one of these two algorithms finishes working we get the specific host that the migration will be performed from.

Alternatives
------------
Other overload algorithms may be implemented, for example:
Threshold algorithm
Input:
A list of active compute nodes
Acceptable threshold values of CPU and RAM
Complexity of the algorithm:
O(n) (does not include querying the database)
Algorithm description:
Iteratively look through all compute nodes
For each node get its CPU and RAM loads (%)
Compare them with threshold values of CPU and RAM
If one of the values is greater than the threshold value, make decision to migrate
Otherwise move on to the next host

Output:
The node that VMs should be migrated from, otherwise None

.. list-table:: Summary
   :header-rows: 1

   * - Advantages
     - Disadvantages
   * - Simple to implement
     - The threshold values are constants and cannot be dynamically changed. That's why this algorithm is poorly adaptive to workload changes in a cluster.






Data model impact
-----------------
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

REST API impact
---------------
There are new API methods to handle:
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
-----------
Primary assignees:
Alexander Chadin (joker946)
https://launchpad.net/~joker946
Alexander Stavitskiy (alexstav)
https://launchpad.net/~alexstav
Other contributors:
None (but highly welcomed)
Work Items
==========
Before starting LoadBalancer service make sure to perform the following actions:
Add executable file nova-loadbalancer.py:
File contents:
#!/usr/bin/python
# PBR Generated from u'console_scripts'

import sys

from nova.cmd.loadbalancer import main


if __name__ == "__main__":
 sys.exit(main())

This file should be added to folder usr/bin/
And provide the following privileges to user root:
root@vm:~# chmod 775 /usr/bin/nova-loadbalancer

Specify password for user nova in file /usr/lib/python2.7/site-packages/nova/loadbalancer/utils.py

The following files on the compute node should be updated:
nova/compute/manager.py
nova/compute/resource_tracker.py
nova/virt/libvirt/driver.py

Turn on  VM live migration support:

On NFS server/controller follow these steps:
Install NFS server (using package manager of your operating system, in this case apt-get):
root@vm:~# apt-get install nfs-kernel-server
IDMAPD extends functionality of NFSv4 core for client and server, converting user and group id into their names and back. File /etc/default/nfs-kernel-server should be edited and the specified parameter should be assigned value yes. This file needs to be the same on client and on NFS server:
NEED_IDMAPD=yes # only needed for Ubuntu 11.10 and earlier

File /etc/idmapd.conf should include the following lines:
[Mapping]

Nobody-User = nobody
Nobody-Group = nogroup

To provide controller with general access to nodes /var/lib/nova/instances, the following line should be added to /etc/exports:
192.168.122.0/24(rw,fsid=0,insecure,no_subtree_check,async,no_root_squash)
Where 192.168.122.0/24 – network address of the node, on which nfs-server is launched in your OpenStack cluster.
Execution rights should be given to your shared catalog so that qemu could use images from directories that have been exported to compute nodes:
root@vm:~# chmod o+x /var/lib/nova/instances
Services should be reloaded:
root@vm:~# service nfs-kernel-server restart
root@vm:~# /etc/init.d/idmapd restart
The following actions should be performed on each compute node:
Make sure there is SSH access between hosts without password or Strict Host Key Checking. Direct access between hosts is required for sending files between VMs.
Install NFS client services:
root@vm:~#apt-get install nfs-common

In file /etc/default/nfs-common the specified parameter should be assigned value yes:
NEED_IDMAPD=yes # only needed for Ubuntu 11.10 or earlier

Plug in the remote folder from NFS server:
root@vm:~#mount NFS-SERVER:/var/lib/nova/instances /var/lib/nova/instances
Where NFS-SERVER is the hostname/ip-address of the NFS server

In order to avoid repeating these steps after every restart, add the following line to /etc/fstab:
nfs-server:/ /var/lib/nova/instances nfs auto 0 0

Make sure that privileges are provided as shown below on all nodes. This means that the right permissions are given on controller using chmod+X command:
root@vm:~# ls -ld /var/lib/nova/instances/
drwxr-xr-x 8 nova nova 4096 Oct 3 12:41 /var/lib/nova/instances/
Make sure that exported directory can be connected and verify that it has been plugged in:
root@vm:# mount –a -v
root@vm:~# df -k
Filesystem 1K-blocks Used Available Use% Mounted on
/dev/vda1 6192704 1732332 4145800 30% /
udev 1991628 4 1991624 1% /dev
tmpfs 800176 284 799892 1% /run
none 5120 0 5120 0% /run/lock
none 2000432 0 2000432 0% /run/shm
cgroup 2000432 0 2000432 0% /sys/fs/cgroup
vm:/var/lib/nova/instances 6192896 2773760 3104512 48% /var/lib/nova/instances

The last line is necessary. It shows that /var/lib/nova/instances has been successfully exported from NFS server. If it's not there, your NFS may be working incorrectly and it should be fixed before carrying on.
Libvirt configuration should be changed by updating or adding the following lines in file /etc/libvirt/libvirtd.conf:
before : #listen_tls = 0
after : listen_tls = 0

before : #listen_tcp = 1
after : listen_tcp = 1

add: auth_tcp = "none"



The following lines should be updated or added in /etc/init/libvirt-bin.conf:
before : exec /usr/sbin/libvirtd -d
after : exec /usr/sbin/libvirtd -d -l

The following lines should be updated or added in /etc/default/libvirt-bin:
before :libvirtd_opts=" -d"
after :libvirtd_opts=" -d -l"

Libvirt should be restarted. After that make sure that restart was successful:
root@vm# stop libvirt-bin && start libvirt-bin
root@vm# ps -ef | grep libvirt

Verify that the following commands work:
live-migration
migrate
resize
resize-confirm
You can see instruction for working with any of those commands using
root@vm:~# nova help <COMMAND>
where COMMAND is one of the commands from the list above.


Dependencies
============
Libraries:
Psutil
Dateutil
Testing
=======
Description of the situation and steps for achieving expected result
Description of the expected result
There are two nodes with several VMs on each of them.
Turn off balancing in /etc/nova/nova.conf
Manually migrate VMs from one node to another.
root@vm:~# nova live-migration <name> <hostname>
where name is what to migrate,
hostname is where to migrate to.
Make sure the second node is overloaded.
Turn on balancing in  /etc/nova/nova.conf

Workload has been successfully distributed among nodes.
Logs of node workloads are being written to file /var/log/nova/nova-loadbalancer.log

Documentation Impact
--------------------
None
References
----------
https://launchpad.net/nova-loadbalancer – home page.
https://github.com/joker946/nova/commits/drs – juno tree
https://github.com/Stavitsky/nova/commits/loadbalancer-client – kilo tree
