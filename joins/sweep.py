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

# ALGORITHM 2: Forward Scan based Plane Sweep (FS)
def FS(R, S, preds):
    # Input: collections of intervals R and S
    # Output: set J of all intersecting interval pairs (r, s) ∈ R × S
    op1 = preds[0]['op']
    r_start = preds[0]['lhs']
    s_end = preds[0]['rhs']

    op2 = preds[1]['op']
    r_end = preds[1]['lhs']
    s_start = preds[1]['rhs']

    # 1. J←∅;
    J = []

    # 2. sort R and S by start endpoint;
    R = sorted(R, key=lambda x: x[r_start])
    S = sorted(S, key=lambda x: x[s_start])

    # 3. r ← first interval in R;
    r = 0

    # 4. s ← first interval in S;
    s = 0

    # 5. while R and S not depleted do
    while r < len(R) and s < len(S):
        # 6. if r.start < s.start then
        if R[r].start < S[s].start:
            # 7. s′ ← s;
            s1 = s
            # 8. while s′ ≠ null and r.end ≥ s′.start do
            while s1 < len(S) and op2(R[r][r_end], S[s1][s_start]):
                # 9. J ← J U {(r,s′)};          ◃ add result
                J.append((R[r], S[s1],))
                # 10. s′ ← next interval in S;  ◃ scan forward
                s1 += 1
            # 11. r ← next interval in R;
            r += 1
        # 12. else
        else:
            # 13. r ←r;
            r1 = r
            # 14. while r′ ≠ null and s.end ≥ r′.start do
            while r1 < len(R) and op1(S[s][s_end] >= R[r1][r_start]):
                # 15. J ← J U {(r′,s)};         ◃ add result
                J.append((R[r1], S[s],))
                # 16. r′ ← next interval in R;  ◃ scan forward
                r1 += 1
            # 17. s ← next interval in S;
            s += 1

    # 18. return J
    return J

if __name__ == '__main__':
    unittest.main()
