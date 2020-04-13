import datetime
import importlib
import re
import requests
import uuid
from bs4 import BeautifulSoup

api = importlib.import_module('api')

class BankApi(api.Api):
    def __init__(self):
        super().__init__('https://online.mbank.pl')
        self.__tab_id = None
        self.__token = None
        self.__jar = requests.cookies.RequestsCookieJar()
    
    def prepare_request(self, method, url):
        headers = {
            'X-Requested-With': 'XMLHttpRequest'
        }
        if (self.__tab_id is not None):
            headers['X-Tab-Id'] = self.__tab_id
        if (self.__token is not None):
            headers['X-Request-Verification-Token'] = self.__token
        return requests.Request(method, self.format_url(url), headers=headers, cookies=self.__jar)

    def parse_cookies(self, set_cookie):
        cookies = set_cookie.split('; ')
        for i, c in enumerate(cookies):
            if (', ' in c):
                cookies[i] = c.split(', ')[1]
        return [c.split('=', 1) for c in cookies if 'mBank' in c]
    
    def send_request(self, request):
        res = self.session.send(request.prepare())
        # self.debug(res)
        if ('Set-Cookie' in res.headers):
            for c in self.parse_cookies(res.headers['Set-Cookie']):
                self.__jar.set(c[0], c[1])
        try:
            return res.json()
        except:
            return res.text
    
    def __login(self, settings):
        if ('cookie' in settings):
            self.__jar.set('mBank8', settings['cookie'])

        res = self.session.get(self.format_url('/pl'))
        match = re.search(r'app.initialize\(\'([\w=-]+)\'', res.text)
        if (match is None):
            raise Exception('Seed not found.')
        seed = match.groups()[0]

        req = self.prepare_request('POST', '/pl/LoginMain/Account/JsonLogin')
        req.json = {
            'Username': settings['username'],
            'Password': settings['password'],
            'Scenario': 'Default',
            'Seed': seed,
            'Lang': '',
            'DfpData': {
                'Dfp': settings['dfp'],
                'ScaOperationId': str(uuid.uuid4())
            }
        }
        res = self.send_request(req)
        if (res['successful'] == 'false'):
            raise Exception('Login failed.')
        self.__tab_id = res['tabId']
    
    def login(self, settings):
        self.__login(settings)

        req = self.prepare_request('GET', '/pl')
        res = self.send_request(req)
        soup = BeautifulSoup(res, features="html.parser")
        tag = soup.head.find('meta', attrs={ 'name': '__AjaxRequestVerificationToken' })
        self.__token = tag['content']
    
    def authorize(self, settings):
        self.__login(settings)
        
        req = self.prepare_request('GET', '/authorization')
        self.send_request(req)

        req = self.prepare_request('GET', '/api/app/setup/data')
        req.headers['Referer'] = self.format_url('/authorization')
        res = self.send_request(req)
        self.__token = res['antiForgeryToken']

        req = self.prepare_request('POST', '/pl/Sca/GetScaAuthorizationData')
        res = self.send_request(req)
        if (res['TrustedDeviceAddingAllowed'] == 'false'):
            raise Exception('Cannot add a new trusted device.')

        sca_authorization_id = res['ScaAuthorizationId']
        device_name = str(uuid.uuid4())[:8]

        req = self.prepare_request('POST', '/api/auth/initprepare')
        req.json = {
            'Url': 'sca/authorization/trusteddevice',
            'Method': 'POST',
            'Data': {
                'ScaAuthorizationId': sca_authorization_id,
                'DfpData': settings['dfp'],
                'DeviceName': device_name,
                'IsTheOnlyDeviceUser': True
            }
        }
        res = self.send_request(req)
        if (res['Status'] != 'Prepared'):
            raise Exception('Error while adding a new device.')

        print('Waiting for confirmation on your device {}...'.format(res['DeviceName']))
        input('Press any key once you confirm')

        req = self.prepare_request('POST', '/api/auth/status')
        req.json = {
            'TranId': res['TranId']
        }
        res = self.send_request(req)
        if (res['Status'] != 'Authorized'):
            raise Exception('Error while confirming the new device.')

        req = self.prepare_request('POST', '/api/auth/execute')
        req.json = {}
        res = self.send_request(req)

        req = self.prepare_request('POST', '/pl/Sca/FinalizeTrustedDeviceAuthorization')
        req.json = {
            'ScaAuthorizationId': sca_authorization_id,
            'CurrentDfp': settings['dfp'],
            'DeviceName': device_name
        }
        res = self.send_request(req)

        return self.__jar.get('mBank8')

    def get_accounts(self, settings):
        if (self.__tab_id is None or self.__token is None):
            self.login(settings)
        
        req = self.prepare_request('GET', '/pl/Pfm/HistoryApi/GetPfmInitialData')
        res = self.send_request(req)
        return res['pfmProducts']

    def get_transactions(self, settings):
        if (self.__tab_id is None or self.__token is None):
            self.login(settings)
        
        accounts = [a for a in settings['accounts'] if a['ynab_id'] != '']

        dateTo = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        dateFrom = dateTo - datetime.timedelta(days=2)
        
        req = self.prepare_request('GET', '/pl/Pfm/HistoryApi/GetOperationsPfm')
        req.params = {
            'productIds': ','.join([a['id'] for a in accounts]),
            'dateFrom': dateFrom.isoformat(),
            'dateTo': dateTo.isoformat()
        }
        res = self.send_request(req)
        return res['transactions']