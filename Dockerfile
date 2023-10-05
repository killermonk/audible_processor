FROM linuxserver/ffmpeg:latest AS deps

RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip install ffmpeg-python

FROM deps AS app

WORKDIR /app
COPY requirements.txt *.sh ./
COPY audible_processor ./audible_processor/

RUN pip install -r requirements.txt
RUN chmod +x *.sh
RUN ln -s /app/auth.sh /usr/local/bin/auth
RUN ln -s /app/process.sh /usr/local/bin/process
RUN ln -s /app/watch.sh /usr/local/bin/watch

# /aax - volume where we watch for AAX files
# /mp3 - volume where we output the processed mp3 files
VOLUME [ "/aax", "/mp3" ]

ENTRYPOINT [ "/app/run.sh" ]
CMD [ "/app/watch.sh", "-o", "/mp3", "/aax" ]