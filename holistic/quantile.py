import statistics
import unittest

def Rank1(n):
    table = [{'a': 0, 'b': i} for i in range(n)]
    table.sort(key=lambda r: -hash(r['b']))
    return table

def Rank100(n, p):
    return [{'a': i % p, 'b': i} for i in range(n)]

class Frame:
    def __init__(self, l=0, r=0):
        self._l = l
        self._r = r

    def Length(self):
        return self._r - self._l

    def Contains(self, idx):
        return self._l  <= idx and idx < self._r

    def Range(self):
        return range(self._l, self._r)

    def Slice(self, values):
        return values[self._l:self._r]

    def Before(self, other):
        return range(self._l, other._l)

    def After(self, other):
        return range(other._r, self._r)

    def Shift(self, delta=1):
        return Frame(self._l+delta, self._r+delta)

def Swap(index, l, r):
    index[l], index[r] = index[r], index[l]

def Partition(values, index, l, r, p):
    v  =  values[index[p]]
    Swap(index, p, r)
    s = l
    for i in range(l,r):
        if values[index[i]] < v:
            Swap(index, s, i)
            s = s + 1

    Swap(index, s, r)
    return s

def QSelect(k, values, index, l, r):
    while l < r:
        p = (l + r) // 2
        p = Partition(values, index, l, r - 1, p)
        if k == p:
            break
        elif k < p:
            r = p
        else:
            l = p+1

def NaiveQuantile(values, quants, frames):
    result = []
    for i in range(len(frames)):
        F = frames[i]
        k = int(quants[i] * (F.Length() - 1))
        index = [j for j in F.Range()]
        QSelect(k, values, index, 0, F.Length())
        result.append(values[index[k]])
    return result

def ReuseIndexes(index, F, P):
    j = 0

    #   Copy overlapping indices
    for p in range(P.Length()):
        idx = index[p]

        #   Shift:wn into any hole
        if j != p:
            index[j] = idx

        #   Skip overlapping values
        if F.Contains(idx):
            j = j + 1

    #   Insert new indices
    if j > 0:
        #   Overlap: append the new ends
        for f in F.Before(P):
            index[j] =  f
            j = j+1
        for f in F.After(P):
            index[j] = f
            j = j+1

    else:
        #   No overlap: overwrite with new values
        for f in F.Range():
            index[j] = f
            j = j+1

def ReuseQuantile(values, quants, frames):
    result = []
    P = Frame()
    index = [i for i in range(len(values))]
    for i in range(len(frames)):
        F = frames[i]
        k = int(quants[i] * (F.Length() - 1))
        ReuseIndexes(index, F, P)
        QSelect(k, values, index, 0, F.Length())
        result.append(values[index[k]])
        P = F

    return result

def ReplaceIndex(prev, k, values, index, F, P):
    same = False

    j = 0
    for f in range(P.Length()):
        idx = index[f]
        if j != f:
            break

        if InFrame(idx, F):
            j += 1

    index[j] = F[1] - 1
    if k < j:
        same = prev < values[index[j]]

    elif j < k:
        same = values[index[j]] < prev

    return same

def ReplaceQuantile(values, quants, frames):
    result = []
    P = Frame()
    index = [i for i in range(len(values))]
    for i in range(len(frames)):
        F = frames[i]
        k = int(quants[i] * (F.Length() - 1))
        same = False

        if P.Shift() == F:
            #   Fixed frame size
            same = ReplaceIndex(result[i-1], k, values, index, F, P)
        else:
            ReuseIndexes(index, F, P)

        if same:
            result.append(result[i-1])

        else:
            QSelect(k, values, index, 0, F.Length())
            result.append(values[index[k]])

        P = F

    return result

class TestPartition(unittest.TestCase):

    def test_rank1(self):
        rank1 = Rank1(10)
        self.assertEqual(10, len(rank1))

    def assertPartitioned(self, values, index, k, l, r):
        for i in range(l, k):
            self.assertTrue(values[index[i]] <= values[index[k]], i)

        for i in range(k, r):
            self.assertTrue(values[index[k]] <= values[index[i]], i)

    def test_midpoint(self):
        l = 0
        r = 10
        p = (l + r) // 2
        table = Rank1(r * 2)
        values = [row['b'] for row in table]
        index = [i for i in range(l, r)]

        s = Partition(values, index, l, r-1, p)
        self.assertEqual((r - 1) // 2, s)
        self.assertPartitioned(values, index, s, l, r)

    def test_qselect(self):
        l = 0
        r = 16
        table = Rank1(r)
        values = [row['b'] for row in table]
        index = [i for i in range(l, r)]

        for i in range(l, r):
            k = l + (i * 5) % (r-l)
            QSelect(k, values, index, l, r)
            self.assertPartitioned(values, index, k, l, r)

    def assert_fixed_median(self, q, l=0, r=32, W=5):
        table = Rank100(r, 1)
        values = [row['b'] for row in table]
        frames = [Frame(max(0,i-W), min(r,i+W)) for i in range(l, r)]
        quants = [0.5 for f in frames]

        expected = [int(statistics.median(F.Slice(values))) for F in frames]
        actual = q(values, quants, frames)
        self.assertEqual(expected, actual)

    def test_naive_fixed_median(self):
        self.assert_fixed_median(NaiveQuantile)

    def test_reuse_fixed_median(self):
        self.assert_fixed_median(ReuseQuantile)

    def test_replace_fixed_median(self):
        self.assert_fixed_median(ReplaceQuantile)

if __name__ == '__main__':
    unittest.main()
