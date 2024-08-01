FROM python:3.12-bookworm
RUN apt-get update && apt-get install libgl1 -y
RUN groupadd -g 10001 app && \
   useradd -m -u 10000 -g app app
USER app:app
COPY . /home/app
WORKDIR /home/app
ENV PATH="$PATH:/home/app/.local/bin"
RUN pip install -r requirements.txt
ENTRYPOINT ["./entrypoint.sh"]
CMD ["false", "flask"]
