#!/usr/bin/env python3
import json
import sys
import os
import getpass
import argparse

from cisco_gnmi import ClientBuilder


class GetState:
    def __init__(self, target, username, password, verify=True):
        builder = ClientBuilder(target)
        builder.set_secure_from_target()
        if not verify:
            builder.set_ssl_target_override()
        builder.set_call_authentication(username, password)
        self.client = builder.construct()
        capabilities = self.client.capabilities()

    def get_bgp_neighbors(self):
        ret = []
        get_path = self.client.parse_xpath_to_gnmi_path(
            "/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state/session-state")
        res = self.client.get(paths=[get_path], data_type="STATE", encoding="JSON_IETF")

        for e in res.notification[0].update:
            ret.append({
                "vrf_name": e.path.elem[1].key['name'],
                "neighbor_addr": e.path.elem[6].key['neighbor-address'],
                "session_state": e.val.string_val
            })

        return ret

    def get_bgp_received_routes(self):
        # Workaround because some devices return address-families that are not
        # enabled, but showing 0 received routes. Make sure address-family is
        # enabled before returning such results
        enabled = {}
        get_path = self.client.parse_xpath_to_gnmi_path(
            "/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/afi-safis/afi-safi/config/enabled")
        res = self.client.get(paths=[get_path], data_type="STATE", encoding="JSON_IETF")
        for e in res.notification[0].update:
            vrf_name = e.path.elem[1].key['name']
            neighbor_addr = e.path.elem[6].key['neighbor-address']
            safi = e.path.elem[8].key['afi-safi-name']
            if vrf_name in enabled:
                vrf_data = enabled[vrf_name]
                if neighbor_addr in vrf_data:
                    neighbor_addr = vrf_data[neighbor_addr]
                    neighbor_addr[safi] = e.val.bool_val
                    vrf_data[neighbor_addr] = neighbor_addr
                else:
                    vrf_data[neighbor_addr] = {safi: e.val.bool_val}
                enabled[vrf_name] = vrf_data
            else:
                enabled[vrf_name] = {neighbor_addr: {safi: e.val.bool_val}}

        ret = []
        get_path = self.client.parse_xpath_to_gnmi_path(
            "/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/afi-safis/afi-safi/state/prefixes/received")
        res = self.client.get(paths=[get_path], data_type="STATE", encoding="JSON_IETF")

        for e in res.notification[0].update:
            try:
                vrf_name = e.path.elem[1].key['name']
                neighbor_addr = e.path.elem[6].key['neighbor-address']
                safi = e.path.elem[8].key['afi-safi-name']
                ret.append({
                    "vrf_name": vrf_name,
                    "neighbor_addr": neighbor_addr,
                    "safi": safi,
                    "enabled": enabled[vrf_name][neighbor_addr][safi],
                    "prefixes_received": e.val.uint_val,
                })
            except KeyError as e:
                pass

        return ret

    def get_lldp_neighbors(self):
        ret = []
        get_path = self.client.parse_xpath_to_gnmi_path(
            "/lldp/interfaces/interface/neighbors/neighbor/state/system-name")
        res = self.client.get(paths=[get_path], data_type="STATE", encoding="JSON_IETF")

        for e in res.notification[0].update:
            ret.append({
                "local_interface": e.path.elem[2].key['name'],
                "neighbor_name": e.val.string_val
            })

        return ret
    
    def run(self):
        output = {
            'bgp_neighbors': self.get_bgp_neighbors(),
            'bgp_received_routes': self.get_bgp_received_routes(),
            'lldp_neighbors': self.get_lldp_neighbors()
        }
        return output


def cli():
    parser = argparse.ArgumentParser("get current state of network device")
    parser.add_argument('targets', metavar='target', type=str, nargs='+',
                        help="Target devices in format: hostname:port")
    parser.add_argument('--output', default="text",
                        help="Output format: text, json")
    parser.add_argument('--insecure', action="store_false",
                        help="Accept self-signed certificates")
    args = parser.parse_args()

    try:
        username = os.environ['GRPC_USERNAME']
        password = os.environ['GRPC_PASSWORD']
    except KeyError as e:
        print("Environment variables GRPC_USERNAME and GRPC_PASSWORD not set")
        username = input("Username: ")
        password = getpass.getpass()

    output = {}
    for target in args.targets:
        gs = GetState(target, username, password, verify=args.insecure)
        output[target] = gs.run()
    
    if args.output == "json":
        print(json.dumps(output, indent=4))
    else:
        for target, target_data in output.items():
            hostname = target.split(':')[0]
            print("Hostname: {}".format(hostname))
            for key, value in target_data.items():
                for item in value:
                    print("{}: {}".format(key, item))


if __name__ == "__main__":
    cli()
