# Musicstats (Django)

Musicstats is an API for tracking song plays on radio stations. Information is pushed into this from the playout system and supplemented with Last.FM and Apple data.

## Launching the containers

For local development:

    docker-compose -p dev -f docker-compose.local.yml up -d --build

On dev/prod instances:

    COMPOSE_PROJECT_NAME=dev /usr/local/bin/docker-compose -p dev up -d
    COMPOSE_PROJECT_NAME=prod /usr/local/bin/docker-compose -p prod up -d

## Stopping the containers

For local development:

    docker-compose -p dev -f docker-compose.local.yml down

On dev/prod instances:

    COMPOSE_PROJECT_NAME=dev /usr/local/bin/docker-compose -p dev down
    COMPOSE_PROJECT_NAME=prod /usr/local/bin/docker-compose -p prod f docker-compose.yml -f docker-compose.prod.yml down