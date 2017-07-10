FROM resin/raspberry-pi-python:3.6

RUN apt-get update \
  && apt-get install -y \
     fonts-liberation \
     fonts-dejavu  \
     libjpeg-dev \
     libfreetype6-dev \
     libtiff5-dev \
     liblcms2-dev \
     libwebp-dev \
     zlib1g-dev \
     libyaml-0-2 \
  && apt-get autoremove \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN python -m venv /opt/legomac \
  && /opt/legomac/bin/pip install -r requirements.txt

COPY . /app

ENTRYPOINT ["/opt/legomac/bin/python"]
CMD ["run.py"]
