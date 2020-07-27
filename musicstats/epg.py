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


class OnAir2:
    '''
    OnAir 2 Data Source
    '''

    data_source = None

    def __init__(self, data_source):
        '''
        Constructor for the OnAir2 helper
        '''

        if not isinstance(data_source, OnAir2DataSource):
            raise Exception('Data source must be an OnAir2 instance for this helper to work!')

        self.data_source = data_source

    def _tag_is_show_outer_div(self, tag):
        '''
        Indicates if the tag is the outer div for a show
        '''

        return tag.has_attr('class') and 'qt-part-show-schedule-day-item' in tag['class']

    def get_current_epg(self):
        '''
        Obtains the current EPG entry
        '''

        # Pull in the content

        try:
            result = requests.get(self.data_source.schedule_url)
            result.raise_for_status()
        except requests.exceptions.RequestException as ex:
            print(f'Failed to get EPG data from {self.data_source.schedule_url}. Reason: {ex}')
            return None

        # Make some soup (parse the HTML)

        soup = BeautifulSoup(result.text, features="html.parser")
        show_wrappers = soup.find_all(self._tag_is_show_outer_div)
        epg_entry = None

        for show_wrapper in show_wrappers:

            # Figure out if this is the current show

            current_show_badges = show_wrapper.find_all("span", text="Current show")
            if current_show_badges:

                # It's the current show pull some details out

                epg_entry = EpgEntry()
                epg_entry.image = show_wrapper.find("img")["src"]
                epg_entry.title = show_wrapper.find("a").text
                epg_entry.description = show_wrapper.find("p", {"class": "qt-ellipsis-2"}).text

                # Parse the start time from string

                start_time_text = show_wrapper.find("span", {"class": "qt-time"}).text
                epg_entry.start = datetime.strptime(start_time_text, "%H:%M").time()

                # Strip any forced resolution out of the image URL

                epg_entry.image = re.sub(r'-\d{3}x\d{3}', '', epg_entry.image)
                return epg_entry
