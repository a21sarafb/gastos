web: bash -c "python manage.py showmigrations core && python manage.py migrate --noinput && gunicorn gastos_project.wsgi:application --log-file -"
