FROM nvidia/cuda:12.0.0-base-ubuntu22.04
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

RUN apt update && apt install -y \
    ocl-icd-opencl-dev \
    opencl-headers \
    ninja-build \
    python3-pip

COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt

RUN mkdir -p /etc/OpenCL/vendors && \
    echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd

COPY src .

CMD ["python3", "/app/main.py"]