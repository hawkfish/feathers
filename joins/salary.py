import argparse
import csv
import random
import sys

# (1) Employees. A dataset that contains employees’ salary and tax information [3] with eight attributes:
# state, married, dependents, salary, tax, and three others for notes. The relation has been populated with real-life data:
# tax rates, in- come brackets, and exemptions for each state in the USA have been manually collected to generate
# synthetic tax records. We used the following self-join query to identify anomalies [7]:
#     Q1 : SELECT r.id, s.id
#     FROM Employees r, Employees s
#     WHERE r.salary < s.salary AND r.tax > s.tax;
# The above query returns a set of employee pairs, where one employee earns higher salary than the other but pays less tax.
# To make sure that we generate output for Q1, we selected 10% random rows and increased their tax values.
# Employees2 is a group of larger input datasets with up to 6 Billion records, but with only 0.001% random changes to tax values.
# The higher selectivity is used to test the distributed algorithm on large input files.

name = (
    "Smith",
    "Johnson",
    "Williams",
    "Jones",
    "Brown",
    "Davis",
    "Miller",
    "Wilson",
    "Moore",
    "Taylor",
    "Anderson",
    "Thomas",
    "Jackson",
    "White",
    "Harris",
    "Martin",
    "Thompson",
    "Garcia",
    "Martinez",
    "Robinson",
)

def main():
    parser = argparse.ArgumentParser(description='Generate a Salary table for IEJoin testing.')
    parser.add_argument('rows', metavar='N', type=int, default=10, help='The number of rows generated')
    parser.add_argument('--iterations', type=int, default=1, help='The number of salary iterations (default 1)')
    parser.add_argument('--delta', type=int, default=100, help='The number of rows to increase on each iteration (default 100)')
    parser.add_argument('--seed', type=int, default=8675309, help='The random number seed')
    parser.add_argument('--range', type=int, default=10, help='The amount to reduce random tax rates by (default 10)')
    parser.add_argument('--departments', type=int, default=5, help='The number of departments (default 5)')
    parser.add_argument('--extend', type=float, default=0.01, help='The fraction of events to extend (default 0.01)')

    args = parser.parse_args()

    random.seed(args.seed)

    # Progress count
    progress = args.rows // 100
    if progress < 100: progress = args.rows

    fieldnames = ('Name', 'Dept', 'Salary', 'Tax',)
    record = {field: None for field in fieldnames}

    writer = csv.DictWriter(sys.stdout, fieldnames)
    writer.writeheader()

    for it in range(args.iterations):
        sys.stderr.write('Iteration %d: ' % it)
        salary = 100;
        for row in range(args.rows):
            record['Name'] = random.choice(name)
            record['Dept'] = random.randint(0, args.departments)
            record['Salary'] = salary
            salary += 100

            tax = salary // 100
            if random.random() <= args.extend: tax -= (args.range + 1)
            record['Tax'] = tax

            writer.writerow(record)

            if 0 == row % progress:
                sys.stderr.write('.')
                sys.stderr.flush()

        sys.stderr.write('\n')

if __name__ == '__main__':
    main()
