#
# -*- coding: utf-8 -*-
# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The sonic snmp fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type
from copy import deepcopy

from ansible_collections.ansible.netcommon.plugins.module_utils.network.common import utils

from ansible_collections.dellemc.enterprise_sonic.plugins.module_utils.network.sonic.argspec.snmp.snmp import SnmpArgs
from ansible_collections.dellemc.enterprise_sonic.plugins.module_utils.network.sonic.sonic import (
    to_request,
    edit_config
)
from ansible.module_utils.connection import ConnectionError


class SnmpFacts(object):
    """ The sonic snmp fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = SnmpArgs.argument_spec
        spec = deepcopy(self.argument_spec)
        if subspec:
            if options:
                facts_argument_spec = spec[subspec][options]
            else:
                facts_argument_spec = spec[subspec]
        else:
            facts_argument_spec = spec

        self.generated_spec = utils.generate_dict(facts_argument_spec)

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for snmp
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if connection:
            pass

        if not data:
            # Fetch data from the current device configuration
            # (Skip if operating on previously fetched configuraation)
            data = self.get_all_snmps()

        snmps = dict()
        for key, value in data.items():
            if value:
                value = self.render_config(self.generated_spec, value)
                if value:
                    options = {key: value}
                    snmps.update(options)

        facts = {}
        if snmps:
            facts['snmp'] = dict()
            params = utils.validate_config(self.argument_spec, {'config': snmps})

            if params:
                facts['snmp'].update(params['config'])
        ansible_facts['ansible_network_resources'].update(facts)

        return ansible_facts

    def get_all_snmps(self):
        """
        Get all the snmp servers in the device
        """
        request = [{"path": "data/sonic-snmp:sonic-snmp", "method": "get"}]
        try:
            response = edit_config(self._module, to_request(self._module, request))
        except ConnectionError as exc:
            self._module.fail_json(msg=str(exc), code=exc.code)

        snmp_dict = dict()
        snmp_configs = dict()
        if len(response) == 0 or len(response[0]) == 0:
            return snmp_configs
        if "sonic-snmp:sonic-snmp" in response[0][1]:
            snmp_list = response[0][1].get("sonic-snmp:sonic-snmp", {})

            snmp_dict.update({'agentaddress': self.get_snmp_agentaddress(snmp_list)})
            snmp_dict.update({'community': self.get_snmp_community(snmp_list)})
            snmp_dict.update({'engine': self.get_snmp_engine(snmp_list)})
            snmp_dict.update({'user': self.get_snmp_users(snmp_list)})
            snmp_dict.update({'view': self.get_snmp_view(snmp_list)})
            snmp_dict.update({'contact': self.get_snmp_contact(snmp_list)})
            snmp_dict.update({'location': self.get_snmp_location(snmp_list)})
            snmp_dict.update({'enable_trap': list(self.get_snmp_enable_trap(snmp_list))})
            snmp_dict.update({'group': self.get_snmp_group(snmp_list)})
            host, targets_list, target_params = self.get_snmp_hosts_targets(snmp_list)
            snmp_dict.update({'host': host})

        if snmp_dict:
            snmp_configs = snmp_dict

        return snmp_configs

    def get_snmp_agentaddress(self, snmp_list):
        """
        Get snmp agent address from the snmp list
        """
        agentaddress_list = list()

        if not snmp_list.get('SNMP_AGENT_ADDRESS_CONFIG'):
            return agentaddress_list
        agentaddress_config = snmp_list['SNMP_AGENT_ADDRESS_CONFIG']['SNMP_AGENT_ADDRESS_CONFIG_LIST']

        for agentaddress in agentaddress_config:
            agentaddress_list.append({"interface": agentaddress.get("interface"), "ip": agentaddress.get("ip"), "port": agentaddress.get("port")})

        return agentaddress_list

    def get_snmp_community(self, snmp_list):
        """
        Get snmp community from the snmp list
        """
        community_list = list()

        if not snmp_list.get('SNMP_SERVER_COMMUNITY'):
            return community_list
        community_config = snmp_list['SNMP_SERVER_COMMUNITY']['SNMP_SERVER_COMMUNITY_LIST']

        for community in community_config:
            community_list.append({"name": community.get("index"), "group": community.get("securityName")})

        return community_list

    def get_snmp_engine(self, snmp_list):
        """
        Get snmp engine from the snmp list
        """
        engine = ''

        if not snmp_list.get('SNMP_SERVER_ENGINE'):
            return engine

        engine_config = snmp_list['SNMP_SERVER_ENGINE']['SNMP_SERVER_ENGINE_LIST']
        engine = engine_config[0]

        return engine

    def get_snmp_users(self, snmp_list):
        """
        Get snmp users from the snmp list
        """
        user_list = list()

        if not snmp_list.get('SNMP_SERVER_GROUP') or not snmp_list.get('SNMP_SERVER_USER'):
            return user_list

        group_config = snmp_list['SNMP_SERVER_GROUP']['SNMP_SERVER_GROUP_LIST']
        user_config = snmp_list['SNMP_SERVER_USER']['SNMP_SERVER_USER_LIST']

        for user in user_config:
            auth_type = "md5"
            auth_key = "md5Key"
            if user.get("md5Key") is None:
                auth_type = "sha"
                auth_key = "shaKey"

            priv_type = "aes"
            priv_key = "aes-128"
            if user.get("aesKey") is None:
                priv_type = "des"
                priv_key = "des"

            user_list.append({"group": group_config[0].get("name"),
                              "name": user.get("name"), "auth": {"auth_type": auth_type,
                                                                 "key": auth_key},
                                                                 "priv": {"priv_type": priv_type,
                                                                          "key": priv_key}, "encryption": "False"})

        return user_list

    def get_snmp_view(self, snmp_list):
        """
        Get snmp view from the snmp list
        """
        view_list = list()

        if not snmp_list.get('SNMP_SERVER_VIEW'):
            return view_list

        view_config = snmp_list['SNMP_SERVER_VIEW']['SNMP_SERVER_VIEW_LIST']

        for view in view_config:
            view_list.append({"name": view.get("name"), "included": view.get("include"), "excluded": view.get("exclude")})

        return view_list

    def get_snmp_contact(self, snmp_list):
        """
        Get snmp contact from the snmp list
        """
        contact_str = ""

        if not snmp_list.get('SNMP_SERVER'):
            return contact_str

        snmp_server_config = snmp_list['SNMP_SERVER']['SNMP_SERVER_LIST']

        if snmp_server_config:
            contact_str = snmp_server_config[0].get("sysContact")

        return contact_str

    def get_snmp_location(self, snmp_list):
        """
        Get snmp location from the snmp list
        """
        location_str = ""
        if not snmp_list.get('SNMP_SERVER'):
            return location_str

        snmp_server_config = snmp_list['SNMP_SERVER']['SNMP_SERVER_LIST']

        if snmp_server_config:
            location_str = snmp_server_config[0].get("sysLocation")

        return location_str

    def get_snmp_enable_trap(self, snmp_list):
        """
        Get snmp enable trap from the snmp list
        """
        enable_trap = list()
        if not snmp_list.get('SNMP_SERVER'):
            return enable_trap
        snmp_server_config = snmp_list['SNMP_SERVER']['SNMP_SERVER_LIST']

        for server in snmp_server_config:
            auth_fail_trap = server.get("authenticationFailureTrap")
            bgp_trap = server.get("bgpTraps")
            config_change_trap = server.get("configChangeTrap")
            link_down_trap = server.get("linkDownTrap")
            link_up_trap = server.get("linkUpTrap")
            ospf_trap = server.get("ospfTraps")
            all_trap = server.get("traps")

            if all_trap is None:
                if auth_fail_trap:
                    enable_trap.append("auth-fail")
                elif bgp_trap:
                    enable_trap.append("bgp")
                elif config_change_trap:
                    enable_trap.append("config-change")
                elif link_down_trap:
                    enable_trap.append("link-down")
                elif link_up_trap:
                    enable_trap.append("link-up")
                elif ospf_trap:
                    enable_trap.append("ospf")
            else:
                enable_trap.append("all")

        return enable_trap

    def get_snmp_group(self, snmp_list):
        """
        Get snmp group from the snmp list
        """
        group_list = list()
        access_list = list()
        if not snmp_list.get('SNMP_SERVER_GROUP_ACCESS'):
            return group_list

        snmp_group_list = snmp_list['SNMP_SERVER_GROUP_ACCESS']['SNMP_SERVER_GROUP_ACCESS_LIST']

        for group in snmp_group_list:
            access_list.append({"notify_view": group.get("notifyView"),
                                "read_view": group.get("readView"), "security_level": group.get("securityLevel"),
                                "security_model": group.get("securityModel"), "write_view": group.get("writeView")})

            group_list.append({"name": group.get("groupName"), "access": access_list})

        return group_list

    def get_snmp_hosts_targets(self, snmp_list):
        """
        Get snmp hosts and targets from the snmp list
        """
        host_list = list()
        targets_list = list()
        target_params = list()
        num_host = 0

        if not snmp_list.get('SNMP_SERVER_TARGET'):
            return host_list, targets_list, target_params

        server_params_config = snmp_list['SNMP_SERVER_PARAMS']['SNMP_SERVER_PARAMS_LIST']
        server_target_config = snmp_list['SNMP_SERVER_TARGET']['SNMP_SERVER_TARGET_LIST']

        for host in server_target_config:
            host_dict = dict()
            targets_dict = dict()
            target_params_dict = dict()
            user = server_params_config[num_host].get("user")
            if user is None:
                host_dict["community"] = server_params_config[num_host].get("securityNameV2")
            else:
                user_dict = dict()
                security_level = server_params_config[num_host].get("security-level")
                user_security_level = "auth"
                if security_level == 'no-auth-no-priv':
                    user_security_level = "noauth"
                if security_level == "no-auth-priv":
                    user_security_level = "priv"
                user_dict["security_level"] = user_security_level
                user_dict["name"] = server_params_config[num_host].get("user")
                host_dict["user"] = user_dict
            host_dict['ip'] = host.get("ip")
            host_dict['retries'] = host.get("retries")
            host_dict['port'] = host.get("port")
            host_dict['tag'] = host.get('tag')[0][:-6]
            host_dict['timeout'] = host.get("timeout")
            host_dict['source_interface'] = host.get("src_intf")
            if len(host.get("tag")) == 2:
                host_dict['vrf'] = host.get("tag")[1]

            host_list.append(host_dict)

            targets_dict['name'] = host.get('name')
            targets_dict['udp'] = {'port': host.get('port')}
            targets_dict['tag'] = host.get('tag')[0][:-6]
            targets_dict['target_params'] = host.get('targetParams')
            targets_dict['source_interface'] = host.get("src_intf")

            targets_list.append(targets_dict)

            target_params_dict['name'] = host.get('name')
            target_params_dict['v2c'] = {"security_name": server_params_config[num_host].get("securityNameV2")}
            target_params_dict['usm'] = {"user_name": server_params_config[num_host].get("user"),
                                         "security_level": server_params_config[num_host].get("security-level")}

        return host_list, targets_list, target_params

    def render_config(self, spec, conf):
        """
        Render config as dictionary structure and delete keys
          from spec for null values

        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        return conf

    def update_dict(self, dict, key, value, parent_key=None):
        if value not in [None, {}, [], ()]:
            if parent_key:
                dict[parent_key][key] = value
            else:
                dict[key] = value
        return dict

        