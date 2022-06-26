import asyncio
from websockets import connect
import json
import signal

def _ei_parse_cbor(s: str) -> dict:
    '''Private helper, converts cbor formatted string to python dict)
    '''
    split = s.split('{', 1) # remove non json compatible prefix
    #print("DEBUG: split=", split)
    if len(split) != 2:
        return {}

    s = split[1]
    rsplit = s.rsplit('}', 1) # remove non json compatible postfix
    #print("DEBUG: rsplit=", rsplit)
    message = f"{{ {rsplit[0]} }}"
    return json.loads(message)

async def heartbeat(websocket):
    while True:
        await asyncio.sleep(3)
        await websocket.send('ping')

async def handler(websocket, sample_cb, upload_cb):
    while True:
        message = await websocket.recv()
        print('TRACE: ei_socket raw recv=', message)

        try: 
            message_data = _ei_parse_cbor(message)
        except Exception as e:
            print('ERROR: ei_socket failed to decode:', message)
            print(e)

        try:
            if 'sample' in message_data:
                print('INFO: ei_socket sample request received')

                await websocket.send(json.dumps({'sample': True}))
                print('TRACE: ei_socket sampling started')

                err, sample = sample_cb(message_data)

                if err:
                    await websocket.send(json.dumps({'sample': False, 'error': err }))
                    print('TRACE: ei_socket sampling failed', err)
                    continue
                else:
                    await websocket.send(json.dumps({'sampleUploading': True}))

                err = upload_cb(message_data, sample)

                if err:
                    await websocket.send(json.dumps({'sample': False, 'error': err }))
                    print('TRACE: ei_socket sampling upload failed', err)
                    continue
                else:
                    await websocket.send(json.dumps({'sampleFinished': True}))
                    print('TRACE: ei_socket sampling finished')

        except Exception as e:
            print('ERROR: ei_socket exception occurred during sampling')
            print('EXCEPTION:', e)
            await websocket.send(json.dumps({'sample': False, 'error' : str(e)}))


async def hello(websocket, data):
    await websocket.send(json.dumps(data))

async def ei_socket(uri: str, hello_data: dict, sample_cb, upload_cb):
    async with connect(uri) as websocket:
        await hello(websocket, hello_data)
        await asyncio.gather(heartbeat(websocket), handler(websocket, sample_cb, upload_cb))

def run(uri: str, hello_data: dict, sample_cb, upload_cb):
    '''Run an ei device that persists until program is terminated. Able to live sample data via the provided *_cb functions.
    Note: The callback functions must accept a single dict parameter which will pass in the sample request
    '''
    asyncio.run(ei_socket(uri, hello_data, sample_cb, upload_cb))
