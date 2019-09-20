'''
EPG Helper Classes
'''

import requests
from bs4 import BeautifulSoup
from musicstats.models import OnAir2DataSource, EpgEntry

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

        soup = BeautifulSoup(result.text)
        show_wrappers = soup.find_all(self._tag_is_show_outer_div)
        for show_wrapper in show_wrappers:

            # Figure out if this is the current show

            current_show_badges = show_wrapper.find_all("span", text="Current show")
            if current_show_badges:

                # It's the current show pull some details out

                epg_entry = EpgEntry()
                epg_entry.image = show_wrapper.find("img")["src"]
                epg_entry.title = show_wrapper.find("a").text
                epg_entry.description = show_wrapper.find("p", {"class": "qt-ellipsis-2"}).text

                time_text = show_wrapper.find("p", {"class": "qt-ellipsis-2"}).text

                return epg_entry