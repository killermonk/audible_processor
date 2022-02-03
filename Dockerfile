FROM ivanlee/ffmpeg-python

RUN mkdir /app
WORKDIR /app
COPY requirements.txt *.sh *.py ./
COPY src ./src/

RUN [ "chmod", "+x", "/app/*.sh" ]
RUN [ "pip", "install", "-r", "requirements.txt"]
RUN [ "ln", "-s", "/app/process.sh", "/usr/local/bin/process" ]
RUN [ "ln", "-s", "/app/watch.sh", "/usr/local/bin/watch" ]
