import hvac
import logging

K8S = 'k8s'
APPROLE = 'approle'
DEFAULT_CHOICE = K8S
CHOICES = [K8S, APPROLE]

log = logging.getLogger('auth')

def get_client(args):

    client = hvac.Client(url=args.vault_address, verify=False if args.no_tls_verify else True)

    if (args.auth_type == K8S):
        return _auth_k8s(client, args.k8_auth_mount_point, role=args.k8_role)
    elif (args.auth_type == APPROLE):
        return _auth_approle(client, args.approle_role_id, args.approle_secret_id)
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
