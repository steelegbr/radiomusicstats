# Musicstats (Django)

Musicstats is an API for tracking song plays on radio stations. Information is pushed into this from the playout system and supplemented with Last.FM and Apple data.

## Building the container

    docker build -t musicstats .
    docker run --detach --name musicstats --link musicstats-mysql:mysql --link musicstats-redis:redis -p 8000:8000 musicstats

## Dev containers (MySQL and redis)

     docker run --name musicstats-mysql -e MYSQL_ROOT_PASSWORD=Password1 -d mysql
     docker run --name musicstats-redis -d redis

## Container cleanup

    docker stop musicstats
    docker rm musicstats
    docker stop musicstats-mysql
    docker rm musicstats-mysql
    docker stop musicstats-redis
    docker rm musicstats-redis