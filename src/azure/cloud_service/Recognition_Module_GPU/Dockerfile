FROM mxnet/python:gpu

RUN apt-get update \
    && apt-get install -y python-dev \
    && apt-get install -y build-essential \
    && apt-get install -y cmake \
    && apt-get install -y libglib2.0-0

RUN pip install opencv-python==3.2.0.8 \
    && pip install scipy \
    && pip install sklearn \
    && pip install easydict \
    && pip install --ignore-installed numpy scikit-image \
    && pip install flask \
    && pip install flask-cors \
    && pip install pydocumentdb

RUN apt-get update \
    && apt-get install -y libffi-dev libssl-dev \
    && pip install pyopenssl ndg-httpsclient pyasn1

COPY . .

ENTRYPOINT [ "python", "-u", "./main.py" ]
