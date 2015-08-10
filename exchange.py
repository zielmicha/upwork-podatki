import xlrd
import glob
import datetime
import logging

values = {}

def load_exchange(name):
    sheets = xlrd.open_workbook(name).sheets()
    if len(sheets) != 1:
        raise ValueError('expected exactly one sheet in %r' % name)
    s = sheets[0]
    rows = [ [ s.cell(r, c) for c in range(s.ncols) ] for r in range(s.nrows) ]
    currencies = [ col.value for col in rows[0][1:] ][:-2]
    for row in rows[2:]:
        val = row[0].value
        if not val: break
        days = float(val)
        delta = datetime.timedelta(days=days - 2)
        date = datetime.date(1900, 1, 1) + delta
        vals = {}
        for i, currency in enumerate(currencies):
            vals[currency] = row[i + 1].value
        values[date] = vals

def exchange_rate(date, currency):
    assert isinstance(date, datetime.date)
    for i in range(1, 4):
        check_date = date - datetime.timedelta(days=i)
        if check_date in values:
            return values[check_date][currency]
    raise Exception('failed to find exchange rate %r at %r' % (
        currency, date))

def exchange(date, amount, currency):
    rate = exchange_rate(date, currency)
    return rate * amount

files = glob.glob('nbp/*.xls')

if not files:
    logging.error('No NBP exchange rate archives found.')

for name in files:
    load_exchange(name)

if __name__ == '__main__':
    print(exchange(datetime.date(2014, 2, 8), 20, '1 USD'))
