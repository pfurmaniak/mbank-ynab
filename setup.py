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
bank = bank_module.Bank(settings)
# settings['cookie'] = bank.authorize(settings)

ynab_token = input('YNAB token: ')
ynab_module = importlib.import_module('ynab')
ynab = ynab_module.YnabApi(ynab_token)

budgets = ynab.get_budgets()
print('Choose one of the following YNAB budgets:')
for (i, b) in enumerate(budgets):
    print('  {}) {}'.format(i + 1, b['name']))
index = int(input('Your choice: '))
ynab_budget_id = budgets[index - 1]['id']

print('')
print('Accounts in YNAB:')
ynab_accounts = ynab.get_accounts(ynab_budget_id)
for (i, a) in enumerate(ynab_accounts):
    print('  {}) {}'.format(i + 1, a['name']))

print('')
print('Accounts in bank:')
bank_accounts = bank.get_accounts()
for a in bank_accounts:
    ynab_id = input('Map {} ({}) to YNAB account: '.format(a['name'], a['contractNumber']))
    if (ynab_id == ''):
        a['ynab_id'] = ''
    else:
        a['ynab_id'] = ynab_accounts[int(ynab_id) - 1]['id']

accounts = [{ 'id': a['id'], 'ynab_id': a['ynab_id'] } for a in bank_accounts]

with open('.env', 'w', encoding='utf-8') as f:
    f.write('BANK_USERNAME={}\n'.format(settings['username']))
    f.write('BANK_PASSWORD={}\n'.format(settings['password']))
    f.write('BANK_DFP={}\n'.format(settings['dfp']))
    f.write('BANK_COOKIE={}\n'.format(settings['cookie']))
    f.write('YNAB_TOKEN={}\n'.format(ynab_token))
    f.write('YNAB_BUDGET_ID={}\n'.format(ynab_budget_id))
    f.write('ACCOUNTS={}\n'.format(json.dumps(accounts, ensure_ascii=False)))