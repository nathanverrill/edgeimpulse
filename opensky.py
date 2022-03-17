# get and save opensky api data once per minute and save to log file with current seconds as filename
import requests
import time 

API = 'https://opensky-network.org/api/states/all?extended=true'

while True:
    # get data

    response = requests.get(API)

    # filename using seconds epoch
    file_and_path = f'data/opensky/{str(int(time.time()))}.log'
    file_and_path

    print(f'saving to {file_and_path}')

    # write the data
    # use response.content, for the raw bytes of the data
    f = open(file_and_path, "w")
    f.write(str(response.content))
    f.close()

    time.sleep(60)