import importlib
import json
import os

def run():
    bank_settings = {
        'username': os.getenv('BANK_USERNAME'),
        'password': os.getenv('BANK_PASSWORD'),
        'dfp': os.getenv('BANK_DFP'),
        'cookie': os.getenv('BANK_COOKIE')
    }
    bank_module = importlib.import_module('bank')
    bank = bank_module.BankApi(bank_settings)

    bank.login()
    bank.switch_profile('I')

    bank_accounts = bank.get_accounts()
    settings_accounts = json.loads(os.getenv('ACCOUNTS'))

    accounts = dict([[
        [ba['contractAlias'] for ba in bank_accounts if ba['id'] == a['id']][0], a['ynab_id']
    ] for a in settings_accounts])

    transactions = bank.get_transactions(settings_accounts)
    ynab_transactions = [{
        'account_id': accounts[t['accountNumber']],
        'date': t['transactionDate'][:10],
        'amount': int(float(t['amount']) * 1000),
        'payee_name': t['description'][:100] if len(t['description']) > 100 else t['description'],
        'cleared': 'cleared',
        'approved': False,
        'import_id': 'mBank:{}'.format(t['pfmId'])
    } for t in transactions]

    ynab_module = importlib.import_module('ynab')
    ynab = ynab_module.YnabApi(os.getenv('YNAB_TOKEN'))

    response = ynab.post_transactions(os.getenv('YNAB_BUDGET_ID'), ynab_transactions)
    posted = len(response['transaction_ids'])
    existed = len(response['duplicate_import_ids'])
    print('Posted {} new transactions to YNAB. Tried to post {} that already existed.'.format(posted, existed))