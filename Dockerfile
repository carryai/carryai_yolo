ARG ARCH=l4t
FROM nvcr.io/nvidia/l4t-base:r35.2.1 AS base-l4t
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    python3-pip \
    libgstreamer1.0-0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-libav \
    libgstrtspserver-1.0-0 \
    libredis++-dev \
    && rm -rf /var/lib/apt/lists/*

FROM base-${ARCH} AS runtime
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python3", "-u", "app/main.py"]
