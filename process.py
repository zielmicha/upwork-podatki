from __future__ import print_function
import csv
import collections
import datetime
import glob
import dateutil.parser
import decimal
from decimal import Decimal
from exchange import exchange

incomes = {}

Income = collections.namedtuple('Income', 'date amount amount_before_fee client type')

def parse_income(line):
    amount = decimal.Decimal(line['Amount'])
    date = dateutil.parser.parse(line['Date'])
    date = datetime.date(date.year, date.month, date.day)
    if line['Type'] in ('Withdrawal', 'Withdrawal Fee'):
        return None

    if line['Type'] == 'Service Fee':
        arr = line['Description'].split(' - ')
        assert arr[0] == 'Service Fee'
        assert arr[2].startswith('Ref ID ')
        fee_for_id = int(arr[2].split(None)[2])
        fee_for = incomes[fee_for_id]
        assert amount <= 0
        assert abs((fee_for.amount / 10 + amount) / amount) < 0.01, 'Unexpected value of Service Fee'
        incomes[fee_for_id] = fee_for._replace(amount=fee_for.amount + amount)
        return None

    try:
        client = line['Client']
    except KeyError:
        client = line['Team']
    return Income(date, amount, amount, client, line['Type'])

def read_income(name):
    for line in reversed(list(csv.DictReader(open(name)))):
        income = parse_income(line)
        if income:
            if income.date <= datetime.date.today():
                incomes[int(line['Ref ID'])] = income

for name in glob.glob('statement_*.csv'):
    read_income(name)

def read_countries():
    resp = {}
    for line in csv.reader(open('kraje.csv')):
        k, v = line
        resp[k] = v
    return resp

countries = read_countries()


def read_advances():
    resp = {}
    for line in csv.reader(open('zaliczki.csv')):
        year, month, value = line
        resp[(int(year), int(month))] = decimal.Decimal(value)
    return resp

paid_advances = read_advances()

def money_round(dec):
    return dec.quantize(decimal.Decimal('0.01'),
                        rounding=decimal.ROUND_UP)

def unit_round(dec):
    return dec.quantize(decimal.Decimal('1.'),
                        rounding=decimal.ROUND_UP)

def split_by_month():
    month = None
    current = None
    for income in sorted(incomes.values(), key=lambda a: a.date):
        date = income.date
        curr_month = (date.year, date.month)
        if month != curr_month:
            if current:
                yield month, current
            month = curr_month
            current = []
        current.append(income)
    if current:
        yield month, current

def calculate_tax(value):
    granica = 85528
    if value < granica:
        tax = Decimal('.18') * value - Decimal('556.02')
        ret = max(tax, Decimal(0))
    else:
        ret = Decimal('14839.02') + Decimal('.32') * (value - granica)
    return money_round(ret)

by_country = collections.defaultdict(decimal.Decimal)
sums_global = collections.defaultdict(decimal.Decimal)
global_advance_paid = 0
global_advance_base = 0

for month, month_incomes in split_by_month():
    print()
    print('Month', month)
    print('------------')
    sums = {
        'o-dzielo': decimal.Decimal(),
        'zlecenie': decimal.Decimal(),
        'inne': decimal.Decimal(),
    }
    type_map = {
        'Milestone': 'o-dzielo',
        'Fixed Price': 'o-dzielo',
        'Expense': 'o-dzielo', # always?
        'Hourly': 'zlecenie',
        'Bonus': 'inne',
        'Upfront Payment': 'inne',
    }
    deductible = {
        'o-dzielo': decimal.Decimal(0.2),
        'zlecenie': decimal.Decimal(0.2),
        'inne': decimal.Decimal(0),
    }
    need_advance = ['o-dzielo', 'zlecenie',
                    'inne' # nieobowiazkowe
    ]

    paid_advance = paid_advances.get(month, 0)

    for income in month_incomes:
        pln = exchange(amount=float(income.amount),
                       date=income.date,
                       currency='1 USD')
        pln = money_round(decimal.Decimal(pln))
        type = type_map.get(income.type, income.type)
        country = countries[income.client]
        by_country[country] += pln
        sums[type] += pln
        sums_global[type] += pln
        print('%s, kwota: %s USD = %s PLN (before fee %s USD), klient: %s, umowa: %s, kraj: %s' % (
            income.date, income.amount, pln, income.amount_before_fee, income.client, type, country))

    print()
    print('Umowy:')
    for k, v in sums.items():
        print('  %s: %s PLN' % (k, v))
    print('W sumie: %s PLN' % sum(sums.values()))
    print()

    print('Zaliczka wplacona: %s PLN' % paid_advance)
    global_advance_paid += paid_advance
    print('Zaliczka wplacona (caly rok): %s PLN' % global_advance_paid)
    for type in need_advance:
        tax_base = sums[type] * (1 - deductible[type])
        global_advance_base += money_round(tax_base)

    print('Podstawa zaliczki (caly rok): %s PLN' % (global_advance_base))
    global_advance = calculate_tax(global_advance_base)
    print('Zaliczka (caly rok): %s PLN' % global_advance)
    print('Zaliczna do zaplacenia: %s PLN' % unit_round(global_advance - global_advance_paid))


print()
print('Podsumowanie')
print('-------------')
print('PIT-ZG:')
for k, v in by_country.items():
    print('  %s: %s PLN' % (k, v))
print()
print('Umowy:')
for k, v in sums_global.items():
    print('  %s: %s PLN' % (k, v))
print('W sumie: %s PLN' % sum(sums_global.values()))
