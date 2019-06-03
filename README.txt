# django-api

Enviroments:
  Python >=3.5
  django 2.1
packages:
  django-rest-framework
  djangorestframework-jwt
  django-cors-headers
  PyPDF2
  reportlab

Testing: 
  pytest
  pytest-django
  pytest-cov
  mixer

Install packages:
  
  pip install -r requirements.txt

Migrations: 
  rm -f db.sqlite3
  rm -r applications/migrations
  python manage.py makemigrations applications
  python manage.py migrate
  python manage.py createsuperuser

