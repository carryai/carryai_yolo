#ARG ARCH=l4t
#FROM nvcr.io/nvidia/l4t-base:r35.2.1 AS base-l4t
FROM nvcr.io/nvidia/pytorch:24.12-py3 AS pytorch
# Set environment variables
ENV NVIDIA_VISIBLE_DEVICES=all
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=$PATH:$CUDA_HOME/bin
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CUDA_HOME/lib64
# Install dependencies
# RUN apt-get update && apt-get install -y \
# ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    python3-pip \
    libgstreamer1.0-0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-libav \
    libgstrtspserver-1.0-0 \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

FROM pytorch AS runtime
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python3", "-u", "app/main.py"]
