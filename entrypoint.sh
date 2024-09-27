#!/bin/sh
python manage.py migrate  --noinput
echo "database migrated"
gunicorn Ecommerce_API.wsgi -b 0.0.0.0:8001 --disable-redirect-access-to-syslog --timeout 200 --reload