FROM python:3.12-bookworm
RUN apt-get update && apt-get install libgl1 -y
RUN mkdir /blackout
COPY . /blackout
RUN groupadd -g 10001 blackout && \
   useradd -u 10000 -g blackout blackout \
   && chown -R blackout:blackout /blackout
USER blackout:blackout
WORKDIR /blackout
ENTRYPOINT ["./entrypoint.sh"]
