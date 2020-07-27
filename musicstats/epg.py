'''
EPG Helper Classes
'''

import re
from datetime import datetime
import requests
import time
from bs4 import BeautifulSoup
from musicstats.models import OnAir2DataSource, EpgEntry

class OnAir2Parser:
    '''
        Parses the EPG from an OnAir 2 web page.
    '''

    def _tag_is_show_outer_div(self, tag):
        '''
        Indicates if the tag is the outer div for a show
        '''
        return tag.has_attr('class') and 'qt-part-show-schedule-day-item' in tag['class']

    def parse(self, content):
        '''
            Parses the supplied EPG content.
        '''

        # Setup our week

        week = {
            0: [],
            1: [],
            2: [],
            3: [],
            4: [],
            5: [],
            6: []
        }

        # Make some soup (parse the HTML)

        soup = BeautifulSoup(content, features="html.parser")
        show_wrappers = soup.find_all(self._tag_is_show_outer_div)

        # Cycle through the shows

        for show_wrapper in show_wrappers:

            # Pull out some basic details

            epg_entry = EpgEntry()
            epg_entry.image = show_wrapper.find("img")["src"]
            epg_entry.title = show_wrapper.find("a").text
            epg_entry.description = show_wrapper.find("p", {"class": "qt-ellipsis-2"}).text

            # Work out which day the entry is for

            day = show_wrapper.find("span", {"class": "qt-day"}).text
            epg_entry.day = time.strptime(day, "%A").tm_wday

            # Parse the start time from string

            start_time_text = show_wrapper.find("span", {"class": "qt-time"}).text
            epg_entry.start = datetime.strptime(start_time_text, "%H:%M").time()

            # Strip any forced resolution out of the image URL

            epg_entry.image = re.sub(r'-\d{3}x\d{3}', '', epg_entry.image)
            
            # Add the EPG entry to the list

            week[epg_entry.day].append(epg_entry)

        return week

class EpgSynchroniser:
    '''
        Synchronises an EPG into a database.
    '''

    def synchronise(self, station, epg):
        '''
            Synchronises the EPG.
        '''

        # Cycles through each day

        for day in range(0, 7):

            # Find all the existing entries for this day

            existing_entries = list(
                EpgEntry.objects.filter(
                    station=station,
                    day=day
                )
            )

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

                if (match_found):
                    existing_entries.remove(match_found)
                else:
                    entry.station = station
                    entry.save()

            # Delete any unmatched entries

            for existing_entry in existing_entries:
                existing_entry.delete()

        # Clean up any old EPG entries

        old_epg_entries = EpgEntry.objects.filter(
            station=station,
            day__isnull=True
        ).delete()



