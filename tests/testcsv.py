import csv
import re
import sys

fields = ['start', 'end', 'test', 'total', 'percent', 'name',]
writer = csv.DictWriter(sys.stdout, fields)
writer.writeheader()

# Previous timestamp (the start of the test)
ts = re.compile(r'^([-\dT:\.Z]+)')
start = None

# With percentage
pct = re.compile(r'^([-\dT:\.Z]+) \[(\d+)/(\d+)\] ?\((\d+%)\)?: (.*) *$')
pct_fields = ['end', 'test', 'total', 'percent', 'name',]

# Without percentage
pat = re.compile(r'^([-\dT:\.Z]+) \[(\d+)/(\d+)\]: (.*) *$')
pat_fields = ['end', 'test', 'total', 'name',]

for l in sys.stdin:
    result = pct.match(l.strip())
    if result:
        row = dict(zip(pct_fields, result.groups()))
        row['start'] = start
        start = row['end']
        writer.writerow(row)
        continue

    result = pat.match(l.strip())
    if result:
        row = dict(zip(pat_fields, result.groups()))
        row['percent'] = int(row['test']) * 100 // int(row['total'])
        row['start'] = start
        start = row['end']
        writer.writerow(row)
        continue

    result = ts.match(l.strip())
    if result:
        start = result.group(1)
        continue
