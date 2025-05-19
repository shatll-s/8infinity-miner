FROM nvidia/cuda:12.0.0-base-ubuntu22.04
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

RUN apt update \
    && apt install software-properties-common -y \
    && add-apt-repository ppa:deadsnakes/ppa

RUN apt install -y \
    python3.12 \
    ninja-build \
    ocl-icd-opencl-dev \
    opencl-headers

RUN python3.12 -c "import urllib.request; urllib.request.urlretrieve('https://bootstrap.pypa.io/get-pip.py', '/tmp/get-pip.py')" \
    && python3.12 /tmp/get-pip.py

COPY requirements.txt .
RUN python3.12 -m pip install -r requirements.txt

RUN mkdir -p /etc/OpenCL/vendors && \
    echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd

COPY src .

CMD ["python3.12", "/app/main.py"]