FROM python:3.9-slim
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential libopencv-dev python3-opencv libatlas-base-dev libportaudio2 libportaudiocpp0 portaudio19-dev ffmpeg libsm6

COPY requirements.txt ./
RUN pip3 install --upgrade pip
RUN pip3 install six
RUN pip3 install -r requirements.txt

# This deployment is capable of displaying video with detections. To enable
# setup the DISPLAY variable and enable access to the display when running the container
ENV DISPLAY=:0

COPY . ./

EXPOSE 5000

ENV NGROK_AUTH_TOKEN 1zPFFOAwgV30ZHtaWn6dnbj3zpw_2GGf1SQWhdRkuCwwp3Trr

CMD [ "python3", "-u",  "detect.py", "--backup-source", "http://ei-webcam.ngrok.io/stream"] 
