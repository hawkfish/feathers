import statistics
import unittest

def sqldiv(x, y):
    if x is None or y is None or y == 0: return None
    return x / y

def sqlmod(x, y):
    if x is None or y is None or y == 0: return None
    return x % y

def sqlround(x, n=6):
    if x is None: return None
    return round(x, n)

def sqliff(p, t, e):
    if p is None: return None
    return t if p else e

def frame(a, p, preceding, following):
    n = len(a)
    preceding = 0 if preceding is None else max(0, p + preceding)
    following = n if following is None else min(n, p + following + 1)
    return a[preceding:following]

def mad(data):
    not_null = list(filter(lambda x: x is not None, data))
    if not not_null: return None
    m = statistics.median(not_null)
    return statistics.median([abs(d - m) for d in not_null])

class TestMedianAbsoluteDeviation(unittest.TestCase):

    def setUp(self):
        self.mads = [None,] * 3
        self.mads.extend(list(range(20)))

        self.thirds = [sqldiv(r, 3.0) for r in self.mads]
        self.half_null = [sqliff(sqlmod(r, 2) == 0, r, None) for r in self.mads]

    def test_constant(self):
        for d in range(-10, 10):
            self.assertEqual(0, mad((d / 10,)))

    def test_constants(self):
        data = [1,] * 2000
        self.assertEqual(0, mad(data))

    def assert_range(self, setup, expected):
        data = list(range(setup))
        self.assertEqual(expected, mad(data))

    def test_100(self):
        self.assert_range(100, 25.0)

    def test_2000(self):
        self.assert_range(2000, 500.0)

    def test_10000(self):
        self.assert_range(10000, 2500.0)

    def test_one_third(self):
        self.assertEqual(0.333333, mad([sqlround(r/3.0) for r in range(3)]))

    def assertRange(self, setup, expected, preceding, following):
        n = len(setup)

        actual = [sqlround(mad(frame(setup, p, preceding, following))) for p in range(n)]
        self.assertEqual(expected, actual)

    def test_range_from_1_to_1(self):
        expected = [0.333333 for x in self.mads]
        expected[0] = None
        expected[1] = None
        expected[2] = 0.0
        expected[3] = 0.166667
        expected[-1] = 0.166667
        self.assertRange(self.thirds, expected, -1, 1)

    def test_range_from_1_to_3(self):
        expected = [0.333333 for x in self.mads]
        expected[0] = 0.0
        expected[1] = 0.166667
        expected[-1] = 0.166667
        self.assertRange(self.thirds, expected, -1, 3)

    def test_range_from_1_to_1_nulls(self):
        expected = [sqliff(sqlmod(i, 2), 0.0, 1.0) for i in range(len(self.half_null))]
        expected[0] = None
        expected[1] = None
        expected[2] = 0.0
        expected[-1] = 0.0

        self.assertRange(self.half_null, expected, -1, 1)

    def test_range_from_1_to_3_nulls(self):
        expected = [sqliff(sqlmod(i, 2), 1.0, 2.0) for i in range(len(self.half_null))]
        expected[0] = 0.0
        expected[1] = 0.0
        expected[2] = 1.0
        expected[-3] = 1.0
        expected[-2] = 0.0
        expected[-1] = 0.0

    def test_range_from_unblonded_to_unbounded_nulls(self):
        expected = [5.0 for n in self.half_null]

        self.assertRange(self.half_null, expected, None, None)

if __name__ == '__main__':
    unittest.main()

