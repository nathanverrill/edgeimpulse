
FROM node

WORKDIR /ei

RUN apt-get update

RUN apt-get install -y curl
RUN apt install -y gcc g++ make build-essential nodejs sox gstreamer1.0-tools gstreamer1.0-plugins-good gstreamer1.0-plugins-base gstreamer1.0-plugins-base-apps

# required for pyaudio / edge impulse python
RUN apt install libasound2-dev -y
RUN apt install libportaudio2 -y
RUN apt install libportaudiocpp0 -y 
RUN apt install portaudio19-dev -y

# setup edge impulse for linux node
RUN npm config set user root 
RUN npm install edge-impulse-linux -g --unsafe-perm

# address opencv dependancy issue
RUN apt-get install libgl1 -y

# python environment and libraries; edge impulse python sdk
RUN apt-get install python3 -y
RUN apt-get install python3-pip -y

RUN python3 -m pip install --upgrade pip==20.3.4
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install six
RUN python3 -m pip install edge_impulse_linux

# for features, output, etc.
# map to local system, ie: -v data:/data
RUN mkdir data

# for scripts we can add dynamically
RUN mkdir scripts

# for the models in .eim format
RUN mkdir models

# copy in scripts, model, features etc
COPY . ./

# NOTE sudo chmod 777 ./models outside of Docker
ENTRYPOINT [ "python3", "-u", "/scripts/classify.py", "/models/modelfile.eim", "/input/features.txt" ]