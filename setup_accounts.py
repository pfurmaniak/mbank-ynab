import importlib
import json

with open('settings.json', 'r+', encoding='utf-8') as f:
    settings = json.load(f)

    ynab_module = importlib.import_module('ynab')
    ynab = ynab_module.YnabApi(settings['ynab']['token'])

    budgets = ynab.get_budgets()
    print('Choose one of the following YNAB budgets:')
    for (i, b) in enumerate(budgets):
        print('  {}) {}'.format(i + 1, b['name']))
    index = int(input('Your choice: '))
    settings['ynab']['budget_id'] = budgets[index - 1]['id']

    ynab_accounts = ynab.get_accounts(settings['ynab']['budget_id'])
    settings['ynab']['accounts'] = [{ 'id': a['id'], 'name': a['name'] } for a in ynab_accounts]

    print('')
    print('Accounts in YNAB:')
    for (i, a) in enumerate(settings['ynab']['accounts']):
        print('  {}) {}'.format(i + 1, a['name']))

    bank_module = importlib.import_module('bank')
    bank = bank_module.BankApi()

    print('')
    print('Accounts in bank:')
    accounts = bank.get_accounts(settings['bank'])
    for a in accounts:
        ynab_id = input('Map {} ({}) to YNAB account: '.format(a['name'], a['contractNumber']))
        if (ynab_id == ''):
            a['ynab_id'] = ''
        else:
            a['ynab_id'] = ynab_accounts[int(ynab_id) - 1]['id']
    settings['bank']['accounts'] = [{ 'id': a['id'], 'name': a['name'], 'number': a['contractNumber'], 'ynab_id': a['ynab_id'] } for a in accounts]

    f.truncate(0)
    json.dump(settings, f, ensure_ascii=False, indent=4)