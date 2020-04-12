import requests

class Api:
    def __init__(self, base_url):
        self.__base_url = base_url
        self.session = requests.Session()
    
    def format_url(self, url):
        return '{}{}'.format(self.__base_url, url)
    
    def debug(self, response):
        request = response.request
        print('{} {}'.format(request.method, request.url))
        print('  headers: {}'.format(request.headers))
        print('  body: {}'.format(request.body))
        print('{} {}'.format(response.status_code, response.reason))
        print('  headers: {}'.format(response.headers))
        if ('Content-Type' in response.headers and 'json' in response.headers['Content-Type']):
            print('  body: {}'.format(response.text))