# django-api

Enviroments:
  Python >=3.5
  django 2.1
packages:
  django-adminrestrict
  django-rest-framework
  djangorestframework-jwt
  jango-cors-headers
  PyPDF2
  reportlab

Testing: 
  pytest
  pytest-django
  pytest-cov
  mixer

Migrations: 
  rm -f db.sqlite3
  rm -r applications/migrations
  python manage.py makemigrations applications
  python manage.py migrate
  python manage.py createsuperuser

