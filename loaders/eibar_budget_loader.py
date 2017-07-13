# -*- coding: UTF-8 -*-
from budget_app.models import *
from budget_app.loaders import SimpleBudgetLoader
from decimal import *
import csv
import os
import re

class EibarBudgetLoader(SimpleBudgetLoader):

    # Parse an input line into fields
    def parse_item(self, filename, line):
        # Programme codes have changed in 2015, due to new laws. Since the application expects a code-programme
        # mapping to be constant over time, we are forced to amend budget data prior to 2015.
        # See https://github.com/dcabo/presupuestos-aragon/wiki/La-clasificaci%C3%B3n-funcional-en-las-Entidades-Locales
        # TODO: it seems that the specific regional laws apply in a different way
        programme_mapping = {
        # old programme: new programme
        }

        # Institutional code (all income goes to the root node)
        ic_code = '000'

        # Description
        description = line[3].replace('..', '. ')
        description = description.strip()
        if not re.search('[A-Z]\.$',description):
            description = description.rstrip('.')

        # Type of data
        is_expense = (filename.find('gastos.csv')!=-1)
        is_actual = (filename.find('/ejecucion_')!=-1)

        # Expenses
        if is_expense:
            # We got a composite identifier, with more info, so we must isolate the functional code
            fc_code = line[0].strip()
            fc_code = fc_code[14:20]
            fc_code = fc_code.replace('.', '')

            # For years before 2015 we check whether we need to amend the programme code
            year = re.search('municipio/(\d+)/', filename).group(1)
            if int(year) < 2015:
                fc_code = programme_mapping.get(fc_code, fc_code)

            # We got a composite identifier, with more info, so we must isolate the economic code
            # On economic codes we get the first three digits (everything but last two)
            ec_code = line[0].strip()
            ec_code = ec_code[7:10]

            # Item numbers are the last two digits from the economic codes (fourth and fifth digit)
            item_number = line[0].strip()
            item_number = item_number[11:13]

            # Parse amount
            amount = line[10 if is_actual else 5].strip()
            amount = self._parse_amount(amount)

            return {
                'is_expense': True,
                'is_actual': is_actual,
                'fc_code': fc_code,
                'ec_code': ec_code,
                'ic_code': ic_code,
                'item_number': item_number,
                'description': description,
                'amount': amount
            }

        # Income
        else:
            # We got a composite identifier, with more info, so we must isolate the economic code
            # On economic codes we get the first three digits (everything but last two)
            ec_code = line[0].strip()
            ec_code = ec_code[2:5]

            # Item numbers are the last two digits from the economic codes (fourth and fifth digit)
            item_number = line[0].strip()
            item_number = item_number[6:8]

            # Parse amount
            amount = line[5 if is_actual else 4].strip()
            amount = self._parse_amount(amount)

            return {
                'is_expense': False,
                'is_actual': is_actual,
                'ec_code': ec_code,
                'ic_code': ic_code,
                'item_number': item_number,
                'description': description,
                'amount': amount
            }