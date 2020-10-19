"""
MusicStats unit tests
"""

import json
from datetime import datetime, time
from parameterized import parameterized
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.urls import reverse


class TestIndex(APITestCase):
    """
    Tests we can access the index.
    """

    def test_index(self):
        """
        Checks the index returns the static content
        """

        url = reverse("index")
        response = self.client.get(url)
        self.assertEqual(response.content.decode(), "Hello from the musicstats index.")

