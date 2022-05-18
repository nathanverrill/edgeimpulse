
import datetime
import json
import time
import sys

from azure.iot.device import IoTHubModuleClient, Message
from azure.iot.device.exceptions import ConnectionFailedError
from azure.iot.device.constant import VERSION


class EdgeMessage(Message):
    # Shape the data as expected by the Optra portal.
    def __init__(self, msg_data):
        msec = int(datetime.datetime.now().timestamp()*1000)
        msg_fields = {}
        msg_fields["createdAt"] = msec
        msg_fields["data"] = msg_data
        # create a message object from the contents
        Message.__init__(self, json.dumps(msg_fields, indent=2))



def setup_iot_module_client():

    print(f"Python Version: - {sys.version}")
    print(f"Azure Device SDK Version: - {VERSION}")

    module_client = IoTHubModuleClient.create_from_edge_environment(websockets=True)
    # After a cold boot of the device, edgeHub may not be fully initialized
    # before skills start running.  edgeHub must be up and running in order
    # for skills to retrieve their module twin and send IoT messages.
    while True:
        try:
            module_client.connect()
            break
        except ConnectionFailedError as e:
            pass
        print(f'Waiting to connect to IoT Hub')
        time.sleep(10)
    print(f'Module client connected')
    
    return module_client

def get_iot_twin_parameters(module_client):    
    twin_data = module_client.get_twin()
    init_data = twin_data.get("desired", None)
    return init_data

#
# find_camera_url_in_twin_data()
#
# returns string on success
# returns None on failure.
# 
# Example Data
# {
#    "device":{
#       "sensors":{
#          "327035674575241809":{
#             "name":"MyCamera",
#             "ip":"rtsp://192.168.1.20:8554/cam"
#          }
#       }         
#    }
# }
def find_camera_url_in_twin_data(twin_data):    
    if 'device' in twin_data:
        device = twin_data["device"]        
        if "sensors" in device: 
            sensors = device["sensors"]                    
            for key in sensors:                
                sensor = sensors[key] 
                if "ip" in sensor:
                    ip = sensor["ip"]                    
                    return ip
                
    return None



