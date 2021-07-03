"""
    Radio Music Stats - Radio Music Statistics and Now Playing
    Copyright (C) 2017-2021 Marc Steele

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""

from bs4 import BeautifulSoup
import requests
from typing import List
import xml.etree.ElementTree as ET
from musicstats.models import Presenter, Station


class WordpressPresenterImage:
    """Parses an image URL from a presenter page."""

    def parse(self, html: str) -> str:
        """Parses a presener graphic from their biography pag.

        Args:
            html (str): The HTML from the biography page.

        Returns:
            str: The URL for the presenter image.
        """

        # Sanity check

        if not html:
            return None

        # Parse

        soup = BeautifulSoup(html, features="html.parser")
        image_tags = soup.find_all("div", {"class": "qt-header-bg"})

        # Check and return the first on we find

        if image_tags:
            return image_tags[0]["data-bgimage"]
        else:
            return None


class WordpressPresenterParser:
    """Parses a list of presenters from an XML file."""

    def parse(self, xml: str, station: Station) -> List[Presenter]:
        """Parses a list of presenters from XML.

        Args:
            xml (str): The XML to parse.

        Returns:
            List[Presenter]: The list of presenters.
        """

        presenters: List[Presenter] = []
        root = ET.fromstring(xml)

        for item in root.findall("channel/item"):

            # Find the interesting tags

            name_tag = item.find("title")
            bio_tag = item.find("{http://purl.org/rss/1.0/modules/content/}encoded")
            url_tag = item.find("link")

            # Pull out the name and biography

            presenter = Presenter()
            presenter.name = name_tag.text
            presenter.biography = bio_tag.text
            presenter.url = url_tag.text
            presenter.station = station

            presenters.append(presenter)

        return presenters


class PresenterSynchroniser:
    """Synchronises the presenters into the database."""

    def synchronise(self, station: Station, presenters: List[Presenter]):
        """Performs the sync.

        Args:
            station (Station): The station to sync for.
            presenters (List[Presenter]): The presenters to sync in.
        """

        # Sanity check

        if not presenters or not station:
            return

        # Build a map of new presenters

        presenter_map = {}

        for presenter in presenters:
            presenter_map[presenter.name] = presenter

        # Get our list of existing presenters

        existing_presenters = list(Presenter.objects.filter(station=station))

        # Strip out any presenters no longer on the roster

        remaining_presenters: List[Presenter] = []

        for existing_presenter in existing_presenters:
            if existing_presenter.name in presenter_map:
                remaining_presenters.append(existing_presenter)
            else:
                existing_presenter.delete()

        # Build a map for quick lookups

        existing_map = {}

        for existing_presenter in remaining_presenters:
            existing_map[existing_presenter.name] = existing_presenter

        # Update or create presenters

        for presenter in presenters:
            if presenter.name in existing_map:
                existing_presenter = existing_map[presenter.name]
                existing_presenter.biography = presenter.biography
                existing_presenter.image = presenter.image
                existing_presenter.save()
            else:
                presenter.save()
