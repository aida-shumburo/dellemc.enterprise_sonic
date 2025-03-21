#
# -*- coding: utf-8 -*-
# Copyright 2024 Dell Inc. or its subsidiaries. All Rights Reserved
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#############################################
#                WARNING                    #
#############################################
#
# This file is auto generated by the resource
#   module builder playbook.
#
# Do not edit this file manually.
#
# Changes to this file will be over written
#   by the resource module builder.
#
# Changes should be made in the model used to
#   generate this file or in the resource module
#   builder template.
#
#############################################

"""
The arg spec for the sonic_bgp_af module
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class Bgp_afArgs(object):  # pylint: disable=R0903
    """The arg spec for the sonic_bgp_af module
    """

    def __init__(self, **kwargs):
        pass

    argument_spec = {
        'config': {
            'elements': 'dict',
            'options': {
                'address_family': {
                    'options': {
                        'afis': {
                            'elements': 'dict',
                            'options': {
                                'advertise_pip': {'type': 'bool'},
                                'advertise_pip_ip': {'type': 'str'},
                                'advertise_pip_peer_ip': {'type': 'str'},
                                'advertise_svi_ip': {'type': 'bool'},
                                'route_advertise_list': {
                                    'elements': 'dict',
                                    'options': {
                                        'advertise_afi': {
                                            'choices': ['ipv4', 'ipv6'],
                                            'required': True,
                                            'type': 'str'
                                        },
                                        'route_map': {
                                            'type': 'str'
                                        }
                                    },
                                    'type': 'list'
                                },
                                'advertise_all_vni': {'type': 'bool'},
                                'advertise_default_gw': {'type': 'bool'},
                                'afi': {
                                    'choices': ['ipv4', 'ipv6', 'l2vpn'],
                                    'required': True,
                                    'type': 'str'
                                },
                                'aggregate_address_config': {
                                    'elements': 'dict',
                                    'options': {
                                        'prefix': {'required': True, 'type': 'str'},
                                        'as_set': {'type': 'bool'},
                                        'policy_name': {'type': 'str'},
                                        'summary_only': {'type': 'bool'}
                                    },
                                    'type': 'list'
                                },
                                'rd': {'type': 'str'},
                                'rt_in': {'type': 'list', 'elements': 'str'},
                                'rt_out': {'type': 'list', 'elements': 'str'},
                                'vnis': {
                                    'elements': 'dict',
                                    'options': {
                                        'advertise_default_gw': {'type': 'bool'},
                                        'advertise_svi_ip': {'type': 'bool'},
                                        'rd': {'type': 'str'},
                                        'rt_in': {'type': 'list', 'elements': 'str'},
                                        'rt_out': {'type': 'list', 'elements': 'str'},
                                        'vni_number': {'required': True, 'type': 'int'}
                                    },
                                    'type': 'list'
                                },
                                'max_path': {
                                    'options': {
                                        'ebgp': {'type': 'int'},
                                        'ibgp': {'type': 'int'}
                                    },
                                    'type': 'dict'
                                },
                                'network': {'type': 'list', 'elements': 'str'},
                                'dampening': {'type': 'bool'},
                                'dup_addr_detection': {
                                    'options': {
                                        'enabled': {'type': 'bool'},
                                        'freeze': {'type': 'str'},
                                        'max_moves': {'type': 'int'},
                                        'time': {'type': 'int'}
                                    },
                                    'required_together': [['max_moves', 'time']],
                                    'type': 'dict'
                                },
                                'redistribute': {
                                    'elements': 'dict',
                                    'options': {
                                        'metric': {'type': 'str'},
                                        'protocol': {
                                            'choices': ['ospf', 'static', 'connected'],
                                            'required': True,
                                            'type': 'str'
                                        },
                                        'route_map': {'type': 'str'}
                                    },
                                    'type': 'list'
                                },
                                'import': {
                                    'options': {
                                        'vrf': {
                                            'options': {
                                                'vrf_list': {'type': 'list', 'elements': 'str'},
                                                'route_map': {'type': 'str'}
                                            },
                                            'type': 'dict'
                                        }
                                    },
                                    'type': 'dict'
                                },
                                'safi': {
                                    'choices': ['unicast', 'evpn'],
                                    'default': 'unicast',
                                    'type': 'str'
                                }
                            },
                            'required_together': [['afi', 'safi']],
                            'type': 'list'
                        }
                    },
                    'type': 'dict'
                },
                'bgp_as': {'required': True, 'type': 'str'},
                'vrf_name': {'default': 'default', 'type': 'str'}
            },
            'type': 'list'
        },
        'state': {
            'choices': ['merged', 'deleted', 'overridden', 'replaced'],
            'default': 'merged'
        }
    }  # pylint: disable=C0301
