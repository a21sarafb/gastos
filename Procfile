web: bash -c "python manage.py migrate --noinput && python manage.py createsuperuser --noinput || true && gunicorn gastos_project.wsgi:application --log-file -"
