# get and save opensky api data once per minute and save to log file with current seconds as filename
import argparse
import requests
import os, time 

API = 'https://opensky-network.org/api/states/all?extended=true'

parser = argparse.ArgumentParser(
    description='Module to run a TF animal detection model on images')
parser.add_argument(
    '--in-directory',
    help='directory for input')
parser.add_argument(
    '--out-directory',
    help='Directory for input images (defaults to same as input)')
parser.add_argument(
    '--metadata',
    help='Directory for output images (defaults to same as input)')

args, unknown = parser.parse_known_args()

assert os.path.exists(args.in_directory), '--in-directory argument does not exist'

# get data
response = requests.get(API)

# filename using seconds epoch
filename = f'opensky_all_{str(int(time.time()))}.log'
print(f'saving to {filename}')

# write the data
# use response.content for the raw bytes of the data
f = open(os.path.join(args.out_directory, filename), "w+")
f.write(str(response.content))
f.close()
