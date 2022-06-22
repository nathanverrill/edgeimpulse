# First, install the dependencies via:
#    $ pip3 install requests

import json
import time, hmac, hashlib, argparse, threading
import requests
import copy

from kafka import KafkaConsumer
import json

# and upload the file

def upload_sample(data, name, label):
    '''Uploads an edge impulse forwarded data sample.

    `data` arg must be a dict in valid edge impulse Data Acquisition format:
    https://docs.edgeimpulse.com/reference/data-ingestion/data-acquisition-format 

    `name` is the filename for a sample. Duplicates are allowed as the sample is hashed in EI
    `label` is the string label for the sample. Use 'unknown' if no label available

    '''

    # encode in JSON
    encoded = json.dumps(data)

    # sign message
    signature = hmac.new(bytes(args.hmac_key, 'utf-8'), msg = encoded.encode('utf-8'), digestmod = hashlib.sha256).hexdigest()

    # set the signature again in the message, and encode again
    data['signature'] = signature
    encoded = json.dumps(data)

    res = requests.post(url='https://ingestion.edgeimpulse.com/api/training/data',
                        data=encoded,
                        headers={
                            'Content-Type': 'application/json',
                            'x-label': label,
                            'x-file-name': name,
                            'x-api-key': API_KEY
                        })
    if (res.status_code == 200):
        print('INFO: Uploaded file to Edge Impulse', res.status_code, res.content)
    else:
        print('ERROR: Failed to upload file to Edge Impulse', res.status_code, res.content)

desc = '''
Edge Impulse + Tenjin Data forwarder

Captures streaming data from Tenjin kafka sources, and extracts user defined sensor data and label entries into a edge impulse formatted sample.

usage (uploads to saic example project):

python3 ingest.py --api-key ei_1185b85996507965f24c77ad63225d0f4e9946ed913df02f35f866f2e588ba91 --hmac-key d29e07904ac5edde24a5b4a6fb113acf --data-keys speed --max-len 100000 --label-key groundtruth

'''

parser = argparse.ArgumentParser(description=desc)
parser.add_argument('--kafka-topic', type=str, required=True, help="topic to consume")
parser.add_argument('--api-key', type=str, required=True, help="api key to edge impulse project")
parser.add_argument('--hmac-key', type=str, required=True, help="hmac key for project")
parser.add_argument('--sample-rate-ms', type=int, default=1, help="approximate sample in milliseconds, does not need to be exact")
parser.add_argument('--data-prefix', nargs='*', default=['properties'], help="prefix key (or set of keys, evaluated in order) to reach the data entries in the kafka message")
parser.add_argument('--data-keys', nargs='+', required=True, help="keys (or set of keys, evaluated in order) used to access data from the kafka message. NOTE: currently all data keys must be grouped in the same prefix") 
parser.add_argument('--max-len', type=int, required=True, help="maximum number of samples to aggregate before uploading") 
parser.add_argument('--label-key', type=str, help="Optional key to use as the label, if present. NOTE: currently all label keys must be grouped with the data prefix") 

args, unknown = parser.parse_known_args()

# empty signature (all zeros). HS256 gives 32 byte signature, and we encode in hex, so we need 64 characters here
emptySignature = ''.join(['0'] * 64)

data = {
    "protected": {
        "ver": "v1",
        "alg": "HS256",
        "iat": time.time() # epoch time, seconds since 1970
    },
    "signature": emptySignature,
    "payload": {
        "device_name": "tenjin data stream",
        "device_type": "TENJIN",
        "interval_ms": args.sample_rate_ms,
        "sensors": [{'name' : axis, 'units' : ''} for axis in args.data_keys],
        "values": []
    }
}

# start parsing kafka input
consumer = KafkaConsumer(args.kafka_topic, bootstrap_servers='localhost:9092')

i = 0
last_label = 'unknown'
current_data = copy.deepcopy(data)

timeout_duration = 10.0
is_timeout = True
# TODO(@dasch0) Since real data rate is ignored, this timeout implementation means samples may have lots of skew. Add sample interval calculation or estimation
def timeout():
    global current_data
    if (is_timeout):
        threading.Timer(timeout_duration, timeout).start()
        print(f"INFO: Timeout occured, no samples in {timeout_duration} seconds")
        if len(current_data['payload']['values']) > 1: #
            print(f"INFO: Uploading sample....")
            upload_sample(current_data, args.kafka_topic, last_label)
            i = 0
            current_data = copy.deepcopy(data)
timeout()

# Infinitely loop waiting for producer messages
for msg in consumer:
    # dict representation of json in kafka messagedata
    msg_json = json.loads(msg.value.decode('utf-8'))

    print(msg_json)

    # drill down through prefixes
    for prefix in args.data_prefix:
        msg_json = msg_json[prefix]

    # check if sample should be swapped to a new one
    if args.label_key:
        label = msg_json[args.label_key]
        if label is not last_label:
            last_label = label
            i = 0
            upload_sample(current_data, args.kafka_topic, last_label)
            current_data = copy.deepcopy(data)
            continue

    if i > args.max_len:
        i = 0
        upload_sample(current_data, args.kafka_topic, last_label)
        current_data = copy.deepcopy(data)
        continue

    row = []
    for key in args.data_keys:
        row.append(msg_json[key])

    current_data['payload']['values'].append(row)

    i += 1

