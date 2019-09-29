# Musicstats (Django)

Musicstats is an API for tracking song plays on radio stations. Information is pushed into this from the playout system and supplemented with Last.FM and Apple data.

## Launching the containers

For local development:

    docker-compose -p dev -f docker-compose.local.yml up -d --build

On dev/prod instances:

    COMPOSE_PROJECT_NAME=dev /usr/local/bin/docker-compose -p dev pull
    COMPOSE_PROJECT_NAME=dev /usr/local/bin/docker-compose -p dev up -d
    COMPOSE_PROJECT_NAME=prod /usr/local/bin/docker-compose -p prod -f docker-compose.prod.yml pull
    COMPOSE_PROJECT_NAME=prod /usr/local/bin/docker-compose -p prod -f docker-compose.prod.yml up -d

## Stopping the containers

For local development:

    docker-compose -p dev -f docker-compose.local.yml down

On dev/prod instances:

    COMPOSE_PROJECT_NAME=dev /usr/local/bin/docker-compose -p dev down
    COMPOSE_PROJECT_NAME=prod /usr/local/bin/docker-compose -p prod -f docker-compose.prod.yml down

## Tests and Coverage

To run the test and get a coverage report:

    coverage run manage.py test
    coverage html

You can now copy the htmlcov folder to a local host to see the pretty report.