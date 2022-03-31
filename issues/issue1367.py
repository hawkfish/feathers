import time
import random
import duckdb

db = duckdb.connect(':memory:')
db.execute('select setseed(0.5)')
db.execute('create table data AS SELECT id, (random() * 100000)::INTEGER val FROM range(0,1000000) tbl(id)')
db.commit()

print("Beginning query...")
start = time.time()
db.execute('select val, row_number() over(order by id) from data limit 1').fetchall()
duration = time.time() - start
print(f'{duration:.3f} s')
