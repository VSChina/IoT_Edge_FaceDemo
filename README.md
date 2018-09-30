# IoT_Edge_FaceDemo
Face Recognition Demo base on IoT Edge

# Requirement
A PC with Linux OS(16.04)

An Azure account with subscription Id

Python
# Installation procedure

Download the codes. The root directory of the AI sample project is called AISampleSolution.

Download the recognition model(https://www.dropbox.com/s/yp7y6jic464l09z/model-r34-arcface-ms1m-refine-v1.zip?dl=0) and unzip it into the $AISampleSolution/models/

cd $AISampleSolution/models

chmod +x Download.sh

./Download.sh

cd $AISampleSolution/scripts

modify the subscriptionId in setup.sh

chmod +x setup.sh

./setup.sh

# Optional
## GPU-Enable
Nvidia-GPU

Install nvidia driver
https://www.nvidia.com/object/unix.html

Install nvidia-docker	
https://github.com/NVIDIA/nvidia-docker/wiki/Installation-(version-2.0)

rename the $ AISampleSolution/src/edge/config/deployment.json.gpu to deployment.json

## Leaf Device Isolation
Using Edge Devices as a gateway

Install the reqiurement on leaf device

# Known Issues
Docker network issue
https://stackoverflow.com/questions/24991136/docker-build-could-not-resolve-archive-ubuntu-com-apt-get-fails-to-install-a/40516974#40516974 

CA issue
https://github.com/MicrosoftDocs/azure-docs/issues/12826

Latency issue
https://github.com/Azure/iotedge/issues/44

Stable issue
https://github.com/Azure/iotedge/issues/19

