import csv
import collections
import datetime
import glob
import dateutil.parser
import decimal
from exchange import exchange

incomes = {}

Income = collections.namedtuple('Income', 'date amount client type')

def parse_income(line):
    amount = decimal.Decimal(line['Amount'])
    date = dateutil.parser.parse(line['Date'])
    date = datetime.date(date.year, date.month, date.day)
    if line['Type'] == 'Withdrawal':
        return None
    return Income(date, amount, line['Client'], line['Type'])

def read_income(name):
    for line in csv.DictReader(open(name)):
        income = parse_income(line)
        if income:
            incomes[line['Ref ID']] = income

for name in glob.glob('statement_*.csv'):
    read_income(name)

def read_countries():
    resp = {}
    for line in csv.reader(open('kraje.csv')):
        k, v = line
        resp[k] = v
    return resp

countries = read_countries()

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

by_country = collections.defaultdict(decimal.Decimal)
sums_global = collections.defaultdict(decimal.Decimal)

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
        'Hourly': 'zlecenie',
        'Bonus': 'inne',
        'Upfront Payment': 'inne',
    }
    deductible = {
        'o-dzielo': decimal.Decimal(0.2),
        'zlecenie': decimal.Decimal(0.2),
        'inne': decimal.Decimal(0.2),
    }
    need_advance = ['o-dzielo', 'zlecenie']
    tax_value = decimal.Decimal(0.19)

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
        print('%s, kwota: %s USD = %s PLN, klient: %s, umowa: %s, kraj: %s' % (
            income.date, income.amount, pln, income.client, type, country))

    print()
    print('Umowy:')
    for k, v in sums.items():
        print('  %s: %s PLN' % (k, v))
    print()

    advance_sum = decimal.Decimal(0)
    for type in need_advance:
        tax_base = sums[type] * (1 - deductible[type])
        tax = money_round(tax_base * tax_value)
        print('Zaliczna od %s: %s PLN' % (type, tax))
        advance_sum += tax

    print('Zaliczna w sumie: %s PLN' % unit_round(advance_sum))


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
