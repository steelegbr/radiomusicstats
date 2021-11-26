FROM python:3.9

WORKDIR /opt/musicstats

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY  . .

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "musicstats.asgi:application"]