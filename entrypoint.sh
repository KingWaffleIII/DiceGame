#!/bin/bash
# apt install python-dev libpq-dev -y &> /dev/null
python -m pip install -r requirements.txt &> /dev/null
python manage.py collectstatic --noinput
python manage.py makemigrations 
python manage.py migrate

mkdir -p /app/backups
cp /app/db.sqlite3 /app/backups/db-$(date +%F-%H-%M).sqlite3 
find /app/backups/ -type f -mtime +7 -name '*.sqlite3' -delete

python manage.py test --keepdb
if [ $? -eq 0 ]; then
    python manage.py runserver 0.0.0.0:80
    # gunicorn --bind=0.0.0.0:80 --workers=2 cashmoney.wsgi
else
    echo "Unit tests failed, aborting... If you have not edited the code, create an issue on GitHub."
    exit 1
fi
