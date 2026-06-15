#!/usr/local/vuln-bash/bin/bash

echo "Content-Type: text/plain"
echo
echo "Shellshock lab victim"
echo "CGI script executed as: $(id)"
echo "Server time: $(date -u)"
