FROM python:3.12-slim
RUN apt-get update && apt-get install libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 -y
RUN mkdir -p /root/projects/blackout
WORKDIR /root/projects/blackout
