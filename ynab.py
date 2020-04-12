import importlib
import requests

api = importlib.import_module('api')

class YnabApi(api.Api):
    def __init__(self, token):
        super().__init__('https://api.youneedabudget.com/v1')
        self.__token = token

    def prepare_request(self, method, url):
        headers = {
            'Authorization': 'Bearer {}'.format(self.__token),
            'Content-Type': 'application/json'
        }
        return requests.Request(method, self.format_url(url), headers=headers)
    
    def send_request(self, request):
        request.headers['Authorization'] = 'Bearer {}'.format(self.__token)
        request.headers['Content-Type'] = 'application/json'
        res = self.session.send(request.prepare())
        try:
            return res.json()
        except:
            return res.text

    def get_budgets(self):
        req = self.prepare_request('GET', '/budgets')
        res = self.send_request(req)
        return res['data']['budgets']

    def get_accounts(self, budget_id):
        req = self.prepare_request('GET', '/budgets/{}/accounts'.format(budget_id))
        res = self.send_request(req)
        return res['data']['accounts']