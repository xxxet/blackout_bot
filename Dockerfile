FROM python:3.12-bookworm
ARG LITESTREAM="v0.3.13"
ARG ARCH="arm64"
RUN apt-get update && apt-get install libgl1 -y
ADD https://github.com/benbjohnson/litestream/releases/download/${LITESTREAM}/litestream-${LITESTREAM}-linux-${ARCH}.deb litestream.deb
RUN mkdir /home/app
COPY . /home/app
RUN groupadd -g 10001 app && \
   useradd -m -u 10000 -g app app && \
   chown -R app:app /home/app && \
   dpkg -i litestream.deb
COPY litestream.yml /etc/litestream.yml
USER app:app
WORKDIR /home/app
ENV PATH="$PATH:/home/app/.local/bin"
RUN pip install -r requirements.txt
ENTRYPOINT ["./entrypoint.sh"]
CMD ["no_venv", "flask", "replicate"]
