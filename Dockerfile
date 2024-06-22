FROM python:3.12-bookworm
RUN apt-get update
RUN apt-get install libgl1 -y
RUN mkdir -p /root/projects/blackout
WORKDIR /root/projects/blackout
