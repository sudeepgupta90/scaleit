FROM python:3.8

ENV APP_HOME=/home/scaleit
WORKDIR /home/scaleit

COPY . .
RUN chmod +x ${APP_HOME}/bin/*
RUN pip install --no-cache-dir -r requirements.txt

# ENTRYPOINT [ "/bin/bash", "-c"]
# CMD ["bin/scaleit-linux-amd64"]