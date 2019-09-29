'''
MusicStats Pagination Settings
'''

from rest_framework.pagination import PageNumberPagination

class MusicstatsPagination(PageNumberPagination):
    '''
    Default pagination for the application.
    '''

    page_size = 0
    page_size_query_param = 'page_size'
    max_page_size = 1000
