import duckdb
import numpy as np
import pandas as pd

print(duckdb.__name__, duckdb.__version__)
print(np.__name__, np.__version__)
print(pd.__name__, pd.__version__)

# set seed
np.random.seed(19)

# connect to an in-memory temporary database
conn = duckdb.connect()

# https://stackoverflow.com/questions/50559078/generating-random-dates-within-a-given-range-in-pandas
def random_dates(start, end, n=10):

    start_u = start.value // 10 ** 9
    end_u = end.value // 10 ** 9

    return pd.to_datetime(np.random.randint(start_u, end_u, n), unit="s")


start = pd.to_datetime("2020-01-01")
end = pd.to_datetime("2021-01-01")

data = {"dt1": random_dates(start, end, n=5),
        "dt2": random_dates(start, end, n=5)}
df = pd.DataFrame(data)

SQL = """
      SELECT
      dt1,
      dt2,
      dt2 - dt1 as duck_diff
      from df
      """

res = conn.execute(SQL).fetchdf()

res["duck_diff"] = abs(res["duck_diff"])
res["pd_diff"] = abs(res["dt1"] - res["dt2"])
print(res)
