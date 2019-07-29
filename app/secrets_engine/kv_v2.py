from constants import export_format
from utils import helper

KV2 = 'kv-v2'

class KVV2:

    def __init__(self, client, secrets_path, mount_point):
        self.client = client
        self.secrets_path = secrets_path
        self.mount_point = mount_point

    def get_secrets(self, format):

        if format == export_format.TOML:
            results = self.read_toml(self.secrets_path)
        else:
            results = self._read_secrets()

        return results

    def _read_secrets(self, value_type='secrets'):
        secret = {}
        try:
            if value_type == 'secrets':
                secret = self.client.secrets.kv.v2.read_secret_version(
                    path=self.secrets_path,
                    mount_point=self.mount_point)['data']['data']
            else:
                secret = self.client.secrets.kv.v2.list_secrets(
                    path=self.secrets_path,
                    mount_point=self.mount_point)['data']
        except None:
            pass
        finally:
            return secret

    def read_toml(self, path):
        tmp_toml = {}
        # Reads any keys stored in root of path and adds it to the toml dict
        toml = self._read_secrets()

        # recursively traverses the tree to generate keys and get secrets for kv backend
        # selection names are considered the root of the path in KV with key/value inside.
        # any key/value that fall under the path are added under the subsequent selection name.
        kv_keys = self._read_secrets('key')
        if 'keys' in kv_keys:
            for k in kv_keys['keys']:
                if k.endswith('/'):
                    # this is to prevent same keys being traversed twice
                    if k[:-1] in kv_keys['keys']:
                        continue
                    else:
                        tmp_toml[k[:-1]] = self.read_toml('{}/{}'.format(path, k[:-1]))
                else:
                    tmp_toml[k] =self.read_toml('{}/{}'.format(path, k))
            toml = helper.merge_dict(tmp_toml, toml)
        return toml











