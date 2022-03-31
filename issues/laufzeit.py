import csv
import datetime
import random
import sys

n = 26000

def epoch(iso):
    return datetime.datetime.fromisoformat(iso).timestamp()

bounds = {
    'timestamp': (epoch('2020-10-15 16:45:00'), epoch('2020-10-15 17:00:00'),),
    'laufzeit': (0, 100,),
}

def randomInt(field):
    lo, hi = bounds[field]
    return {field: random.randint(lo, hi)}

def randomTimestamp(field):
    lo, hi = bounds[field]
    return {field: datetime.datetime.fromtimestamp(random.uniform(lo, hi))}

writer = csv.DictWriter(sys.stdout, bounds.keys())
writer.writeheader()
for r in range(n):
    row = randomTimestamp('timestamp')
    row.update(randomInt('laufzeit'))
    writer.writerow(row)

