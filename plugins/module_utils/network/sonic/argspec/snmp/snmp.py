#
# -*- coding: utf-8 -*-
# Copyright 2024 Dell Inc. or its subsidiaries. All Rights Reserved.
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
The arg spec for the sonic_snmp module
"""


class SnmpArgs(object):  # pylint: disable=R0903
    """The arg spec for the sonic_snmp module
    """

    def __init__(self, **kwargs):
        pass

    argument_spec = {
       'config': {
              'options': {
                     'agentaddress': {
                            'elements': 'dict',
                            'options': {
                                   'interface': {'type': 'str'},
                                   'ip': {
                                          'required': True,
                                          'type': 'str'
                                          },
                                   'port': {'type': 'int'},
                                   'vrf': {'type': 'str'}
                            },
                            'type': 'list'       
                     },
                     'community': {
                            'elements': 'dict',
                            'options': {
                                   'group': {'type': 'str'},
                                   'name': {
                                          'required': True,
                                          'type': 'str'
                                          }
                                   },
                                   'type': 'list'
                     },
                     'contact': {'type': 'str'},
                     'enable_trap': {
                            'choices': [
                                   'auth-fail',
                                   'bgp',
                                   'config-change',
                                   'link-down',
                                   'link-up',
                                   'ospf',
                                   'all'
                                   ],
                            'elements': 'str',
                            'type': 'list'
                     },
                     'engine': {'type': 'str'},
                     'group': {
                            'elements': 'dict',
                            'options': {
                                   'access': {
                                          'elements': 'dict',
                                          'options': {
                                                 'notify_view': {'type': 'str'},
                                                 'read_view': {'type': 'str'},
                                                 'security_level': {
                                                        'choices': [
                                                               'no-auth-no-priv',
                                                               'auth-no-priv',
                                                               'auth-priv'
                                                        ]
                                                 },
                                                 'security_model': {
                                                        'choices': [
                                                               'any',
                                                               'v2c',
                                                               'v3'
                                                        ],
                                                        'required': True,
                                                        'type': 'str'
                                                 },
                                                 'write_view': {'type': 'str'}
                                          },
                                          'type': 'list'
                                          },
                                          'name': {
                                                 'required': True,
                                                 'type': 'str'
                                          }
                                   },
                            'type': 'list'
                     },
                     'host': {
                            'elements': 'dict',
                            'options': {
                                   'community': {'type': 'str'},
                                   'ip': {
                                          'required': True,
                                          'type': 'str'
                                   },
                                   'port': {'type': 'int'},
                                   'retries': {'type': 'int'},
                                   'source_interface': {'type': 'str'},
                                   'tag': {
                                          'choices': ['inform', 'trap'],
                                          'type': 'str'
                                   },
                                   'timeout': {'type': 'int'},
                                   'user': {
                                          'options': {
                                                 'name': {
                                                        'required': True,
                                                        'type': 'str'
                                                 },
                                                 'security_level': {
                                                        'choices': [
                                                               'auth',
                                                               'noauth',
                                                               'priv'
                                                        ],
                                                        'type': 'str'
                                                 }
                                          },
                                          'type': 'dict'
                                   },
                                   'vrf': {'type': 'str'}
                            },
                            'type': 'list'
                     },
                     'location': {'type': 'str'},
                     'user': {
                            'elements': 'dict',
                            'options': {
                                   'group': {'type': 'str'},
                                   'name': {
                                          'required': True,
                                          'type': 'str'
                                   },
                                   'auth': {
                                          'options': {
                                                 'auth_type': {
                                                        'choices': [
                                                               'md5',
                                                               'sha'
                                                        ],
                                                        'type': 'str'
                                                 },
                                                 'key': {'type': 'str'},
                                          },
                                          'type': 'dict'
                                   },
                                   'priv': {
                                          'options': {
                                                 'priv_type': {
                                                        'choices': [
                                                               'des',
                                                               'aes'
                                                        ],
                                                        'type': 'str'
                                                 },
                                                 'key': {'type': 'str'},
                                          },
                                          'type': 'dict'
                                   },
                                   'encryption': {'type': 'bool'}
                            },
                            'type': 'list'
                            },
                     'view': {
                            'elements': 'dict',
                            'options': {
                                   'excluded': {
                                          'elements': 'str',
                                          'type': 'list'
                                   },
                                   'included': {
                                          'elements': 'str',
                                          'type': 'list'
                                   },
                                   'name': {
                                          'required': True,
                                          'type': 'str'
                                   }
                            },
                            'type': 'list'
                     }
              },
            'type': 'dict'
       },
       'state': {
              'choices': ['merged', 'deleted', 'replaced', 'overridden'],
              'default': 'merged',
              'type': 'str'
       }
    }  # pylint: disable=C0301
