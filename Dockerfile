FROM linuxserver/ffmpeg:latest AS deps

RUN apt-get update && apt-get install -y software-properties-common
# Package python3 gives us python 3.12, but the audible package requires python <3.12
# So we need to manually install 3.11 from deadsnakes, then bootstrap pip for it
RUN add-apt-repository ppa:deadsnakes/ppa -y
RUN apt-get update && apt-get install -y python3.11
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11
RUN pip3.11 install --break-system-packages ffmpeg-python


FROM deps AS app

WORKDIR /app
COPY requirements.txt *.sh ./
RUN pip3.11 install -r requirements.txt

COPY audible_processor ./audible_processor/

RUN chmod +x *.sh
RUN ln -s /app/auth.sh /usr/local/bin/auth
RUN ln -s /app/process.sh /usr/local/bin/process
RUN ln -s /app/watch.sh /usr/local/bin/watch

# /aax - volume where we watch for AAX files
# /mp3 - volume where we output the processed mp3 files
VOLUME [ "/aax", "/mp3" ]

ENTRYPOINT [ "/app/run.sh" ]
CMD [ "/app/watch.sh", "-o", "/mp3", "/aax" ]