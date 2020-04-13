import importlib
import json

with open('settings.json') as f:
    settings = json.load(f)

    bank_module = importlib.import_module('bank')
    bank = bank_module.BankApi()

    bank_accounts = bank.get_accounts(settings['bank'])
    settings_accounts = settings['bank']['accounts']

    accounts = dict([[
        [ba['contractAlias'] for ba in bank_accounts if ba['id'] == a['id']][0], a['ynab_id']
    ] for a in settings_accounts])

    transactions = bank.get_transactions(settings['bank'])

    ynab_transactions = [{
        'account_id': accounts[t['accountNumber']],
        'date': t['transactionDate'][:10],
        'amount': int(float(t['amount']) * 1000),
        'payee_name': t['description'],
        'cleared': 'cleared',
        'approved': False,
        'import_id': 'mBank:{}'.format(t['pfmId'])
    } for t in transactions]

    ynab_module = importlib.import_module('ynab')
    ynab = ynab_module.YnabApi(settings['ynab']['token'])

    response = ynab.post_transactions(settings['ynab']['budget_id'], ynab_transactions)
    posted = len(response['transaction_ids'])
    existed = len(response['duplicate_import_ids'])
    print('Posted {} new transactions to YNAB. Tried to post {} that already existed.'.format(posted, existed))