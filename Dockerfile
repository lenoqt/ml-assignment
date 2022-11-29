FROM nvidia/cuda:11.2.0-runtime-ubuntu20.04 AS build

RUN apt-get update && apt-get upgrade -y
RUN apt-get install software-properties-common curl -y
RUN add-apt-repository ppa:deadsnakes/ppa -y
RUN apt-get update
RUN apt-get install python3.10 -y
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1
RUN update-alternatives --config python

RUN pip install --no-cache-dir pipenv

WORKDIR /code
COPY requirements.txt /code/requirements.txt
RUN pipenv install -r /code/requirements.txt
COPY run.py .
COPY modules modules

CMD ["pipenv", "run", "python", "run.py"]
