# cnaas-state

This script will get the current state of network devices. You can run it before
and after a maintenance window/firmware upgrade etc and make a diff to make sure
nothing changed.

Requires gNMI with openconfig models.

To enable gNMI on Arista devices with self-signed certificate (don't use in production):

```
#security pki certificate generate self-signed grpc.crt key grpc.key generate rsa 4096
(config)#management api gnmi
   transport grpc def
      ssl profile grpc
      vrf MGMT
!
management security
   ssl profile grpc
      certificate grpc.crt key grpc.key
```

Run script (accept self-signed cert, don't use in production):
```
$ ./getstate.py 10.101.2.3:6030 --insecure
Overriding SSL option from certificate could increase MITM susceptibility!
Hostname: 10.101.2.3
bgp_neighbors: {'vrf_name': 'default', 'neighbor_addr': '10.101.0.0', 'session_state': 'ESTABLISHED'}
bgp_neighbors: {'vrf_name': 'default', 'neighbor_addr': '10.101.0.1', 'session_state': 'ESTABLISHED'}
bgp_neighbors: {'vrf_name': 'default', 'neighbor_addr': '10.101.1.2', 'session_state': 'ESTABLISHED'}
bgp_neighbors: {'vrf_name': 'default', 'neighbor_addr': '10.101.1.10', 'session_state': 'ESTABLISHED'}
bgp_received_routes: {'vrf_name': 'default', 'neighbor_addr': '10.101.0.0', 'safi': 'L2VPN_EVPN', 'enabled': True, 'prefixes_received': 7}
bgp_received_routes: {'vrf_name': 'default', 'neighbor_addr': '10.101.0.1', 'safi': 'L2VPN_EVPN', 'enabled': True, 'prefixes_received': 7}
bgp_received_routes: {'vrf_name': 'default', 'neighbor_addr': '10.101.1.2', 'safi': 'IPV4_UNICAST', 'enabled': True, 'prefixes_received': 4}
bgp_received_routes: {'vrf_name': 'default', 'neighbor_addr': '10.101.1.10', 'safi': 'IPV4_UNICAST', 'enabled': True, 'prefixes_received': 5}
lldp_neighbors: {'local_interface': 'Ethernet49/1', 'neighbor_name': 'c1'}
lldp_neighbors: {'local_interface': 'Ethernet48', 'neighbor_name': 'a2'}
lldp_neighbors: {'local_interface': 'Ethernet47', 'neighbor_name': 'a1'}
lldp_neighbors: {'local_interface': 'Ethernet50/1', 'neighbor_name': 'c2'}
```

Run once and pipe output to a file before maintenance, run again after
maintenance and pipe to a second file. Diff the two files to see if
something changed. You can specify multiple target devices in the same run,
see ./getstate.py -h.
