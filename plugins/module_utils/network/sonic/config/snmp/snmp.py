#
# -*- coding: utf-8 -*-
# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The sonic_snmp class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
from __future__ import absolute_import, division, print_function
import base64
import secrets
import string
__metaclass__ = type

from copy import deepcopy
from ansible.module_utils.connection import ConnectionError

from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.cfg.base import ConfigBase

from ansible_collections.dellemc.enterprise_sonic.plugins.module_utils.network.sonic.facts.facts import Facts
from ansible_collections.dellemc.enterprise_sonic.plugins.module_utils.network.sonic.sonic import (
    to_request,
    edit_config,
)
from ansible_collections.dellemc.enterprise_sonic.plugins.module_utils.network.sonic.utils.utils import (
    update_states,
    get_diff,
    get_replaced_config,
    send_requests
)

from ansible_collections.dellemc.enterprise_sonic.plugins.module_utils.network.sonic.utils.formatted_diff_utils import (
    get_new_config,
    get_formatted_config_diff
)

from plugins.module_utils.network.sonic.facts.snmp.snmp import SnmpAutoGeneratedValues

PATCH = 'patch'
DELETE = 'delete'


class Snmp(ConfigBase):
    """
    The sonic_snmp class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'snmp',
    ]

    def __init__(self, module):
        super(Snmp, self).__init__(module)

    def get_snmp_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        snmp_facts = facts['ansible_network_resources'].get('snmp')

        if not snmp_facts:
            return []

        return snmp_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()

        existing_snmp_facts = self.get_snmp_facts()
        commands, requests = self.set_config(existing_snmp_facts)

        if commands and requests:
            if not self._module.check_mode:
                try:
                    edit_config(self._module, to_request(self._module, requests))
                except ConnectionError as exc:
                    self._module.fail_json(msg=str(exc), code=exc.code)
            result['changed'] = True
        result['commands'] = commands

        changed_snmp_facts = self.get_snmp_facts()
        result['before'] = existing_snmp_facts
        if result['changed']:
            result['after'] = changed_snmp_facts

        new_config = changed_snmp_facts
        old_config = existing_snmp_facts
        if self._module.check_mode:
            result.pop('after', None)
            new_config = get_new_config(commands, existing_snmp_facts)
            result['after(generated)'] = new_config
        if self._module._diff:
            result['diff'] = get_formatted_config_diff(old_config, new_config, self._module._verbosity)

        result['warnings'] = warnings

        return result

    def set_config(self, existing_snmp_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_snmp_facts
        resp = self.set_state(want, have)
        return resp

    def set_state(self, want, have):
        """ Select the appropriate function based on the state provided

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        requests = []
        state = self._module.params['state']

        if state == 'overridden':
            commands, requests = self._state_overridden(want, have)
        elif state == 'deleted':
            commands, requests = self._state_deleted(want, have)
        elif state == 'merged':
            commands, requests = self._state_merged(want, have)
        elif state == 'replaced':
            commands, requests = self._state_replaced(want, have)

        return commands, requests

    def _state_replaced(self, want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands, requests = [], []
        replaced_config = get_replaced_config(want, have)

        if replaced_config:
            requests = self.get_delete_snmp_request(replaced_config, have, False)

            send_requests(self._module, requests)
            commands = want
        else:
            commands = get_diff(want, have)

        requests = []
        if commands:
            requests = self.get_create_snmp_request(commands)
            if len(requests) > 0:
                commands = update_states(commands, "replaced")
            else:
                commands = []
        else:
            commands = []

        return commands, requests

    def _state_overridden(self, want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """

        if have and have != want:
            requests = self.get_delete_snmp_request(have, have, False)
            send_requests(self._module, requests)
            have = []

        commands, requests = [], []

        if not have and want:
            commands = want
            requests = self.get_create_snmp_request(commands)

            if requests:
                commands = update_states(commands, "overridden")
            else:
                commands = []

        return commands, requests

    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = get_diff(want, have)
        requests = self.get_create_snmp_request(commands)

        if commands and requests:
            commands = update_states(commands, "merged")
        else:
            commands = []

        return commands, requests

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands, requests = [], []
        delete_all = False

        if not want:
            commands = deepcopy(have)
            delete_all = True
        else:
            commands = deepcopy(want)

        requests = self.get_delete_snmp_request(commands, dict(have), delete_all)

        if commands and requests:
            commands = update_states(commands, 'deleted')
        else:
            commands = []

        return commands, requests

    def get_create_snmp_request(self, config):
        """ Create the requests necessary to create the desired configuration

        :rtype: A list
        :returns: the requests necessary to create the desired configuration
        """
        requests = []
        method = PATCH

        if config.get('agentaddress'):
            agentaddress_path = 'data/ietf-snmp:snmp/engine'
            payload = self.build_create_agentaddress_payload(config)
            agentaddress_request = {'path': agentaddress_path, 'method': method, 'data': payload}
            requests.append(agentaddress_request)

        if config.get('community'):
            community_path = 'data/ietf-snmp:snmp/community'
            payload = self.build_create_community_payload(config)
            community_request = {'path': community_path, 'method': method, 'data': payload}
            requests.append(community_request)
            group_path = 'data/ietf-snmp:snmp/vacm'
            payload = self.build_create_group_community_payload(config)
            group_request = {'path': group_path, 'method': method, 'data': payload}
            requests.append(group_request)

        if config.get('contact'):
            contact_path = 'data/ietf-snmp:snmp/ietf-snmp-ext:system/contact'
            payload = self.build_create_contact_payload(config)
            contact_request = {'path': contact_path, 'method': method, 'data': payload}
            requests.append(contact_request)

        if config.get('enable_trap'):
            enable_trap_path = 'data/ietf-snmp:snmp/ietf-snmp-ext:system'
            payload = self.build_create_enable_trap_payload(config)
            enable_trap_request = {'path': enable_trap_path, 'method': method, 'data': payload}
            requests.append(enable_trap_request)

        if config.get('engine'):
            engine_path = 'data/ietf-snmp:snmp/engine'
            payload = self.build_create_engine_payload(config)
            engine_request = {'path': engine_path, 'method': method, 'data': payload}
            requests.append(engine_request)

        if config.get('group'):
            group_path = 'data/ietf-snmp:snmp/vacm/group'
            payload = self.build_create_group_payload(config)
            group_request = {'path': group_path, 'method': method, 'data': payload}
            requests.append(group_request)
#
        if config.get('host'):
            target_path = 'data/ietf-snmp:snmp/target'
            payload = self.build_create_enable_target_payload(config)
            target_request = {'path': target_path, 'method': method, 'data': payload}
            requests.append(target_request)
            server_params_path = 'data/ietf-snmp:snmp/target-params'
            payload = self.build_create_enable_target_params_payload(config)
            target_params_request = {'path': server_params_path, 'method': method, 'data': payload}
            requests.append(target_params_request)

        if config.get('location'):
            location_path = 'data/ietf-snmp:snmp/ietf-snmp-ext:system/location'
            payload = self.build_create_location_payload(config)
            location_request = {'path': location_path, 'method': method, 'data': payload}
            requests.append(location_request)

        if config.get('user'):
            user_path = 'data/ietf-snmp:snmp/usm/local/user'
            payload = self.build_create_user_payload(config)
            users_request = {'path': user_path, "method": method, 'data': payload}
            requests.append(users_request)
            vacm_path = 'data/ietf-snmp:snmp/vacm'
            vacm_payload = self.build_create_vacm_payload(config)
            users_request = {'path': vacm_path, "method": method, 'data': vacm_payload}
            requests.append(users_request)

        if config.get('view'):
            views_path = 'data/ietf-snmp:snmp/vacm/view'
            payload = self.build_create_view_payload(config)
            views_request = {'path': views_path, 'method': method, 'data': payload}
            requests.append(views_request)

        return requests

    def build_create_agentaddress_payload(self, config):
        """ Build the payload for SNMP agentaddress

        :rtype: A dictionary
        :returns: The payload for SNMP agentaddress
        """
        agentaddress = config.get('agentaddress', None)
        agentaddress_list = list()
        payload_url = dict()
        for conf in agentaddress:
            agentaddress_dict = dict()
            agentaddress_dict['name'] = self.get_agententry()
            agentaddress_dict['udp'] = {'ietf-snmp-ext:interface': conf.get('interface'), 'ip': conf.get('ip'), 'port': conf.get('port')}
            agentaddress_list.append(agentaddress_dict)

        payload_url['listen'] = agentaddress_list
        return payload_url

    def build_create_community_payload(self, config):
        """ Build the payload for SNMP community

        :rtype: A dictionary
        :returns: The payload for SNMP community
        """
        community = config.get('community', None)
        community_list = list()
        payload_url = dict()

        for conf in community:
            community_dict = dict()
            community_dict['index'] = conf.get('name')
            community_dict['security-name'] = conf.get('group')
            community_list.append(community_dict)
        payload_url['community'] = community_list
        return payload_url
 
    def build_create_group_community_payload(self, config):
        """ Build the payload for the group associated with SNMP community

        :rtype: A dictionary
        :returns: The payload for the group associated with SNMP community
        """
        community = config.get('community', None)
        community_list = list()
        payload_url = dict()

        for conf in community:
            group_dict = dict()
            group_dict['group'] = {'name': conf.get('group')}
            group_dict['member'] = {'security-model': 'v2c', 'security-name': conf.get('name')}
            community_list.append(group_dict)
        payload_url['group'] = community_list

        return payload_url

    def build_create_engine_payload(self, config):
        """ Build the payload for SNMP engine

        :rtype: A dictionary
        :returns: The payload for SNMP engine
        """
        engine = config.get('engine', None)
        engine_list = list()
        payload_url = dict()

        for conf in engine:
            engine_dict = dict()
            engine_dict['engine-id'] = conf
            engine_list.append(engine_dict)

        payload_url['engine'] = engine_list
        return payload_url

    def build_create_user_payload(self, config):
        """ Build the payload for SNMP user

        :rtype: A dictionary
        :returns: The payload for SNMP user
        """
        user = config.get('user', None)
        user_list = list()
        payload_url = dict()

        for conf in user:
            user_dict = dict()

            characters = string.ascii_letters + string.digits
            random_auth_key = ''.join(secrets.choice(characters) for a in range(55))
            encoded_auth_key = base64.b64encode(random_auth_key.encode()).decode()

            characters = string.ascii_letters + string.digits
            random_priv_key = ''.join(secrets.choice(characters) for a in range(55))
            encoded_priv_key = base64.b64encode(random_priv_key.encode()).decode()
            auth_key = dict()
            priv_key = dict()
            auth_dict = dict()
            priv_dict = dict()
            auth_type = conf['auth'].get('auth_type')
            priv_type = conf['priv'].get('priv_type')
            auth_key['key'] = encoded_auth_key
            priv_key['key'] = encoded_priv_key

            auth_dict[auth_type] = auth_key
            priv_dict[priv_type] = priv_key
            priv_key = conf['priv'].get('priv_type') + "Key"
            user_dict['auth'] = auth_dict
            user_dict['priv'] = priv_dict
            user_dict['name'] = conf.get('name')

            if conf.get('encryption') is None:
                user_dict['ietf-snmp-ext:encrypted'] = True
            else:
                user_dict['ietf-snmp-ext:encrypted'] = conf.get('encryption')
            user_list.append(user_dict)

        payload_url['user'] = user_list
        return payload_url

    def build_create_vacm_payload(self, config):
        """ Build the payload for SNMP group members based on the given user information

        :rtpe: A dictionary
        :returns: The payload for SNMP group members
        """
        group_list = list()
        group = config.get('user', None)

        payload_url = dict()

        for conf in group:
            group_dict = dict()
            member = dict()
            member['security-model'] = "usm"
            member['security-name'] = conf.get('name')
            group_dict['member'] = member
            group_dict['name'] = conf.get('group')

            group_list.append(group_dict)
        payload_url['group'] = group_list
        return payload_url

    def build_create_view_payload(self, config):
        """ Build the payload for SNMP view

        :rtype: A dictonary
        :returns: The payload for SNMP view
        """
        view_list = list()
        payload_url = dict()
        view = config.get('view', None)

        for conf in view:
            view_dict = dict()
            view_dict['name'] = conf.get('name')
            view_dict['include'] = conf.get('included')
            view_dict['exclude'] = conf.get('excluded')
            view_list.append(view_dict)
        payload_url['view'] = view_list
        return payload_url

    def build_create_contact_payload(self, config):
        """ Build the payload for SNMP contact

        :rtype: A dictionary
        :returns: The payload for SNMP contact
        """
        payload_url = dict()
        contact = config.get('contact', None)
        contact_list = list()

        contact_list.append({'contact': contact})
        payload_url['contact'] = contact_list
        return payload_url

    def build_create_location_payload(self, config):
        """ Build the payload for SNMP location

        :rtype: A dictionary
        :returns: The payload for SNMP location
        """
        payload_url = dict()
        location = config.get('location', None)

        payload_url['location'] = location
        return payload_url

    def build_create_enable_trap_payload(self, config):
        """ Build the payload for SNMP enable_trap

        :rtype: A dictionary
        :returns: The payload for SNMP enable_trap
        """
        payload_url = dict()
        enable_trap = config.get('enable_trap', None)
        enable_trap_list = list()

        for conf in enable_trap:
            enable_trap_dict = dict()
            trap_type = conf
            if trap_type:
                trap_type = trap_type[0]
                if trap_type == 'all':
                    enable_trap_dict['trap_enable'] = 'true'
                    enable_trap_list.append(enable_trap_dict)
                else:
                    notifications = dict()
                    if trap_type == 'auth-fail':
                        enable_trap_dict['authentication-failure-trap'] = 'true'
                    if trap_type == 'bgp':
                        enable_trap_dict['bgp_traps'] = 'true'
                    if trap_type == 'config-change':
                        enable_trap_dict['config-change-trap'] = 'true'
                    if trap_type == 'link-down':
                        enable_trap_dict['link-down-trap'] = 'true'
                    if trap_type == 'link-up':
                        enable_trap_dict['link-up-trap'] = 'true'
                    if trap_type == 'ospf':
                        enable_trap_dict['ospf-traps'] = 'true'
                    notifications['notifications'] = enable_trap_dict

                    enable_trap_list.append(notifications)

        payload_url['system'] = enable_trap_list
        return payload_url

    def build_create_group_payload(self, config):
        """ Build the payload for SNMP group

        :rtype: A dictionary
        :returns: The payload for SNMP group
        """
        payload_url = dict()
        group_list = []
        target_e = self.get_available_target() ## TODO: figure out how to get the next possible whne adding multiple
        group = config.get('group', None)
        for conf in group:
            group_dict = dict()
            group_dict['name'] = conf.get('name')

            access_dict = dict()

            access_dict['context'] = 'Default'
            access_dict['context-match'] = "exact"
            access_dict['notify-view'] = conf.get('access')[target_e].get('notify_view')
            access_dict['read-view'] = conf.get('access')[target_e].get('read_view')
            access_dict['writeView'] = conf.get('access')[target_e].get('write_view')

            security_level = conf.get('access')[target_e].get('security_level')
            security_model = conf.get('access')[target_e].get('security_model')
            if security_level is None:
                security_level = 'auth-priv'
            if security_model is None:
                security_model = 'usm'
            access_dict['security-level'] = security_level
            access_dict['security-model'] = security_model

            group_dict['access'] = access_dict
            group_list.append(group_dict)

        payload_url['group'] = group_list
        return payload_url

    def build_create_enable_target_payload(self, config):
        """ Build the payload for SNMP target information based on the given host configuration

        :rtype: A dictionary
        :returns: The payload for SNMP target
        """
        payload_url = dict()
        target_list = []
        target = config.get('host', None)

        for conf in target:
            target_dict = dict()

            target_dict['name'] = self.get_available_target()
            target_dict['retries'] = conf.get('retries')
            tag_list = list()
            if conf.get('tag'):
                tag_list.append(str(conf.get('tag')) + "Notify")
            target_dict["tag"] = tag_list

            target_dict['target-params'] = self.get_available_target()
            target_dict['timeout'] = conf.get('timeout')
            target_dict['udp'] = {'ip': conf.get('ip'), 'port': conf.get('port'), 'ietf-snmp-ext:vrf-name': conf.get('vrf')}
            target_dict['ietf-snmp-ext:source-interface'] = conf.get('source_interface')
            target_list.append(target_dict)

        payload_url['target'] = target_list

        return payload_url

    def build_create_enable_target_params_payload(self, config):
        """ Build the payload for SNMP param information based on the given host configuration

        :rtype: A dictionary
        :returns: The payload for SNMP target
        """
        payload_url = dict()
        target_params_list = []

        server = config.get('host', None)

        for conf in server:
            target_params_dict = dict()
            target_entry_name = self.get_available_target()
            target_params_dict['name'] = target_entry_name
            type_info = dict()
            if conf.get('user') is None:
                type_info['security-name'] = conf.get('community')
                target_params_dict['v2c'] = type_info
            else:
                server_level = conf.get('user').get('security_level', None)
                if server_level == "auth":
                    type_info['security-level'] = 'auth-no-priv'
                if server_level == "noauth":
                    type_info['security-level'] = 'no-auth-no-priv'
                if server_level == "priv":
                    type_info['security-level'] = 'auth-priv'
                type_info['user-name'] = conf.get('user').get('name')
                target_params_dict['usm'] = type_info

            target_params_list.append(target_params_dict)

        payload_url['target-params'] = target_params_list

        return payload_url

    def get_delete_snmp_request(self, configs, have, delete_all):
        """ Create the requests necessary to delete the given configuration

        :rtype: A list
        :returns: The list of requests to delete the given configuration
        """
        requests = []

        if not configs:
            return requests

        agentaddress_requests = []
        community_requests = []
        contact_requests = []
        enable_trap_requests = []
        engine_requests = []
        group_requests = []
        host_requests = []
        location_requests = []
        user_requests = []
        view_requests = []

        agentaddress = configs.get('agentaddress', None)
        community = configs.get('community', None)
        contact = configs.get('contact', None)
        enable_trap = configs.get('enable_trap', None)
        engine = configs.get('engine', None)
        group = configs.get('group', None)
        host = configs.get('host', None)
        location = configs.get('location', None)
        user = configs.get('user', None)
        view = configs.get('view', None)

        if have.get('agentaddress') is not None and (delete_all or agentaddress):
            for want in agentaddress:
                matched_agentaddress = next((each_snmp for each_snmp in have.get('agentaddress') if each_snmp['ip'] == want['id']), None)
                if matched_agentaddress:
                    name = self.get_delete_agententry(matched_agentaddress)
                    agentaddress_url = 'data/ietf-snmp:snmp/engine/listen={name}'.format(name)

                    agentaddress_request = {'path': agentaddress_url, 'method': DELETE}
                    agentaddress_requests.append(agentaddress_request)
        if have.get('community') is not None and (delete_all or community):
            for want in community:
                matched_community = next((each_snmp for each_snmp in have.get('community') if each_snmp['name'] == want['name']), None)
                if matched_community:
                    community_name = matched_community['name']
                    group_name = matched_community['group']
                    community_url = 'data/ietf-snmp:snmp/community={0}'.format(community_name)
                    community_request = {'path': community_url, 'method': DELETE}
                    community_requests.append(community_request)

                    group_community_url = 'data/ietf-snmp:snmp/vacm/group={0}'.format(group_name)
                    community_request = {'path': group_community_url, 'method': DELETE}
                    community_requests.append(community_request)

        if delete_all or contact:
            if have.get('contact') is not None:
                contact_url = 'data/ietf-snmp:snmp/ietf-snmp-ext:system/contact'
                contact_request = {'path': contact_url, 'method': DELETE}
                contact_request['data'] = contact
        if have.get('enable_trap') is not None and (delete_all or enable_trap):
            for want in enable_trap:
                matched_enable_trap = next((each_snmp for each_snmp in have.get('enable_trap') if each_snmp[0] == want[0]), None)
                enable_trap_url = ""
                if matched_enable_trap:
                    if matched_enable_trap == 'all':
                        enable_trap_url = 'data/ietf-snmp:snmp/ietf-snmp-ext:system/trap-enable'
                    if matched_enable_trap == 'link-down':
                        enable_trap_url = 'data/ietf-snmp:snmp/ietf-snmp-ext:system/notifications/link-down-trap'
                    if matched_enable_trap == 'link-up':
                        enable_trap_url = 'data/ietf-snmp:snmp/ietf-snmp-ext:system/notifications/link-up-trap'
                    if matched_enable_trap == 'config-change':
                        enable_trap_url = 'data/ietf-snmp:snmp/ietf-snmp-ext:system/notifications/config-change-trap'
                    if matched_enable_trap == 'ospf':
                        enable_trap_url = 'data/ietf-snmp:snmp/ietf-snmp-ext:system/notifications/ospf-traps'
                    if matched_enable_trap == 'bgp':
                        enable_trap_url = 'data/ietf-snmp:snmp/ietf-snmp-ext:system/notifications/bgp-traps'
                    if matched_enable_trap == 'auth-fail':
                        enable_trap_url = 'data/ietf-snmp:snmp/ietf-snmp-ext:system/notifications/authentication-failure-trap'

                    enable_trap_request = {'path': enable_trap_url, 'method': DELETE}
                    enable_trap_requests.append(enable_trap_request)

        if have.get('engine') is not None and (delete_all or engine):
            matched_engine = next((each_snmp for each_snmp in have.get('engine') if each_snmp['id'] == engine['id']), None)
            if matched_engine:
                engine_id = matched_engine['id']
                engine_url = 'data/ietf-snmp:snmp/engine'
                engine_request = {'path': engine_url, 'method': DELETE}
                engine_requests.append(engine_request)
        if have.get('group') is not None and (delete_all or group):
            for want in group:
                matched_group = next((each_snmp for each_snmp in have.get('group') if each_snmp['name'] == want['name']), None)
                if matched_group:
                    group_name = matched_group['name']
                    matched_access = self.get_matched_access(matched_group['access'], want['access'])[0]
                    group_url = 'data/ietf-snmp:snmp/vacm/group={0}'.format(group_name)
                    group_request = {'path': group_url, 'method': DELETE}
                    group_requests.append(group_request)
        ##
        if have.get('host') is not None and (delete_all or host):
            for want in host:
                matched_host, name = self.get_host(want=want, have=have)
                if matched_host is not None:
                    host_target_url = 'data/ietf-snmp:snmp/target={0}'.format(name)
                    host_request = {'path': host_target_url, 'method': DELETE}
                    host_requests.append(host_request)
                    host_target_params_url = 'data/ietf-snmp:snmp/target-params={0}'.format(name)
                    host_request = {'path': host_target_params_url, 'method': DELETE}
                    host_requests.append(host_request)
        if delete_all or location:
            if have.get('location') is not None:
                location_url = 'data/ietf-snmp:snmp/ietf-snmp-ext:system/location'
                location_request = {'path': location_url, 'method': DELETE}
                location_requests.append(location_request)
        if have.get('user') is not None and (delete_all or user):
            for want in user:
                matched_user = next((each_snmp for each_snmp in have.get('user') if each_snmp['name'] == want['name']), None)
                if matched_user:
                    user_name = matched_user['name']
                    user_url = 'data/ietf-snmp:snmp/usm/local/user={0}'.format(user_name)
                    user_request = {'path': user_url, 'method': DELETE}
                    user_requests.append(user_request)
                    group_name = matched_user['group']
                    group_url = 'data/ietf-snmp:snmp/vacm/gropup={0}'.format(group_name)
                    group_request = {'path': group_url, 'method': DELETE}
                    user_requests.append(group_request)

        if have.get('view') is not None and (delete_all or view):
            for want in view:
                matched_view = next((each_snmp for each_snmp in have.get('view') if each_snmp['name'] == want['name']), None)
                if matched_view:
                    view_name = matched_view['name']
                    view_url = 'data/ietf-snmp:snmp/vacm/view={0}'.format(view_name)
                    view_request = {'path': view_url, 'method': DELETE}
                    view_requests.append(view_request)

        if agentaddress_requests:
            requests.extend(agentaddress_requests)
        if community_requests:
            requests.extend(community_requests)
        if contact_requests:
            requests.extend(contact_requests)
        if enable_trap_requests:
            requests.extend(enable_trap_requests)
        if engine_requests:
            requests.extend(engine_requests)
        if group_requests:
            requests.extend(group_requests)
        if host_requests:
            requests.extend(host_requests)
        if location_requests:
            requests.extend(location_requests)
        if user_requests:
            requests.extend(user_requests)
        if view_requests:
            requests.extend(view_requests)

        return requests

    def get_matched_access(self, access_list, want_access):
        """ Finds and returns the access list that matches the wanted access list

        :rtype: A list
        :returns: the access list that matches the wanted access list
        """
        matched_access = list()
        for want in want_access:
            matched_want = next((each_access for each_access in access_list
                                 if each_access['security_model'] == want['security_model']
                                 and each_access['security_level'] == want['security_level']
                                 and each_access['read_view'] == want['read_view']
                                 and each_access['write_view'] == want['write_view']
                                 and each_access['notify_view'] == want['notify_view']), None)
            matched_access.append(matched_want)
        return matched_access

    def get_host(self, want, have):
        """ Finds and returns the host that matches the wanted host

        :rtype: A list
        :returns: the host that matches the wanted host
        """
        for each_host in have:
            if each_host['ip'] == want['ip']:
                return each_host, self.get_delete_target(each_host)
        return {}, ""

    def get_available_target(self):
        """ Get and return the first available targetEntry that is not already taken

        :rtype: str
        :returns: the first available targetEntry that is not already taken
        """
        all_hosts = SnmpAutoGeneratedValues.get_available_target()
        target = 1
        for host in all_hosts:
            current_target = "targetEntry" + str(target)
            if current_target != host['target-entry']:
                return current_target
            target = target + 1
        return "targetEntry" + str(target)

    def get_delete_target(self, current_host):
        """ Get the targetEntry of the given host config

        :rtype: str
        :returns: Get the targetEntry of the given host config
        """
        all_hosts = SnmpAutoGeneratedValues.get_available_target()

        for host in all_hosts:
            if host['host-info'] == current_host:
                return host['target-entry']
        return None

    def get_agententry(self):
        """ Get and return the first available agentEntry that is already taken

        :rtype: str
        :returns: the first available agentEntry that is not already taken    
        """
        all_agentaddresses = SnmpAutoGeneratedValues.get_agent_entry()

        agent = 1
        for agentaddress in all_agentaddresses:
            current_agententry = "AgentEntry"+str(agent)
            if current_agententry != agentaddress['agent-entry-name']:
                return current_agententry
            agent = agent + 1
        return "AgentEntry"+str(agent)

    def get_delete_agententry(self, current_agentaddress):
        """ Get the agentEntry of the given agentaddress config

        :rtype: str
        :returns: Get the agentEntry of the given agentaddress config   
        """
        all_agentaddresses = SnmpAutoGeneratedValues.get_agent_entry()

        for agentaddress in all_agentaddresses:
            if agentaddress['address'] == current_agentaddress:
                return agentaddress['agent-entry-name']
        return None