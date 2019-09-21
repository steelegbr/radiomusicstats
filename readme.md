# Musicstats (Django)

Musicstats is an API for tracking song plays on radio stations. Information is pushed into this from the playout system and supplemented with Last.FM and Apple data.

## Building the container

    docker build -t musicstats .
    docker run --detach --name dev-musicstats --link dev-musicstats-postgres:postgres --link dev-musicstats-redis:redis --mount source=dev-musicstats-media,target=/opt/musicstats/media --mount source=dev-musicstats-static,target=/opt/musicstats/static -p 9500:8000 musicstats

## Dev containers (Postgres and redis)

     docker run --name musicstats-postgres -e POSTGRES_PASSWORD=Password1 -d postgres
     docker run --name musicstats-redis -d redis

## Container cleanup

    docker stop dev-musicstats
    docker rm dev-musicstats
    docker stop dev-musicstats-postgres
    docker rm dev-musicstats-postgres
    docker stop dev-musicstats-redis
    docker rm dev-musicstats-redis

## Volumes

    docker volume create dev-musicstats-media
    docker volume create dev-musicstats-static