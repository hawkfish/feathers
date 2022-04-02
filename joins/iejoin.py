# encoding=utf8

import copy
import operator
import random
import sys
import unittest

from bitarray import bitarray

ops = {
    operator.lt: "<",
    operator.le: "≤",
    operator.gt: ">",
    operator.ge: "≥",
}

# Bloom filter equivalent (64 bit blocks internally)
one_bit = bitarray(1)
one_bit.setall(1)

# Multi-field sorting
# From https://stackoverflow.com/questions/55866762/how-to-sort-a-list-of-strings-in-reverse-order-without-using-reverse-true-parame/55866810#55866810
def order_by(sequence, *sort_order):
    """Sort a sequence by multiple criteria.

    Accepts a sequence and 0 or more (key, reverse) tuples, where
    the key is a callable used to extract the value to sort on
    from the input sequence, and reverse is a boolean dictating if
    this value is sorted in ascending or descending order.

    """
    from functools import reduce
    return reduce(
        lambda s, order: sorted(s, key=order[0], reverse=order[1]),
        reversed(sort_order),
        sequence
    )

def FormatPredicate(pred):
    return f"{pred['lhs']} {ops[pred['op']]} {pred['rhs']}"

def FormatPredicates(preds):
    return ' AND '.join([FormatPredicate(pred) for pred in preds])

def LoopJoin(left, right, preds):
    result = []

    for l in left:
        for r in right:
            matching = True
            for p in preds:
                if not p['op'](l[p['lhs']], r[p['rhs']]):
                    matching = False
                    break
            if matching:
                result.append((l, r, ))

    return result

def ExtractColumn(table, c):
    return [row[c] for row in table]

def ArrayOf(T, cols, identifier=lambda rid: rid):
    # Project the predicate columns and a row id as tuples: (rid, X, ...)
    L = []
    for rid, row in enumerate(T):
        t = [identifier(rid),]
        t.extend([row[C] for C in cols])
        L.append(t)
    return L

def Mark(L):
    #   Add a marked column that will become P
    for p, l in enumerate(L):
        l.append(p)
    return L

def OffsetArray(L, Lr, op):
    # The offset is the first position where the op holds
    O = [len(Lr)] * len(L)

    l_ = 0
    for l, value in enumerate(L):
        while l_ < len(Lr):
            if op(value, Lr[l_]):
                O[l] = l_
                break
            l_ += 1

    return O

east = (
    {'row': 'r1', 'id': 100, 'dur': 140, 'rev': 12, 'cores': 2},
    {'row': 'r2', 'id': 101, 'dur': 100, 'rev': 12, 'cores': 8},
    {'row': 'r3', 'id': 103, 'dur':  90, 'rev':  5, 'cores': 4},
)

west = (
    {'row': 's1', 't_id': 404, 'time': 100, 'cost':  6, 'cores': 4},
    {'row': 's2', 't_id': 498, 'time': 140, 'cost': 11, 'cores': 2},
    {'row': 's3', 't_id': 676, 'time':  80, 'cost': 10, 'cores': 1},
    {'row': 's4', 't_id': 742, 'time':  90, 'cost':  5, 'cores': 4},
)

def IESingleSelf(T, pred, trace=0):
    op1 = pred['op']
    X = pred['lhs']

    n = len(T)
    if trace: print('IESingleSelf:', n, FormatPredicate(pred))

    # 1. let L1 be the array of X in T
    L = ArrayOf(T, (X,))

    # 3. if (op1 ∈ {>, ≥}) sort L1  in descending order
    # 4. else if (op1 ∈ {<, ≤}) sort L1 in ascending order
    descending1 = (op1 in (operator.gt, operator.ge,))
    L.sort(key=lambda r: (r[1], r[0],), reverse=descending1)
    L1 = ExtractColumn(L, 1)
    if trace: print("L1:", L1, file=sys.stderr)

    Li = ExtractColumn(L, 0)

    # 12. initialize join result as an empty list for tuple pairs
    join_result = []

    # 15. for(i←1 to m) do
    j = 0
    for i in range(m):
        while j < n and not op1(L1[i], L1[j]): j += 1
        for k in range(j,n):
            # 22. add tuples w.r.t. (L1[i],L1[k]) to join result
            join_result.append((T[Li[i]], T[Li[k]],))

    # 23. return join result
    return join_result

