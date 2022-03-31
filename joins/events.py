import argparse
import csv
from datetime import date, datetime, timedelta
import random
import sys
import time


# (2) Events. A synthetic dataset that contains start and end time information for a set of independent events.
# Each event contains the name of the event, event ID, number of attending people, and the sponsor ID.
# We used this dataset with a self-join query that collects pairs of overlapping events:
# Q2 :  SELECT r.id, s.id
#       FROM Events r, Events s
#       WHERE r.start ≤ s.end AND r.end ≥ s.start AND r.id ≠ s.id;
# Again, to make sure we generate output for Q2, we selected 10% random events and extended their end values.
# We also generate Events2 as larger datasets with up to 6 Billion records, but with 0.001% extended random events.

def main():
    parser = argparse.ArgumentParser(description='Generate an Events table for IEJoin testing.')
    parser.add_argument('rows', metavar='N', type=int, default=10, help='The number of rows generated')
    parser.add_argument('--audience', type=int, default=5000, help='Maximum audience size (default 5000)')
    parser.add_argument('--sponsors', type=int, default=10, help='The number of sponsor IDs (default 10)')
    parser.add_argument('--seed', type=int, default=8675309, help='The random number seed')
    parser.add_argument('--date', type=datetime, default=datetime(1992, 1, 1), help='The first start date')
    parser.add_argument('--days', type=int, default=40*365, help='The number of days the events occur over')
    parser.add_argument('--extend', type=float, default=0.1, help='The fraction of events to extend')

    args = parser.parse_args()

    random.seed(args.seed)

    progress = args.rows // 100
    if progress < 100: progress = args.rows

    fieldnames = ('id', 'name', 'audience', 'start', 'end', 'sponsor',)
    record = {field: None for field in fieldnames}

    writer = csv.DictWriter(sys.stdout, fieldnames)
    writer.writeheader()
    for eid in range(1, args.rows+1):
        record['id'] = eid
        record['name'] = f"Event {eid}"
        record['sponsor'] = "Sponsor %d" % random.randint(1, args.sponsors)
        record['audience'] = random.randint(5, args.audience)

        start = args.date + timedelta(days=random.randint(0, args.days), hours=random.randint(0,23))
        record['start'] = start
        if random.random() < args.extend:
            record['end'] = start + timedelta(minutes=120)
        else:
            record['end'] = start + timedelta(minutes=random.randint(5, 55))

        writer.writerow(record)
        if 0 == eid % progress:
            sys.stderr.write('.')
            sys.stderr.flush()

    sys.stderr.write('\n')

if __name__ == '__main__':
    main()
