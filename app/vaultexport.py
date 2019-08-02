#!/usr/bin/env python

"""
vaultexport generates secret files from paths in KV. Supports 3 formats:
- key=value
- export key=value
- TOML: builds of the headings in the root of KV store
"""

import os
import sys
import argparse
import logging

from auth import auth
from secrets_engine import secrets_engine
from secrets_engine import kv_v2
from utils import helper
from constants import export_format

log = logging.getLogger('vaultexport')

class ReadableDir(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir=values
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentTypeError("readable_dir:{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            setattr(namespace,self.dest,prospective_dir)
        else:
            raise argparse.ArgumentTypeError("readable_dir:{0} is not a readable dir".format(prospective_dir))

def is_required_arg(arg):
    return arg in sys.argv

def _parse_argument():
    """ parse commandline input """
    parser = argparse.ArgumentParser(
        description='Generates secrets by pulling them from vault. Uses kubernetes SA to authenticate against backend',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # sub_parsers = parser.add_subparsers(help='sub command help')

    parser.add_argument(
        'secrets_engine',
        metavar='secrets-engine',
        help='Pulls secrets from KV2 backend',
        choices=secrets_engine.CHOICES,
    )

    parser.add_argument(
        '--mount-point',
        '-mp',
        default='kv',
        type=str,
        help='Backend KV mountpoint',
        required=is_required_arg('kv-v2')
    )

    parser.add_argument(
        '--secrets-path',
        '-sp',
        type=str,
        help='Secrets Path in KV backend to pull all the secrets from',
        required = is_required_arg('kv-v2')

    )

    parser.add_argument(
        '--export-format',
        '-ef',
        type=str,
        help='Set config with export followed by key=value',
        choices=export_format.CHOICES,
        default=export_format.DEFAULT_CHOICE,
    )

    parser.add_argument(
        'auth_type',
        metavar='auth-type',
        help='Auth method to use.',
        choices=auth.CHOICES,
        default=auth.DEFAULT_CHOICE
    )

    parser.add_argument(
        '--k8s-auth-role',
        action='store',
        help='Role to validate against vault k8s backend',
        required=is_required_arg(auth.K8S)
    )


    parser.add_argument(
        '--k8s-auth-mount-point',
        default='kubernetes',
        action='store',
        help='Mount point for k8s auth',
        required = is_required_arg(auth.K8S)
    )

    parser.add_argument(
        '--approle-role-id',
        action='store',
        help='role_id for AppRole auth method.',
        required=is_required_arg(auth.APPROLE)
    )

    parser.add_argument(
        '--approle-secret-id',
        action='store',
        help='secret_id for AppRole auth method.',
        required = is_required_arg(auth.APPROLE)
    )

    parser.add_argument(
        '--gcp-role',
        action='store',
        help='role for GCP auth method',
        required=is_required_arg(auth.GCP_GCE)
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action='count',
        default=0,
        help='Log verbosity')

    parser.add_argument(
        '--no-tls-verify',
        action='store_true',
        help='Disable tls verification')

    parser.add_argument(
        '--vault-address',
        action='store',
        default='http://127.0.0.1:8200',
        help='Vault address')

    parser.add_argument(
        '--generated-conf-dir',
        '-g',
        required=True,
        action=ReadableDir,
        help='Full path where the new generated secrets will be stored')

    parser.add_argument(
        '--generated-conf-filename',
        '-n',
        type=str,
        default='secrets.conf',
        help='Name of the secrets file to generate')

    arguments = parser.parse_args()

    # set log level
    log.setLevel(max(3 - arguments.verbose, 1) * 10)
    return arguments

def process(args):
    client = auth.get_client(args)

    if args.secrets_engine == kv_v2.KV2:
        kv_v2_obj = kv_v2.KVV2(
            client=client,
            secrets_path=args.secrets_path,
            mount_point=args.mount_point
        )

        results = kv_v2_obj.get_secrets(
            format=args.export_format
        )
    else:
        #TODO: Additional secret engines go here.
        pass

    helper.write_env_config(
        '{}/{}'.format(args.generated_conf_dir, args.generated_conf_filename),
        results,
        args.export_format
    )

def main():
    """ Entry point """
    # sets up debug logging and logger format
    logging.basicConfig(format='%(name)s (%(levelname)s): %(message)s')
    # parsing arguments
    try:
        process(_parse_argument())
    except Exception as e:
        log.error('Caught an unexpected exception: {}'.format(e))
    finally:
        logging.shutdown()

if __name__ == '__main__':
    sys.exit(main())