def IESingle(T, Tr, pred, trace=0):
    op1 = pred['op']
    X = pred['lhs']
    Xr = pred['rhs']

    m = len(T)
    n = len(Tr)

    if trace: print("IESingle:", m, n, FormatPredicate(pred))

    # 1. let L1 be the array of X in T
    L = ArrayOf(T, (X,))

    # 2. let Lr1 be the array of Xr in Tr
    Lr = ArrayOf(Tr, (Xr,))

    # 3. if (op1 ∈ {>, ≥}) sort L1 , Lr1 in descending order
    # 4. else if (op1 ∈ {<, ≤}) sort L1 , Lr1 in ascending order
    descending1 = (op1 in (operator.gt, operator.ge,))
    L.sort(key=lambda r: (r[1], r[0],), reverse=descending1)
    L1 = ExtractColumn(L, 1)
    if trace: print("L1:", L1, file=sys.stderr)

    Lr.sort(key=lambda r: (r[1], r[0],), reverse=descending1)
    Lr1 = ExtractColumn(Lr, 1)
    if trace: print("L1':", Lr1, file=sys.stderr)

    Li = ExtractColumn(L, 0)
    Lk = ExtractColumn(Lr, 0)

    # 12. initialize join result as an empty list for tuple pairs
    join_result = []

    # 15. for(i←1 to m) do
    j = 0
    for i in range(m):
        while j < n and not op1(L1[i], Lr1[j]): j += 1
        for k in range(j,n):
            # 22. add tuples w.r.t. (L1[i],Lr1[k]) to join result
            join_result.append((T[Li[i]], Tr[Lk[k]],))

    # 23. return join result
    return join_result

def IESelfJoin(T, preds, trace=0):
    # input : query Q with 2 join predicates t1.X op1 t2.X and t1.Y op2 t2.Y , table T of size n
    # output: a list of tuple pairs (ti , tj )
    op1 = preds[0]['op']
    X = preds[0]['lhs']

    op2 = preds[1]['op']
    Y = preds[1]['lhs']

    n = len(T)

    if trace: print("IESelfJoin:", n, FormatPredicates(preds))

    # 1. let L1 (resp. L2) be the array of column X (resp. Y )
    L = ArrayOf(T, (X, Y,))

    # 2. if (op1 ∈ {>, ≥}) sort L1 in descending order
    # 3.  else if (op1 ∈ {<, ≤}) sort L1 in ascending order
    descending1 = (op1 in (operator.gt, operator.ge,))
    L.sort(key=lambda r: (r[1], r[0],), reverse=descending1)
    L1 = ExtractColumn(L, 1)
    if trace: print("L1:", L1, file=sys.stderr)
    L = Mark(L)
    Li = ExtractColumn(L, 0)

    # 4. if (op2 ∈ {>, ≥}) sort L2 in ascending order
    # 5.  else if (op2 ∈ {<, ≤}) sort L2 in descending order
    descending2 = (op2 in (operator.lt, operator.le,))
    L.sort(key=lambda r: (r[2], r[0],), reverse=descending2)
    L2 = ExtractColumn(L, 2)
    if trace: print("L2:", L2, file=sys.stderr)
    if trace: print("Li:", Li, file=sys.stderr)

    # 6. compute the permutation array P of L2 w.r.t. L1
    P = ExtractColumn(L, 3)
    if trace: print("P:", P, file=sys.stderr)

    # 7. initialize bit-array B (|B| = n), and set all bits to 0
    B = bitarray(n)
    B.setall(False)

    # 8. initialize join result as an empty list for tuple pairs
    join_result = []

    # 11. for(i←1 to n) do
    off2 = 0
    for i in range(n):
        # 16. B[pos] ← 1
        # This has to come first or we will never join the first tuple.
        while off2 < n:
            if not op2(L2[i], L2[off2]): break
            B[P[off2]] = True
            off2 += 1
        if trace: print("B:", i, B, file=sys.stderr)

        # 12. pos ← P[i]
        pos = P[i]

        # 9.  if (op1 ∈ {≤,≥} and op2 ∈ {≤,≥}) eqOff = 0
        # 10. else eqOff = 1
        # No, because there could be more than one equal value.
        # Scan the neighborhood instead
        off1 = pos
        while op1(L1[off1], L1[pos]) and off1 > 0: off1 -= 1
        while off1 < n and not op1(L1[pos], L1[off1]): off1 += 1

        # 13. for (j ← pos+eqOff to n) do
        while True:
            # 14. if B[j] = 1 then
            j = B.find(one_bit, off1)
            if j < 0: break

            # 15. add tuples w.r.t. (L1[j], L1[i]) to join result
            if trace: print("j,i':", j, i)
            join_result.append((T[Li[pos]], T[Li[j]],))

            off1 = j + 1

    # 17. return join result
    return join_result

