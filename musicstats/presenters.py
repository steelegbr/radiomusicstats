"""Presenter List Helper Classes
"""

from typing import List
import xml.etree.ElementTree as ET
from musicstats.models import Presenter

class WordpressPresenterParser:
    """Parses a list of presenters from an XML file.
    """

    def parse(self, xml: str) -> List[Presenter]:
        """Parses a list of presenters from XML.

        Args:
            xml (str): The XML to parse.

        Returns:
            List[Presenter]: The list of presenters.
        """

        presenters: List[Presenter] = []
        root = ET.fromstring(xml)

        for item in root.findall('channel/item'):

            # Find the interesting tags

            name_tag = item.find('title')
            bio_tag = item.find('{http://purl.org/rss/1.0/modules/content/}encoded')

            # Pull out the name and biography

            presenter = Presenter()
            presenter.name = name_tag.text
            presenter.biography = bio_tag.text

            presenters.append(presenter)

        return presenters

