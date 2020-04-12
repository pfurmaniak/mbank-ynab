import re
import requests
import uuid

class Bank:
    def __init__(self):
        self.__tab_id = None
        self.__token = None
        self.__base_url = 'https://online.mbank.pl'
        self.__session = requests.Session()
        self.__jar = requests.cookies.RequestsCookieJar()
    
    def format_url(self, url):
        return '{}{}'.format(self.__base_url, url)
    
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
        res = self.__session.send(request.prepare())
        self.__debug(res)
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

        res = self.__session.get(self.format_url('/pl'))
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
        print(res)
    
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

    def __debug(self, response):
        request = response.request
        print('{} {}'.format(request.method, request.url))
        print('  headers: {}'.format(request.headers))
        print('  body: {}'.format(request.body))
        print('{} {}'.format(response.status_code, response.reason))
        print('  headers: {}'.format(response.headers))
        if ('Content-Type' in response.headers and 'json' in response.headers['Content-Type']):
            print('  body: {}'.format(response.text))


# <meta 
# content="shEvEb8MVFMjvIgRCMb2IdjYv7ju2gdb4N9ubsXQfAXk63x42gNFBVBSvk92Xp7QKaKh64EVbADUJREdCh6pDjh1bPdb8At1aSaN4sL6HCTcyN5hJRaP34S2Zh0z/JWy4VmJQzeLqxeQEexq93yV9ooT51u0PisvHF5j41YIGSZP489X" 
# name="__AjaxRequestVerificationToken">