def IEJoin(T, Tr, preds, trace=0):
    # input : query Q with 2 join predicates t1.X op1 t2.Xr and t1.Y op2 t2.Yr, tables T, Tr of sizes m and n resp.
    # output: a list of tuple pairs (ti , tj)
    op1 = preds[0]['op']
    X = preds[0]['lhs']
    Xr = preds[0]['rhs']

    op2 = preds[1]['op']
    Y = preds[1]['lhs']
    Yr = preds[1]['rhs']

    m = len(T)
    n = len(Tr)

    if trace: print("IEJoin:", m, n, FormatPredicates(preds))

    # 1. let L1 (resp. L2) be the array of X (resp. Y) in T
    L = ArrayOf(T, (X, Y,))

    # 2. let Lr1 (resp. L_2) be the array of Xr (resp. Yr) in Tr
    Lr = ArrayOf(Tr, (Xr, Yr,))

    # 3. if (op1 ∈ {>, ≥}) sort L1 , Lr1 in descending order
    # 4. else if (op1 ∈ {<, ≤}) sort L1 , Lr1 in ascending order
    descending1 = (op1 in (operator.gt, operator.ge,))
    L.sort(key=lambda r: (r[1], r[0],), reverse=descending1)
    L1 = ExtractColumn(L, 1)
    if trace: print("L1:", L1, file=sys.stderr)
    L = Mark(L)

    Lr.sort(key=lambda r: (r[1], r[0],), reverse=descending1)
    Lr1 = ExtractColumn(Lr, 1)
    if trace: print("L1':", Lr1, file=sys.stderr)
    Lr = Mark(Lr)

    # 5. if (op2 ∈ {>, ≥}) sort L2 , L_2 in ascending order
    # 6. else if (op2 ∈ {<, ≤}) sort L2 , L_2 in descending order
    descending2 = (op2 in (operator.lt, operator.le,))
    L.sort(key=lambda r: (r[2], r[0],), reverse=descending2)
    L2 = ExtractColumn(L, 2)
    if trace: print("L2:", L2, file=sys.stderr)

    Li = ExtractColumn(L, 0)
    Lk = ExtractColumn(Lr, 0)

    Lr.sort(key=lambda r: (r[2], r[0],), reverse=descending2)
    L_2 = ExtractColumn(Lr, 2)
    if trace: print("L2':", L_2, file=sys.stderr)

    # 7. compute the permutation array P of L2 w.r.t. L1
    P = ExtractColumn(L, 3)
    if trace: print("P:", P, file=sys.stderr)

    # 8. compute the permutation array Pr of L_2 w.r.t. Lr1
    Pr = ExtractColumn(Lr, 3)
    if trace: print("P':", Pr, file=sys.stderr)

    # 9. compute the offset array O1 of L1 w.r.t. Lr1
    O1 = OffsetArray(L1, Lr1, op1)
    if trace: print("O1:", O1, file=sys.stderr)

    # 10. compute the offset array O2 of L2 w.r.t. L_2
    # Not needed - just scan ahead

    # 11. initialize bit-array Br (|Br| = n), and set all bits to 0
    Br = bitarray(n)
    Br.setall(False)

    # 12. initialize join result as an empty list for tuple pairs
    join_result = []

    # 13. if (op1 ∈ {≤,≥} and op2 ∈ {≤,≥}) eqOff = 0
    # else eqOff = 1
    # No, instead offset array contains first value in L' that satisfies the predicate

    # 15. for(i←1 to m) do
    off2 = 0
    for i in range(m):
        # 16. off2 ← O2[i]
        # 17. for j ← O2[i-1] to O2[i] do
        while off2 < n:
            if not op2(L2[i], L_2[off2]): break
            # 18. Br[Pr[j]] ← 1
            Br[Pr[off2]] = True
            off2 += 1
        if trace: print("B':", i, Br, file=sys.stderr)

        # 12. pos ← P[i]
        pos = P[i]

        # 19. off1 ← O1[P[i]]
        off1 = O1[pos]

        # 20. for (k ← off1 + eqOff to n) do
        while True:
            # 21. if Br[k] = 1 then
            k = Br.find(one_bit, off1)
            if k < 0: break

            # 22. add tuples w.r.t. (L2[i],Lr1[k]) to join result
            join_result.append((T[Li[i]], Tr[Lk[k]],))

            off1 = k + 1

    # 23. return join result
    return join_result

