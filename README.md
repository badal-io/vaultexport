# Vault Export

Intention of **vaultexport** is to be used as an init container to authenticate and write secrets for apps to consume in kubernetes. This app generates secret config file that will be stored in a location of your choosing.


Currently supports following:
- Secrets backend:
    1. Supports KV v2 secrets backend
- Authentication:
    1. [Kubernetes](https://www.vaultproject.io/docs/auth/kubernetes.html)
    2. [AppRole](https://www.vaultproject.io/docs/auth/approle.html)
    3. [GCP GCE](https://www.vaultproject.io/docs/auth/gcp.html)
- Output:
  1. Toml: The path given in KV is traversed to generate a TOML formatted secrets file with 'section names' being the root of each of the paths
  2. env: 'key=value' file generated
  3. export: 'export key=value' file generated

Python Version Support : 3.7.2

## Usage

The help page provides information on proper parameters to pass
```sh
Generates secrets by pulling them from vault. Uses different Vault auth methods authenticate against backend.

positional arguments:
  secrets-engine        Pulls secrets from KV2 backend
  auth-type             Auth method to use.

optional arguments:
  -h, --help            show this help message and exit
  --mount-point MOUNT_POINT, -mp MOUNT_POINT
                        Backend KV mountpoint (default: kv)
  --secrets-path SECRETS_PATH, -sp SECRETS_PATH
                        Secrets Path in KV backend to pull all the secrets
                        from (default: None)
  --export-format {toml,env,export}, -ef {toml,env,export}
                        Set config with export followed by key=value (default:
                        env)
  --k8s-auth-role K8S_AUTH_ROLE
                        Role to validate against vault k8s backend (default:
                        None)
  --k8s-auth-mount-point K8S_AUTH_MOUNT_POINT
                        Mount point for k8s auth (default: kubernetes)
  --approle-role-id APPROLE_ROLE_ID
                        role_id for AppRole auth method. (default: None)
  --approle-secret-id APPROLE_SECRET_ID
                        secret_id for AppRole auth method. (default: None)
  --gcp-role GCP_ROLE   role for GCP auth method (default: None)
  --verbose, -v         Log verbosity (default: 0)
  --no-tls-verify       Disable tls verification (default: False)
  --vault-address VAULT_ADDRESS
                        Vault address (default: http://127.0.0.1:8200)
  --generated-conf-dir GENERATED_CONF_DIR, -g GENERATED_CONF_DIR
                        Full path where the new generated secrets will be
                        stored (default: None)
  --generated-conf-filename GENERATED_CONF_FILENAME, -n GENERATED_CONF_FILENAME
                        Name of the secrets file to generate (default:
                        secrets.conf)

This program should be used in init container specifically to source secrets before launching app. Steps for ideal scenario:
1. Create Kubernetes Service account as described in [vault kubernetes auth backend documentation](https://www.vaultproject.io/docs/auth/kubernetes.html)

```yaml
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: vault
---
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRoleBinding
metadata:
  name: role-tokenreview-binding
  namespace: default
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: system:auth-delegator
subjects:
- kind: ServiceAccount
  name: vault
  namespace: default
```

2. Create a kubernetes auth backend and attach roles with appropriate policies. For example, staging cluster should hit backend that only allow staging cluster with appropriate secret access.
3. generate secrets in init container once backend have been configured
```yaml
# sample init-container config for kubernetes
# note this is not the full deployment spec
...
spec:
  serviceAccountName: vault
  initContainers:
    - name: vaultexport
      image: muvaki/vaultexport
      args:
        - "--vault-address"
        - "https://vault.com"
        - "-g"
        - "/etc/vault"
        - "-ef"
        - "env"
        - "--k8-role"
        - "vault"
        - "--k8-auth-mount-point"
        - "kubernetes"
        - "kv-v2"
        - "-sp"
        - "staging/my_app"
...
```
4. save secrets to a shared volume mount so your apps can consume it. Make it memory to be volatile and not persistant
```yaml
# sample kubernetes deployment spec
volumes:
        - name: secrets-vol
          emptyDir:
            medium: "Memory"
```
5. App loads in normal lifecycle and sources secrets (environmnent variables)
```yaml
     containers:
      - name: muvaki
        image: muvaki-web
        command:
          - "bash"
          - "-c"
          - ". /etc/vault/env && node hello.js"
```
