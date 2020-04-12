import importlib
import json

with open('settings.json') as f:
    settings = json.load(f)

    bank_module = importlib.import_module('bank')
    bank = bank_module.Bank()

    bank.get_accounts(settings)