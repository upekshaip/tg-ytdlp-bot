FROM python:3.10

ENV TZ=Asia/Kolkata

COPY magic.py .
COPY config.py .
COPY requirements.txt .

RUN apt-get update -y \
    && apt update -y \
    && apt-get install pip git -y

RUN apt-get install ffmpeg -y
RUN pip3 install -r requirements.txt

CMD python3 magic.py