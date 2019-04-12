"""
SquashedOrder module
implements sequence numbers for sequences

Michael Sube (@msube) 2018
"""
import math

#   choose(n-1,k) = choose(n,k) / n * (n-k)
#   choose(n-1,k-1) = choose(n,k) / n * k
#   choose(n, k) = choose(n, a) * choose(n-a, k-a)
#   n! / (n-k)! / k! = n! / (n-a)! / a! * (n-a)! / (n-a-k+a)! / (k-a) !
#                    = n!          / a!          / (n-k)!     / (k-a) !

def choose(n, k):
    """ Computes the binomial coefficient."""
    return 0 if n < k else math.factorial(n) // math.factorial(n - k) // math.factorial(k)

max26 = choose(26, 13)
max39 = choose(39, 13) * max26

def index(seq):
    """Computes the sequence number for a given sequence.
    seq must be in ascending order.
    """
    return sum(choose(x, i) for i, x in enumerate(seq, start=1))

def index52_13(sets):
    """Computes the sequence number for a sequence 0..51 splitted into 4 groups of 13 elements ."""
    assert len(sets) in [3,4]
    assert all(len(set) == 13 for set in sets)
    assert all(0 <= min(set) and max(set) < 52 for set in sets)
    A = sorted(sets[0]) # 0..51
    B = sorted(sets[1]) # 0..51
    C = sorted(sets[2]) # 0..51
    a, b, c = 0, 0, 0
    for element in range(52):
        if a < 13 and element == A[a]:
            a += 1
        elif b < 13 and element == B[b]:
            B[b] -= a
            b += 1
        elif c < 13 and element == C[c]:
            C[c] -= a + b
            c += 1
    assert min(A) >= 0 and min(B) >= 0 and min(C) >= 0
    assert max(A) < 52 and max(B) < 39 and max(C) < 26
    return index(A) * max39 + index(B) * max26 + index(C)

def seq(index, n, l):
    """Computes a sequence of length l from a given sequence number."""
    set = []
    c = choose(n - 1, l)
    for n in range(n - 1, 0, -1):
        if index < c: # n is included
            c = (c * (n - l)) // n
            continue
        # n is not included
        set.append(n)
        index -= c
        c = (c * l) // n
        l -= 1
    set = [e for e in range(l)] + sorted(set) # add missing numbers
    return sorted(set)

def seq52_13(index):
    """Computes a sequence 0..51 splitted into 4 groups with 13 elements from a given sequence number."""
    i52, i39 = divmod(index, max39)
    i39, i26 = divmod(i39, max26)
    A = seq(i52, 52, 13)
    B = seq(i39, 39, 13)
    C = seq(i26, 26, 13)
    D = []
    a, b, c = 0, 0, 0
    for element in range(52):
        if a < 13 and A[a] == element:
            a += 1
        elif b < 13 and B[b] == (element - a):
            B[b] = element
            b += 1
        elif c < 13 and C[c] == (element - a - b):
            C[c] = element
            c += 1
        else:
            D.append(element)
    sets = [A, B, C, D]
    assert all(len(set) == 13 for set in sets)
    assert all(0 <= min(set) and max(set) < 52 for set in sets)
    return sets

# ============================================================================
if __name__ == '__main__':
    def test(l, n=None):
        n = n if n else max(l) + 1
        l = sorted(l)
        i = index(l)
        s = seq(i, n, len(l))
        print(F"{i :20}  {l}")
        print(F"{'':20}  {s}")
        assert l == s
        print()

    def test52(g):
        for s in g: print(F"{s}")
        i = index52_13(g)
        print(F"{i  :30}")
        gi = seq52_13(i)
        assert g == gi
        for s in gi: print(F"{s}")
        print()

    import random

    def deal():
        s = random.sample(range(52), 52)
        return [sorted(s[i:i+13]) for i in range(0,52,13)]

    for i in range(20):
        test52(deal())

    test([c for c in range(12, 12-13, -1)])
    test([46] + [c for c in range(12, 12-13, -1)][1:13])
    test([47] + [c for c in range(12, 12-13, -1)][1:13])
    test([48] + [c for c in range(12, 12-13, -1)][1:13])
    test([49] + [c for c in range(12, 12-13, -1)][1:13])
    test([50] + [c for c in range(12, 12-13, -1)][1:13])
    test([51] + [c for c in range(12, 12-13, -1)][1:13])
    test([51, 50] + [c for c in range(12, 12-13, -1)][2:13])
    test([51, 50, 49] + [c for c in range(12, 12-13, -1)][3:13])
    test([c for c in range(51, 51-13, -1)])

    test([0, 1, 5])
    test([0, 2, 5])
    test([0, 3, 5])
    test([1, 3, 5])
    test([2, 3, 5])
    test([0, 1, 2, 3, 4, 5, 6])
    test([1, 2, 3, 4, 5, 6])
    test([0, 10, 15, 21, 23, 26, 27, 31, 32, 39, 41, 43, 49])
    test([5, 8, 9, 10, 11, 15, 18, 21, 28, 29, 31, 32, 36])
    test([1, 6, 9, 12, 14, 16, 18, 22, 28, 29, 31, 36, 37], n=52)
    test([x for x in range(51, 51-13, -1)])
