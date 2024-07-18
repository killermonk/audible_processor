FROM ivanlee/ffmpeg-python

RUN mkdir /app
WORKDIR /app
COPY requirements.txt *.sh ./
RUN pip install -r requirements.txt

COPY audible_processor ./audible_processor/

RUN chmod +x *.sh
RUN ln -s /app/auth.sh /usr/local/bin/auth
RUN ln -s /app/process.sh /usr/local/bin/process
RUN ln -s /app/watch.sh /usr/local/bin/watch

# /aax - volume where we watch for AAX files
# /mp3 - volume where we output the processed mp3 files
VOLUME [ "/aax", "/mp3" ]

CMD [ "/app/watch.sh", "-o", "/mp3", "/aax" ]