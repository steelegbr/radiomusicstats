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

import re
from datetime import datetime
import requests
import time
from bs4 import BeautifulSoup
from musicstats.models import OnAir2DataSource, EpgEntry


class OnAir2Parser:
    """
    Parses the EPG from an OnAir 2 web page.
    """

    def _tag_is_show_outer_div(self, tag):
        """
        Indicates if the tag is the outer div for a show
        """
        return (
            tag.has_attr("class") and "qt-part-show-schedule-day-item" in tag["class"]
        )

    def parse(self, content):
        """
        Parses the supplied EPG content.
        """

        # Setup our week

        week = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []}

        # Make some soup (parse the HTML)

        soup = BeautifulSoup(content, features="html.parser")
        show_wrappers = soup.find_all(self._tag_is_show_outer_div)

        # Cycle through the shows

        for show_wrapper in show_wrappers:

            # Pull out some basic details

            epg_entry = EpgEntry()
            epg_entry.image = show_wrapper.find("img")["src"]
            epg_entry.title = show_wrapper.find("a").text
            epg_entry.description = show_wrapper.find(
                "p", {"class": "qt-ellipsis-2"}
            ).text

            # Work out which day the entry is for

            day = show_wrapper.find("span", {"class": "qt-day"}).text
            epg_entry.day = time.strptime(day, "%A").tm_wday

            # Parse the start time from string

            start_time_text = show_wrapper.find("span", {"class": "qt-time"}).text
            epg_entry.start = datetime.strptime(start_time_text, "%H:%M").time()

            # Strip any forced resolution out of the image URL

            epg_entry.image = re.sub(r"-\d{3}x\d{3}", "", epg_entry.image)

            # Add the EPG entry to the list

            week[epg_entry.day].append(epg_entry)

        return week


class ProRadioParser:
    """
    Parses the EPG from a Pro Radio web page.
    """

    DAYS = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    def _article_to_epg_entry(self, article, day):
        """
        Converts an article in the HTML to an EPG entry
        """

        title_tag = article.find("h3", class_="proradio-post__title")
        description_tag = article.find("div", class_="proradio-paper").find("p")
        time_tag = article.find("p", class_="proradio-itemmetas")
        image_tag = article.find("img")

        time_text = time_tag.text
        start_time_text = time_text.split("-")[0].strip().upper()

        epg_entry = EpgEntry()
        epg_entry.title = title_tag.text
        epg_entry.description = description_tag.text
        epg_entry.start = datetime.strptime(start_time_text, "%I:%M %p").time()
        epg_entry.image = image_tag["src"]
        epg_entry.day = day

        return epg_entry

    def parse(self, content):
        """
        Parses the supplied EPG content.
        """

        # Setup our week

        week = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []}

        # Make some soup (parse the HTML)

        soup = BeautifulSoup(content, features="html.parser")
        day_tags = soup.find_all("a", {"data-proradio-target": "#proradio-tabslist"})

        # Build the day map

        day_map = {}

        for day_tag in day_tags:
            current_day = day_tag.text
            if current_day in self.DAYS:
                day_map[current_day] = day_tag["href"][1:]

        # Build up the schedule, day by day

        for index, day in enumerate(self.DAYS):
            day_wrapper = soup.find("div", {"id": day_map[day]})
            show_wrappers = day_wrapper.find_all("article")
            week[index] = [
                self._article_to_epg_entry(show_wrapper, index)
                for show_wrapper in show_wrappers
            ]

        return week


class EpgSynchroniser:
    """
    Synchronises an EPG into a database.
    """

    def synchronise(self, station, epg):
        """
        Synchronises the EPG.
        """

        # Cycles through each day

        for day in range(0, 7):

            # Find all the existing entries for this day

            existing_entries = list(EpgEntry.objects.filter(station=station, day=day))

            # Cycle through the new entries

            for entry in epg[day]:

                # Look for a match

                match_found = False

                for existing_entry in existing_entries:
                    if existing_entry.start == entry.start:

                        # Update the match

                        existing_entry.title = entry.title
                        existing_entry.image = entry.image
                        existing_entry.description = entry.description
                        existing_entry.save()

                        # Mark the existing entry as found

                        match_found = existing_entry

                # Remove any match we found from the list
                # No match, save the new EPG entry

                if match_found:
                    existing_entries.remove(match_found)
                else:
                    entry.station = station
                    entry.save()

            # Delete any unmatched entries

            for existing_entry in existing_entries:
                existing_entry.delete()

        # Clean up any old EPG entries

        old_epg_entries = EpgEntry.objects.filter(
            station=station, day__isnull=True
        ).delete()
