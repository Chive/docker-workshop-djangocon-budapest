# What's all this fuzz about Docker?

> These are the notes or the Docker Workshop I have given at DjangoCon Budapest 2016. Please note that those are still a bit rough, but I'll try to polish them over the next few days.. Follow me at [@AskChive](https://twitter.com/AskChive) to be notified of updates :)


## Running commands
### one-off commands

```shell
$ docker run busybox ps aux
PID   USER     TIME   COMMAND
    1 root       0:00 sh
```

### Starting an interactive shell

```shell
$ docker run -it busybox
/ # ps aux
PID   USER     TIME   COMMAND
    1 root       0:00 sh
    5 root       0:00 ps aux
/ # touch itsalive
/ # ls   # file is here
/ # exit

$ docker run -it busybox
/ # ls   # file is gone! wat.

# what happened? there's 3 containers:
$ docker ps -a
```

**Explanation:** each "docker run" runs the specified command in a new container (isolated environment)

### Cleaning up:

```shell
$ docker rm <names/ids>
```

### The solution?

```shell
$ docker run --rm <image> <command>
```
 
## Dockerfile

create new project

```shell
$ docker run --rm --volume="$PWD":/app --workdir=/app django:1.9.4 django-admin.py startproject project .
```

start your project

```shell
$ docker run --rm -v "$PWD":/app -w /app -p 80:80 django:1.9.4 python manage.py runserver 0.0.0.0:80
```


## docker-compose.yml

docker command and arguments are hard to remember. docker-compose ftw

```
version: "2"
services:
  web:
    image: django:1.9.4
    command: python manage.py runserver 0.0.0.0:80
    working_dir: "/app"
    ports:
      - "80:80"
    volumes:
      - ".:/app"
```

## databases

migrate and create super user

```
$ docker-compose run --rm web python manage.py migrate
$ docker-compose run --rm web python manage.py createsuperuser
user root
pw rootrooot
```

## install an app

Now we're customizing the dockerfile (creating our own):

```
FROM django:1.9.4

WORKDIR /app

EXPOSE 80

COPY requirements.txt .
RUN pip install -r requirements.txt
    
CMD python manage.py runserver 0.0.0.0:80
```
Next we have to remove the ``working_dir``, ``image`` and ``command`` directives from the docker-compose.yml file since they're now defined in the Dockerfile.

Now create a new file ``requirements.txt`` and add the ``django-debug-toolbar`` to it.


per default, debug toolbar is only shown if server in in django.settings.INTERNAL_IPS, but the container ip is random (in a certain range), so we have to define an overwrite for debug-toolbar's checker function:

```python
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda x: DEBUG
}

```


## environment variables

add ``dj-database-url`` to ``requirements.txt`` and change in settings.py:

```
import dj_database_url
DATABASES = {
    'default': dj_database_url.config()
}
```

add to docker-compose.yml in the web service

```
    environment:
      DATABASE_URL: sqlite:///db.sqlite3
```

rebuild the image!

```
docker compose build web
```

Now, let's use a  proper database

add to ``docker-compose.yml``

```
volumes:
  db:
    driver: local

services:
  web:
    ...
    environment:
      DATABASE_URL: postgres://web:secretpassword@db:5432/web


  db:
    image: postgres:9.4
    volumes:
      - "db:/var/lib/postgres/data"
    environment:
      POSTGRES_USER: web
      POSTGRES_PASSWORD: secretpassword
```


migrate + createsuper again since we're using a new database :)


## envars: secret key!

add to docker-compose.yml
```
  web:
    environment:
      SECRET_KEY: notsosecret
```

change in settings.py:

```
SECRET_KEY = os.environ.get('SECRET_KEY')
```

run ``docker-compose down && docker-compose up -d`` to recreate containers since environment changed


# more services!

create ``views.py``

```python
import os

from django.core.cache import cache
from django.views.generic import TemplateView

CACHE_KEY = 'counter'


class IndexView(TemplateView):
    template_name = 'index.html'

    def get(self, request, *args, **kwargs):
        self.counter = cache.get(CACHE_KEY, 0) + 1
        cache.set(CACHE_KEY, self.counter)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'counter': self.counter,
            'hostname': os.environ.get('HOSTNAME'),
        })
        return context


index = IndexView.as_view()
```

append to ``urls.py``

```
    url('^$', views.index, name='index')
```

create the folder ``/templates``
create ``/templates/index.html``

```html
hello my friend. Your number is {{ counter }} and this request has been served by host <pre>{{ hostname }}</pre>.
```

change ``settings.py``

```
TEMPLATES[0]['DIRS'] = [os.path.join(BASE_DIR, 'templates')]

import django_cache_url
CACHES = {'default': django_cache_url.config()}

```

change ``docker-compose.yml``

```
  web:
    environment:
      CACHE_URL: redis://redis:6379

  redis:
    image: redis

```

change ``requirements.txt``

```
django-cache-url
django-redis
```


## even more services: add LB

### Linux (or Docker for Mac/Windows Beta)

add to ``docker-compose.yml``

```
  lb:
    image: dockercloud/haproxy
    links:
      - web
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    ports:
      - "80:80"
```

### Mac with Virtual Box

add to ``docker-compose.yml``

```
  lb:
    image: dockercloud/haproxy
    links:
      - web
    environment:
      - DOCKER_TLS_VERIFY
      - DOCKER_HOST
      - DOCKER_CERT_PATH
    volumes:
      - $DOCKER_CERT_PATH:$DOCKER_CERT_PATH
    ports:
      - 80:80
```

and remove the ``ports`` section from the ``web`` services in the same file, since haproxy is now handling and redirecting all requests.

Tear down everything again since we changed the config and then run it again. Afterwards, scale the web service to 3 so we can see the requests being routed to the different instances:

```
docker-compose down
docker-compose up -d
docker-compose scale web=3
```


# more stuff to talk about

* start interactive container again (``docker start -ai <id>``)
* pycharm: show how to use remote interpreter
* ``ipdb.set_trace`` (in library?)
* https://hub.docker.com/_/django/
* running docker commands
* what to keep in mind when inside a container
* mounting
* onbuild
