FROM resin/rpi-raspbian:jessie

RUN apt-get update \
  && apt-get install -y \
     make \
     gcc \
     libc6-dev \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN curl -o /tmp/pigpio.tar abyz.co.uk/rpi/pigpio/pigpio.tar \
  && tar -xf /tmp/pigpio.tar -C /tmp \
  && make -C /tmp/PIGPIO \
  && make -C /tmp/PIGPIO install \
  && rm -rf /tmp/pigpio.tar /tmp/PIGPIO

EXPOSE 8888

ENTRYPOINT ["/usr/local/bin/pigpiod", "-g"]
