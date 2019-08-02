import hvac
import logging
import requests

K8S = 'k8s'
APPROLE = 'approle'
GCP_GCE = 'gcp-gce'
DEFAULT_CHOICE = K8S
CHOICES = [K8S, APPROLE, GCP_GCE]

log = logging.getLogger('auth')

def get_client(args):

    client = hvac.Client(url=args.vault_address, verify=False if args.no_tls_verify else True)

    if (args.auth_type == K8S):
        return _auth_k8s(client, args.k8_auth_mount_point, role=args.k8_role)
    elif (args.auth_type == APPROLE):
        return _auth_approle(client, args.approle_role_id, args.approle_secret_id)
    elif (args.auth_type == GCP_GCE):
        return _auth_gcp_gce(client, args.gcp_role, args.vault_address)
    else:
        raise Exception("{} is not a supported auth type.", args.auth_type)

def _auth_k8s(client, mount_point, role):
    log.info("Authenticating via K8s method.")

    f = open('/var/run/secrets/kubernetes.io/serviceaccount/token')
    jwt = f.read()
    result = client.auth_kubernetes(role, jwt.strip(), mount_point=mount_point)
    client.token = result['auth']['client_token']

    assert client.is_authenticated()

    return client

def _auth_approle(client, role_id, secret_id):
    log.info("Authenticating via AppRole method.")

    client.auth_approle(role_id=role_id, secret_id=secret_id)

    assert client.is_authenticated()
    return client

def _auth_gcp_gce(client, role, vault_address):
    log.info("Authenticating via GCP-GCE method.")

    audience = '{}/vault/{}'.format(vault_address, role)
    headers = {'Metadata-Flavor': 'Google'}
    format = 'full'
    licenses = 'TRUE'

    client.auth_gcp(role=role, jwt=jwt)

    # Construct a URL with the audience and format.
    url = 'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity?audience={}&format={}&licenses={}'
    url = url.format(audience, format, licenses)

    # Request a token from the metadata server.
    r = requests.get(url, headers=headers)

    # Extract the token from the response.
    jwt = r.text

    client.auth_gcp(role=role, jwt=jwt)

    assert client.is_authenticated()
    return client