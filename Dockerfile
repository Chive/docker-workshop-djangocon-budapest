FROM django:1.9.4

WORKDIR /app

EXPOSE 80

COPY requirements.txt .
RUN pip install -r requirements.txt

CMD python manage.py runserver 0.0.0.0:80
