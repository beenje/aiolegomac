FROM arm32v6/alpine:3.6

RUN apk --update upgrade \
  && apk --no-cache --no-progress add ca-certificates \
  && apk add openssl \
  && rm -rf /var/cache/apk/*

RUN wget -O /usr/local/bin/traefik https://github.com/containous/traefik/releases/download/v1.3.3/traefik_linux-arm \
  && chmod a+x /usr/local/bin/traefik

ENTRYPOINT ["/usr/local/bin/traefik"]
