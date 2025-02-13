#!./.venv/bin/python

import argparse
import csv
import duckdb
import os
import time

timeout = 600

def generate_prices(con, sizes):
    max_size = max(sizes)

    # Create the largest table
    sql = f"""
        CREATE OR REPLACE TABLE prices_{max_size} AS
        SELECT
            r AS id,
            '2021-01-01T00:00:00'::TIMESTAMP + INTERVAL (random() * 60 * 60 * 24 * 365) SECOND AS time,
            (random() * 100000)::INTEGER AS price,
        FROM range({max_size}) tbl(r);
    """
    con.sql(sql)

    # Now generate the smaller tables
    for size in sizes:
        if size == max_size: continue

        sql = f"""
            CREATE OR REPLACE TABLE prices_{size} AS
            FROM prices_{max_size}
            WHERE id < {size}
        """
        con.sql(sql)

def generate_times(con, sizes):
    max_size = max(sizes)

    # Create the largest table
    sql = f"""
        CREATE OR REPLACE TABLE times_{max_size} AS
            SELECT
                r AS id,
                '2021-01-01'::TIMESTAMP + INTERVAL ((365 * 24 * 60 * 60 * RANDOM())::INTEGER) SECONDS AS probe
            FROM range({max_size}) tbl(r);
    """
    con.sql(sql)

    # Now generate the smaller tables
    for size in sizes:
        if size == max_size: continue

        sql = f"""
            CREATE OR REPLACE TABLE times_{size} AS
            FROM times_{max_size}
            WHERE id < {size}
        """
        con.sql(sql)

def build_dict(record, key, dflt):
    if key not in record:
        record[key] = dflt
    return record[key]

def read_history(path):
    history = {}
    if os.path.exists(path):
        with open(path, "r" , newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            for row in reader:
                record = history
                record = build_dict(record, int(row['threads']), {})
                record = build_dict(record, int(row['build']), {})
                record = build_dict(record, row['algorithm'], {})
                runs = build_dict(record, int(row['probe']), [])
                runs.append(float(row['timing']))

    return history

def run_benchmark(con, history, threads, algorithm, build, probe, cutoff, runs=5):
    worst = 0

    # Check history for this run and just echo it if we already have it
    record = history
    for key in (threads, build, algorithm, probe,):
        if key in record:
            record = record[key]
        else:
            record = None
            break

    if record:
        for run, timing in enumerate(record):
            worst = max(worst, timing)
            print(f"{algorithm},{build},{probe},{run+1},{timing},{threads}", flush=True)
        return worst

    iejoin = 'True' if algorithm == 'iejoin' else 'False'

    threshold = 0
    if algorithm == 'nlj':
        threshold = 2048
    elif algorithm == 'pwmj':
        threshold = -2048

    con.sql(f"PRAGMA debug_asof_iejoin={iejoin};")
    con.sql(f"PRAGMA asof_loop_join_threshold={threshold};")
    con.sql(f"PRAGMA threads={threads};")

    sql = f"""
        SELECT COUNT(*) FROM (
            SELECT
              t.probe,
              p.price
            FROM times_{probe} t
              ASOF JOIN prices_{build} p
              ON t.probe >= p.time
            ) t
    """

    # Warmup
    try:
        start = time.time()
        con.execute(sql)
        end = time.time()
        timing = end - start
        worst = max(worst, timing)

        # If the timing is too long, just write out this one example
        if timing > timeout:
            print(f"{algorithm},{build},{probe},0,{timing},{threads}", flush=True)
            return worst

        # Abort if the time is twice as slow as the cutoff
        if algorithm == 'nlj' and worst > 2 * cutoff:
            return worst
    except:
        print(sql)
        raise

    # Timed runs
    for run in range(runs):
        start = time.time()
        con.execute(sql)
        end = time.time()
        timing = end - start
        worst = max(worst, timing)
        print(f"{algorithm},{build},{probe},{run+1},{timing},{threads}", flush=True)
        if worst > timeout: break

    return worst

def main():
    arg_parser = argparse.ArgumentParser(
        prog="asof.py",
        description="AsOf Optimisation Data tester",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    arg_parser.add_argument(
        "-d",
        "--database",
        type=str,
        default="fnord.db",
        help="Database for the test data",
    )
    arg_parser.add_argument(
        "-g",
        "--generate",
        default=False,
        action="store_true",
        help="Regenerate the data",
    )
    arg_parser.add_argument(
        "-P",
        "--max-price",
        type=int,
        default=1_000_000_000,
        help="Maximum price table count",
    )
    arg_parser.add_argument(
        "-p",
        "--min-price",
        type=int,
        default=100_000,
        help="Minimum price table count",
    )
    arg_parser.add_argument(
        "-T",
        "--max-time",
        type=int,
        default=2048,
        help="Maximum time table count",
    )
    arg_parser.add_argument(
        "-t",
        "--min-time",
        type=int,
        default=1,
        help="Minimum time table count",
    )
    arg_parser.add_argument(
        "-l",
        "--history",
        type=str,
        default="asof.csv",
        help="Results of previoud runs",
    )
    args = arg_parser.parse_args()

    if not os.path.exists(args.database):
        args.generate = True

    con = duckdb.connect(args.database)

    # Price sizes are steps of 10
    prices = []
    p = args.max_price
    while p >= args.min_price:
        prices.append(p)
        p = p // 10

    # Times are multiples of 2
    times = []
    t = args.min_time
    while t <= args.max_time:
        times.append(t)
        t *= 2

    algorithms = ('asof', 'nlj', 'pwmj', 'iejoin',)

    threads = (36, 18, 9,)

    if args.generate:
        con.sql('SELECT SETSEED(0.8675309);')
        generate_prices(con, prices)
        generate_times(con, times)

    history = read_history(args.history)

    print("algorithm,build,probe,run,timing,threads", flush=True)
    for thread in threads:
        for build in prices:
            cutoff = 0
            for algorithm in algorithms:
                for probe in times:
                    worst = run_benchmark(con, history, thread, algorithm, build, probe, cutoff)
                    if algorithm == 'asof':
                        cutoff = max(cutoff, worst)
                    elif algorithm == 'iejoin':
                        if worst > cutoff and worst > timeout:
                            break
                    elif worst > cutoff:
                        break

if __name__ == "__main__":
    main()
