FROM metasploitframework/metasploit-framework

USER root

ENV PATH="/usr/src/metasploit-framework:${PATH}"

RUN if command -v apk >/dev/null 2>&1; then \
      apk add --no-cache curl; \
    elif command -v apt-get >/dev/null 2>&1; then \
      apt-get update \
      && apt-get install -y --no-install-recommends curl \
      && rm -rf /var/lib/apt/lists/*; \
    else \
      echo "No supported package manager found to install curl" >&2; \
      exit 1; \
    fi