def lower_bound(L1, pos, op1, trace=0):
    lo = 0
    hi = len(L1)

    if op1(L1[pos], L1[pos]):
        hi = pos
    else:
        lo = pos + 1

    while lo < hi:
        off1 = lo + (hi - lo) // 2
        if op1(L1[pos], L1[off1]):
            hi = off1
        else:
            lo = off1 + 1

    return lo

def SearchL1(L1, pos, op1, off1, trace=0):
    # Perform an exponential search in the appropriate direction
    step = 1
    n = len(L1)

    hi = lo = pos
    # Can we reuse the previous value?
    if off1 < n:
        if op1(L1[pos], L1[off1]):
            hi = off1
        else:
            lo = off1

    if op1 in (operator.ge, operator.le,):
        # Scan left for loose inequality
        lo -= min(step, lo)
        step *= 2
        while lo > 0 and op1(L1[pos], L1[lo]):
            hi = lo
            lo -= min(step, lo)
            step *= 2
    else:
        # Scan right for strict inequality
        hi += min(step, n - hi)
        step *= 2
        while hi < n and not op1(L1[pos], L1[hi]):
            lo = hi
            hi += min(step, n - hi)
            step *= 2

    # Binary search the target area
    while lo < hi:
        off1 = lo + (hi - lo) // 2
        if op1(L1[pos], L1[off1]):
            hi = off1
        else:
            lo = off1 + 1

    return lo

