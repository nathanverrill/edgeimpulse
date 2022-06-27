# First, install the dependencies via:
#    $ pip3 install requests
#    $ pip3 install kafka
#    $ pip3 install asyncio
#    $ pip3 install websockets

import time, hmac, hashlib, argparse, json, requests, copy

import ei
from kafka import KafkaConsumer

desc = '''
Edge Impulse + Tenjin Daemon

Service to steam data on user demand from Tenjin kafka sources, and extracts user defined sensor data and label entries into a edge impulse formatted sample.

usage (uploads to saic example project):

python3 ingest_daemon.py --project-id 114576 --kafka-topic geo-analytics-test --kafka-url localhost:9092 --api-key ei_1185b85996507965f24c77ad63225d0f4e9946ed913df02f35f866f2e588ba91 --data-keys latitude longitude
'''

parser = argparse.ArgumentParser(description=desc)
parser.add_argument('--project-id', type=str, required=True, help="ID of edge impulse project")
parser.add_argument('--kafka-topic', type=str, required=True, help="topic to consume")
parser.add_argument('--kafka-url', type=str, required=True, help="url to kafka")
parser.add_argument('--api-key', type=str, required=True, help="api key to edge impulse project")
parser.add_argument('--sample-rate-ms', type=float, default=1.0, help="approximate sample in milliseconds, does not need to be exact")
parser.add_argument('--data-prefix', nargs='*', default=['properties'], help="prefix key (or set of keys, evaluated in order) to reach the data entries in the kafka message")
parser.add_argument('--data-keys', nargs='+', required=True, help="keys (or set of keys, evaluated in order) used to access data from the kafka message. NOTE: currently all data keys must be grouped in the same prefix") 
parser.add_argument('--uuid', type=str, default='Ross Chair', help="Optional unique identifier or ID for device. This should be unique if multiple instances of this script are pointing to the same project")
args, unknown = parser.parse_known_args()

# empty signature (all zeros). HS256 gives 32 byte signature, and we encode in hex, so we need 64 characters here
emptySignature = ''.join(['0'] * 64)

# empty data structure for EI sample
data = {
    "protected": {
        "ver": "v1",
        "alg": "HS256",
        "iat": time.time() # epoch time, seconds since 1970
    },
    "signature": emptySignature,
    "payload": {
        "device_name": args.uuid,
        "device_type": "TENJIN",
        "interval_ms": args.sample_rate_ms,
        "sensors": [{'name' : axis, 'units' : '-'} for axis in args.data_keys],
        "values": []
    }
}

def sample_cb(request_data: dict) -> tuple: 
    '''Callback to be injected into the edge impulse socket to sample data from Tenjin
    '''
    sample_request = request_data['sample']

    # start parsing kafka input
    consumer = KafkaConsumer(args.kafka_topic, bootstrap_servers=args.kafka_url)

    current_data = copy.deepcopy(data)

    i = 0
    # TODO: make number of samples configurable
    SAMPLES = 100

    for msg in consumer:

        if i < SAMPLES:
            msg_json = json.loads(msg.value.decode('utf-8'))

            print('DEBUG: kafka recv=', msg_json)

            # drill down through prefixes
            for prefix in args.data_prefix:
                msg_json = msg_json[prefix]

            row = []
            for key in args.data_keys:
                row.append(msg_json[key])

            current_data['payload']['values'].append(row)

            i += 1
        
        else:
            return '', current_data

def upload_cb(request_data: dict, sample_data) -> str:
    '''Callback to be injected into the edge impulse socket to upload samples from Tenjin
    '''
    sample_request = request_data['sample']

    # ei supports multiple sample data types, but right now we only care about json
    if type(sample_data) is not dict:
        err = 'ERROR: ingest_daemon.py upload_cb not implemented for data type:{}'.format(type(sample_data))
        return err

    ei.upload_sample_json(sample_data, args.kafka_topic, sample_request['label'], sample_request['hmacKey'], args.api_key)


# Report as a device to the EI API and run until terminated
print("INFO: EI Ingestion Daemon starting...")
ei.device_socket_run(
    args.uuid,
    'TENJIN',
    args.api_key,
    args.sample_rate_ms,
    sample_cb,
    upload_cb)
