FROM linuxserver/ffmpeg:latest AS deps

# Git is required while the requirements.txt for Audible is pinned to a github commit
RUN apt-get update && apt-get install -y python3 python3-pip git
RUN pip3 install --break-system-packages ffmpeg-python

# Clean up apt files
RUN apt-get clean && apt-get autoclean
RUN apt-get autoremove -y
RUN rm -rf /var/lib/{apt,dpkg,cache,log}/

FROM deps AS app-deps

WORKDIR /app
COPY requirements.txt *.sh ./
RUN pip3 install --break-system-packages -r requirements.txt

# Clean up pip cache
RUN pip3 cache purge
RUN apt-get remove -y python3-pip git
RUN apt-get clean && apt-get autoclean
RUN apt-get autoremove -y

FROM app-deps AS app

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