def IEJoinUnion(T, Tr, preds, trace=0):
    # input : query Q with 2 join predicates t1.X op1 t2.Xr and t1.Y op2 t2.Yr, tables T, T' of sizes m and n resp.
    # output: a list of tuple pairs (ti , tj)
    op1 = preds[0]['op']
    X = preds[0]['lhs']
    Xr = preds[0]['rhs']

    op2 = preds[1]['op']
    Y = preds[1]['lhs']
    Yr = preds[1]['rhs']

    m = len(T)
    n = len(Tr)

    if trace: print("IEJoinUnion:", m, n, FormatPredicates(preds))

    # 1. let L1 (resp. L2) be the array of column X (resp. Y )
    L = ArrayOf(T, (X, Y,), lambda rid: rid+1)
    L.extend(ArrayOf(Tr, (Xr, Yr,), lambda rid: -(rid + 1)))
    n += m

    # 2. if (op1 ∈ {>, ≥}) sort L1 in descending order
    # 3. else if (op1 ∈ {<, ≤}) sort L1 in ascending order
    descending1 = (op1 in (operator.gt, operator.ge,))
    descending2 = (op2 in (operator.lt, operator.le,))
    order = (
        (lambda r: r[1], descending1),
        #(lambda r: r[2], descending2),
        #(lambda r: r[0], True),
    )
    L = order_by(L, *order)
    L1 = ExtractColumn(L, 1)
    if trace: print(f"L1 ({X}):", L1, file=sys.stderr)

    Li = ExtractColumn(L, 0)
    if trace: print("Li:", Li, file=sys.stderr)

    # 4. if (op2 ∈ {>, ≥}) sort L2 in ascending order
    # 5. else if (op2 ∈ {<, ≤}) sort L2 in descending order
    order = (
        (lambda r: r[2], descending2),
        #(lambda r: r[1], descending1),
        #(lambda r: r[0], True),
    )
    L = Mark(L)
    L = order_by(L, *order)
    L2 = ExtractColumn(L, 2)
    if trace: print(f"L2 ({Y}):", L2, file=sys.stderr)

    # 6. compute the permutation array P of L2 w.r.t. L1
    P = ExtractColumn(L, 3)
    if trace: print("P:", P, file=sys.stderr)

    # 7. initialize bit-array B (|B| = n), and set all bits to 0
    B = bitarray(n)
    B.setall(False)

    # 8. initialize join result as an empty list for tuple pairs
    join_result = []

    # 11. for(i←1 to n) do
    off1 = 0
    off2 = 0
    for i in range(n):
        # 12. pos ← P[i]
        pos = P[i]
        rid = Li[pos]
        if rid < 0: continue

        # 16. B[pos] ← 1
        while off2 < n:
            if (trace): print("op2:", i, off2, L2[i], L2[off2], file=sys.stderr)
            if not op2(L2[i], L2[off2]): break

            # Filter out tuples with the same sign (they come from the same table)
            p2 = P[off2]
            if Li[p2] < 0:
                B[p2] = True
            off2 += 1
        if trace: print("B:", i, off2, B, file=sys.stderr)

        # 9.  if (op1 ∈ {≤,≥} and op2 ∈ {≤,≥}) eqOff = 0
        # 10. else eqOff = 1
        # No, because there could be more than one equal value.
        # Find the leftmost off1 where L1[pos] op1 L1[off1..n]
        # These are the rows that satisfy the op1 condition
        # and that is where we should start scanning B from
        off1 = SearchL1(L1, pos, op1, off1, trace)
        if off1 >= n: continue
        if trace: print("op1:", pos, off1, L1[pos], L1[off1], op1(L1[pos], L1[off1]), file=sys.stderr)

        # 13. for (j ← pos+eqOff to n) do
        j = off1
        while True:
            # 14. if B[j] = 1 then
            j = B.find(one_bit, j)
            if j < 0: break

            rid_= Li[j]

            # 15. add tuples w.r.t. (L1[j], L1[i]) to join result
            if trace: print("rid:", j, rid, rid_, file=sys.stderr)
            join_result.append((T[rid-1], Tr[-rid_-1],))

            j = j + 1

    # 17. return join result
    return join_result

