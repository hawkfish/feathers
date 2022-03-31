import duckdb

conn = duckdb.connect()

conn.execute("PRAGMA threads=8")

t_path = "table3.csv"
q = f"CREATE TABLE table3 AS SELECT colA::VARCHAR AS colA, colC::BIGINT AS colC, colD::BIGINT AS colD, colE::BIGINT AS colE FROM read_csv_auto('{t_path}')"
conn.execute(q)

q = "SUMMARIZE table3"
print(conn.execute(q).fetchall())
# column_name column_type               min                  max  approx_unique                     avg    count null_percentage
#        colA     VARCHAR  1fbl0gkdkuevi800     1fedclvdguaoq800        9463409                     NaN  9443156            0.0%
#        colC      BIGINT                36               133616          16615       481.4576160766591  9443156            0.0%
#        colD      BIGINT     1220347017063  9223370609951035496        9446040  4.6102407801278725e+18  9443156            0.0%
#        colE      BIGINT                 0            588755658         177212      405537498.17566985  9443156            0.0%

# [
#     ('cola', 'VARCHAR', '1fbl0gkdkuevi800', '1fedclvdguaoq800', '2', None, 9443156, '0.0%'),
#     ('colc', 'BIGINT', '36', '133616', '830', '481.451663511648', 9443156, '0.0%'),
#     ('cold', 'BIGINT', '1220347017063', '9223370609951035496', '9539047', '4.6095508479221745e+18', 9443156, '0.0%'),
#     ('cole', 'BIGINT', '0', '588755658', '175550', '405383533.719532', 9443156, '0.0%')
#     ]

c_path = "combined_data1.csv"
q = f"CREATE TABLE combined_data1 AS SELECT colD::VARCHAR AS colD, colE::BIGINT AS COLE FROM read_csv_auto('{c_path}')"
conn.execute(q)

q = "SUMMARIZE combined_data1"
print(conn.execute(q).fetchall())
#            column_name column_type                                   min                                 max    approx_unique                   avg     count null_percentage
#                    colD     VARCHAR                  1000000202347220058                  999999908358388801         10244779                   NaN  10296550           0.72%
#                    colE      BIGINT                                    0                           588755658           177212    371929819.96801686  10296550            0.0%

# [
#     ('cold', 'VARCHAR', '1000000202347220058', '999999908358388801', '2', None, 10296550, '0.72%'),
#     ('cole', 'BIGINT', '0', '588755658', '177070', '371926594.26214147', 10296550, '0.0%')
#     ]

q = """select c.*, t3.colA,
    case when t3.colD is null then 1 else 0 end as colQ,
    t3.colC as t3_colC
from combined_data1 c
left join table3 t3 on c.colD = t3.colD
    and c.colE = t3.colE"""
q = "SELECT COUNT(*) FROM (%s)" % q
print(conn.execute(q).fetchall())
