'''
EI API calls and helpers
'''

import json
import requests
from threading import Timer
from time import sleep
import hmac
import hashlib

import ei_socket

def upload_sample_json(data: dict, name: str, label: str, hmac_key: str, api_key:str):
    '''Uploads an edge impulse forwarded data sample.

    `data` arg must be a dict in valid edge impulse Data Acquisition format:
    https://docs.edgeimpulse.com/reference/data-ingestion/data-acquisition-format 

    `name` is the filename for a sample. Duplicates are allowed as the sample is hashed in EI
    `label` is the string label for the sample. Use 'unknown' if no label available

    '''

    # encode in JSON
    encoded = json.dumps(data)

    # sign message
    signature = hmac.new(bytes(hmac_key, 'utf-8'), msg = encoded.encode('utf-8'), digestmod = hashlib.sha256).hexdigest()

    # set the signature again in the message, and encode again
    data['signature'] = signature
    encoded = json.dumps(data)

    print('TRACE: attempting to upload file...')
    print('DEBUG:', encoded) 

    res = requests.post(url='https://ingestion.edgeimpulse.com/api/training/data',
                        data=encoded,
                        headers={
                            'Content-Type': 'application/json',
                            'x-label': label,
                            'x-file-name': name,
                            'x-api-key': api_key 
                        })
    if (res.status_code == 200):
        print('INFO: Uploaded file to Edge Impulse', res.status_code, res.content)
    else:
        print('ERROR: Failed to upload file to Edge Impulse', res.status_code, res.content)

def device_socket_run(
        device_id: str,
        device_type: str,
        api_key: str,
        sample_rate_ms: float,
        sample_cb,
        upload_cb):
    '''Connect to the socket API as a device:
    https://docs.edgeimpulse.com/reference/edge-impulse-api/websocket-api

    NOTE: required function signatures for callbacks (error strings should be '' if no error):

    ```
    sample_cb(request_data: dict) -> error_string, sample_data
    upload_cb(request_data: dict, sample_data) -> error_string

    ```
    '''

    ws_url = f"wss://remote-mgmt.edgeimpulse.com/socket.io/"

    # initial hello response to announce to the remote management protocol
    hello_data = {
        'hello': {
            'version': 3,
            'apiKey': api_key,
            'deviceId': device_id,
            'deviceType': device_type,
            'connection': 'ip',
            'sensors': [{
                'name': device_type,
                'maxSampleLengthS': 10000000,
                'frequencies': [sample_rate_ms * 1000.0]
                }],
            'supportsSnapshotStreaming': False
        }
    }
    ei_socket.run(ws_url, hello_data, sample_cb, upload_cb)