class TestIEJoin(unittest.TestCase):

    def makePairs(self, pairs):
        return [(l['row'], r['row']) for (l,r) in pairs]

    def expectedPairs(self, left, right, preds, trace=0):
        expected = self.makePairs(LoopJoin(left, right, preds))
        if trace: print("Expected:", expected)
        return expected

    def assertJoinPairs(self, expected, actual, msg=None):
        self.assertEqual(set(expected), set(actual), msg)

    def assertIEJoin(self, left, right, preds, trace=0):
        expected = self.expectedPairs(left, right, preds, trace)

        actual = self.makePairs(IEJoin(left, right, preds, trace))
        if trace: print("Actual (IEJoin):", actual)
        self.assertJoinPairs(expected, actual, FormatPredicates(preds))

        actual = self.makePairs(IEJoinUnion(left, right, preds, trace))
        if trace: print("Actual (IEJoinUnion):", actual)
        self.assertJoinPairs(expected, actual, FormatPredicates(preds))

    def assertIESingle(self, left, right, preds, trace=0):
        expected = self.expectedPairs(left, right, preds, trace)

        actual = self.makePairs(IESingle(left, right, preds[0], trace))
        if trace: print("Actual (IESingle):", actual)
        self.assertJoinPairs(expected, actual, FormatPredicates(preds))

    def assertIESelfJoin(self, table, preds, trace=0):
        expected = self.expectedPairs(table, table, preds, trace)

        actual = self.makePairs(IESelfJoin(table, preds, trace))
        if trace: print("Actual (IESelfJoin):", actual)
        self.assertJoinPairs(expected, actual, FormatPredicates(preds))

    def assertIEJoinUnion(self, left, right, preds, trace=0):
        expected = self.expectedPairs(left, right, preds, trace)

        actual = self.makePairs(IEJoinUnion(left, right, preds, trace))
        if trace: print("Actual (IEJoinUnion):", actual)
        self.assertJoinPairs(expected, actual, FormatPredicates(preds))

    def assertEastWest(self, op1, op2, trace=0):
        preds = (
            {'op': op1, 'lhs': 'dur', 'rhs': 'time'},
            {'op': op2, 'lhs': 'rev', 'rhs': 'cost'},
        )
        self.assertIEJoin(east, west, preds, trace)

    def assertWest(self, op1, op2, trace=0):
        preds = (
            {'op': op1, 'lhs': 'time', 'rhs': 'time'},
            {'op': op2, 'lhs': 'cost', 'rhs': 'cost'},
        )
        self.assertIESelfJoin(west, preds, trace)

        s = list(west)
        s.sort(key=lambda r: r[preds[0]['lhs']], reverse=True)
        self.assertIEJoin(s, s, preds, trace)

    def test_example_1(self):
        # Qs : SELECT s1.t id, s2.t id FROM west s1, west s2
        # WHERE s1.time > s2.time
        # [('s1', 's3'), ('s1', 's4'), ('s2', 's1'), ('s2', 's3'), ('s2', 's4'), ('s4', 's3')]
        preds = ({'op': operator.gt, 'lhs': 'time', 'rhs': 'time'}, )
        self.assertIESingle(west, west, preds)

    def test_example_2(self):
        # Qp : SELECT s1.t id, s2.t id FROM west s1, west s2
        # WHERE s1.time > s2.time AND s1.cost < s2.cost
        # [('s1', 's3'), ('s4', 's3')]
        self.assertWest(operator.gt, operator.lt)

    def test_west(self):
        for op1 in ops:
            for op2 in ops:
                self.assertWest(op1, op2)

    def test_example_3(self):
        # Qt : SELECT east.id, west.t id FROM east, west
        # WHERE east.dur < west.time AND east.rev > west.cost;
        # [('r2', 's2')]
        self.assertEastWest(operator.lt, operator.gt)

    def test_east_west(self):
        for op1 in ops:
            for op2 in ops:
                self.assertEastWest(op1, op2)

    def test_random(self):
        for repeat in range(100):
            # Left table
            m = random.randint(3,20)
            T = []
            id_ = 100
            for r in range(m):
                row = {'row': f"r{r+1}", 'id': id_}
                row['dur'] = random.randint(50, 150)
                row['rev'] = random.randint(3, 15)
                row['cores'] = 2 ** random.randint(0,5)
                T.append(row)
                id_ += random.randint(1,3)

            # Right table
            n = random.randint(3, 20)
            Tr = []
            id_ = 400
            for r in range(n):
                row = {'row': f"s{r+1}", 't_id': id_}
                row['time'] = random.randint(50, 150)
                row['cost'] = random.randint(3, 15)
                row['cores'] = 2 ** random.randint(0,5)
                Tr.append(row)
                id_ += random.randint(50, 150)

            for op1 in ops:
                for op2 in ops:
                    preds = (
                        {'op': op1, 'lhs': 'dur', 'rhs': 'time'},
                        {'op': op2, 'lhs': 'rev', 'rhs': 'cost'},
                    )
                    self.assertIEJoin(T, Tr, preds)

    def test_debug(self):
        self.assertWest(operator.gt, operator.lt)

if __name__ == '__main__':
    unittest.main()
