"""
Local (Dev) Settings
"""

DEBUG = False
ALLOWED_HOSTS = ["localhost", "some.example.org"]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "musicstats_api",
        "USER": "musicstats_api",
        "PASSWORD": "Pa55w0rd",
        "HOST": "localhost",
        "PORT": "",
    }
}

# Last.FM

LAST_FM = {
    "KEY": "KEY1",
    "SECRET": "SECRET1",
}

# Channels (for Websockets)

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("localhost", "6379")],
        },
    },
}

# Allow CORS from Solid Radio

CORS_ALLOWED_ORIGINS = ["https://some.example.org", "http://localhost:3000"]
