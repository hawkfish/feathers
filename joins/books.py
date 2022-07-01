import csv
import datetime
import sys

fieldnames = ['checkout', 'return', 'faustnummer', 'library', 'postcode', 'age',]

columns = ['type', 'return', 'faustnummer', 'library', 'postcode', 'age',]
bookid = columns[2:]
casts = {'type': int, 'postcode': int, 'age': int}

active = {}

min_time = None
max_time = None

def cast_fields(row, casts):
    for field, cast in casts.items():
        if row[field]: row[field] = cast(row[field])

def process_line(line, writer):
    global max_time
    global min_time
    global active

    row = {c: None for c in columns}
    row.update(dict(zip(columns, line.split('\t'))))

    cast_fields(row, casts)

    max_time = datetime.datetime.strptime(row['return'], '%Y%m%dT%H')
    if not min_time: min_time = max_time
    row['return'] = max_time


    book = tuple(row[k] for k in bookid)
    checkouts = active.get(book, [])

    if row['type'] == 1:
        # Checked out
        checkouts.append(max_time)
        active[book] = checkouts

    else:
        # Returned
        row['checkout'] = min_time
        del row['type']

        # Find the first checkout before this return
        idx = next((i for i, e in enumerate(checkouts) if e <= max_time), -1)
        if idx >= 0:
            row['checkout'] = checkouts.pop(idx)

        if row['checkout'] != row['return']:
            writer.writerow(row)

writer = csv.DictWriter(sys.stdout, fieldnames)
writer.writeheader()

for line in sys.stdin:
    try:
        process_line(line.strip(), writer)
    except:
        print(line, sys.stderr)
        raise

# Dangling checkouts
for book, checkouts in active.items():
    row = dict(zip(bookid, book))
    for checkout in checkouts:
        row['checkout'] = checkout
        row['return'] = max_time
        if row['checkout'] != row['return']:
            writer.writerow(row)
