# django-api

Enviroments:
  Python >=3.5
  django 2.1

packages:
  django-rest-framework
  django-rest-framework-jwt
  PyPDF2
  reportlab
  
  
Migrations:
  rm -f db.sqlite3
  rm -r applications/migrations
  python manage.py makemigrations applications
  python manage.py migrate
  python manage.py createsuperuser

