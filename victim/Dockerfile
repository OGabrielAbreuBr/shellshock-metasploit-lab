FROM debian:bookworm

ARG BASH_VERSION=4.3

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      apache2 \
      ca-certificates \
      curl \
      gcc \
      libc6-dev \
      make \
      texinfo \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL "https://ftp.gnu.org/gnu/bash/bash-${BASH_VERSION}.tar.gz" -o /tmp/bash.tar.gz \
    && mkdir -p /tmp/bash-src \
    && tar -xzf /tmp/bash.tar.gz -C /tmp/bash-src --strip-components=1 \
    && cd /tmp/bash-src \
    && ./configure --prefix=/usr/local/vuln-bash \
    && make -j"$(nproc)" \
    && make install \
    && rm -rf /tmp/bash.tar.gz /tmp/bash-src

RUN a2enmod cgi \
    && mkdir -p /usr/lib/cgi-bin \
    && sed -i 's/^Listen 80$/Listen 80/' /etc/apache2/ports.conf

COPY cgi/status.cgi /usr/lib/cgi-bin/status.cgi

RUN chmod 755 /usr/lib/cgi-bin/status.cgi \
    && chown root:root /usr/lib/cgi-bin/status.cgi

EXPOSE 80

CMD ["apachectl", "-D", "FOREGROUND"]
