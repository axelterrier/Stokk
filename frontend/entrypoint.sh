#!/bin/sh
set -e

# Génère un certificat auto-signé au premier démarrage
if [ ! -f /etc/nginx/ssl/cert.pem ]; then
  mkdir -p /etc/nginx/ssl
  openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/key.pem \
    -out  /etc/nginx/ssl/cert.pem \
    -subj "/CN=stokk-nas/O=Stokk/C=FR" \
    -addext "subjectAltName=IP:127.0.0.1" \
    2>/dev/null
  echo "Certificat SSL généré."
fi

exec nginx -g "daemon off;"
