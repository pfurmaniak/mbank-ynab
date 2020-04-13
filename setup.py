import importlib
import json

settings = {}
settings['username'] = input('Username: ')
settings['password'] = input('Password: ')
print('In order to get the next required value, open your browser in incognito mode, navigate to https://online.mbank.pl')
print('enter Developer Tools (F12), go to Console and execute the following command:')
print('  Ebre.Behaviour.GetCurrentDfp()._rejectionHandler0')
settings['dfp'] = input('DfpData: ')

bank_module = importlib.import_module('bank')
bank = bank_module.Bank()
settings['cookie'] = bank.authorize(settings)

with open('settings.json', 'w', encoding='utf-8') as f:
    json.dump(settings, f, ensure_ascii=False, indent=4)
