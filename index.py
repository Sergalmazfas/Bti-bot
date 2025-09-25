import os
import json
import logging
import urllib.request
import urllib.parse
import ssl
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_data = {}

try:
    import certifi
except Exception:
    certifi = None

def handler(event, context):
    secrets = {
        'BOT_TOKEN': bool(os.getenv('BOT_TOKEN')),
        'USER_ID': bool(os.getenv('USER_ID')),
        'REESTR_API_TOKEN': bool(os.getenv('REESTR_API_TOKEN')),
        'SERPRIVER_API_KEY': bool(os.getenv('SERPRIVER_API_KEY')),
    }
    return {'statusCode': 200, 'body': json.dumps({'secrets_present': secrets})}

def _ssl_context():
    """Build SSL context with the following priority:
    1) CA_BUNDLE_PEM env contains PEM content (use it)
    2) CA_BUNDLE_PATH env points to a PEM file (use it)
    3) certifi bundle if available
    4) system defaults
    """
    ca_pem = os.getenv('CA_BUNDLE_PEM')
    ca_path = os.getenv('CA_BUNDLE_PATH')

    if ca_pem:
        tmp_path = '/tmp/custom_ca_bundle.pem'
        try:
            with open(tmp_path, 'w') as f:
                f.write(ca_pem)
            return ssl.create_default_context(cafile=tmp_path)
        except Exception as e:
            logger.error(f"Failed to write CA_BUNDLE_PEM: {e}")

    if ca_path and os.path.exists(ca_path):
        try:
            return ssl.create_default_context(cafile=ca_path)
        except Exception as e:
            logger.error(f"Failed to load CA_BUNDLE_PATH: {e}")

    if certifi is not None:
        return ssl.create_default_context(cafile=certifi.where())
    return ssl.create_default_context()

if __name__ == '__main__':
    print(handler({}, None))
