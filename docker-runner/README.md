# Edge Impulse classification

Prepared by Nathan Verrill

30 Jun 2022

## tl/dr

`sudo chmod 777 ./models/modelfile.eim`

`docker run -v $PWD/input:/input -v $PWD/scripts:/scripts -v $PWD/models:/models saicaifactory/ei-classifier`

### Docker 

Docker container with Edge Impulse SDK to run Edge Impulse `eim` model files. Only works on AMD64 (most computers, not Apple M1).

The container runs the Edge Impulse SDK, which runs the `classify.py` inside the container.

#### Mapped volumes

The `./scripts`, `./models` and `./input` folders are mapped to corresponding folders in Docker. This allows the files to be updated outside of Docker. So, for example, the Docker container can be pulled to your local, and then update the code in `classify.py` and you're all set. `Classify.py` is then managed in Gitlab.

#### Running container

Navigate to the root of the project (probably the directory where this README is located) 

On the command line, login to SAIC Innovation Factory Docker Hub (if you don't have an account, contact Tim Bassett/Matt Hammond/Nathan Verrill)

Then run the following docker command

`docker run -v $PWD/input:/input -v $PWD/scripts:/scripts -v $PWD/models:/models saicaifactory/ei-classifier`

You then should see inference results displayed in terminal

NOTES
- This has only been tested on Linux and not Windows.
- Does not work on ARM64/Apple M1

#### Updating docker image
Navigate to the directory where Dockerfile is located

On the command line, login to SAIC Innovation Factory Docker Hub (if you don't have an account, contact Tim Bassett/Matt Hammond/Nathan Verrill)

Run the following docker command

`docker buildx build --push --tag saicaifactory/ei-classifier --platform=linux/amd64 .`

NOTES
- The Docker `buildx` command is used because it allows us to build/deploy for ARM as well using the following command

`docker buildx build --push --tag saicaifactory/ei-classifier --platform=linux/amd64,linux/arm64.`

While Edge Impulse Linux SDK runs fine on ARM64/Apple M1 I haven't been able to get it to run successfully in Docker.

#### Updating models
- Navigate to the project in Edge Impulse Studio and collect new data
- Retrain model
- Create a model version
- In deployments, download the Linux build
- Unzip and rename to `modelfile.eim`, placing in the `./models` directory
- Update features.txt if the feature input changed, ie number of data samples for windowing
- Re-run classify container and should be all set
- This should only take 10-15 minutes, depending on how much new data is captured

#### Updating features
To update the input data for the classification, paste the features data in the `./input/features.txt` file. 

The python classification script can be updated to use live data instead of a features.txt file. The features.txt file is used to simplify integration, demo and testing.

#### Updating classify.py
The classification script can be updated at any time and the Docker container re-run. The updated script will be run automatically.

#### Running inference
Run inference with Docker run command:

`sudo chmod 777 ./models/modelfile.eim`

`docker run -v $PWD/input:/input -v $PWD/scripts:/scripts -v $PWD/models:/models saicaifactory/ei-classifier`

Results printed to the terminal or in stdout (if calling from inside python with import os cmd)








