"""Regime info"""

def gen_cluster_mapping(regimes):
    """Define mapping from observed regimes to smaller set of
    European clusters"""
    european_clusters = {
        1: [6, 9, 11, 19, 25, 27, 28],
        2: [4, 8, 20, 23, 26, 30],
        3: [1, 13, 14, 24],
        4: [2, 12, 15, 21],
        5: [5, 16, 17, 22],
        6: [3, 18],
        7: [7, 29],
        8: [10]
    }
    mapping = {}
    for reg in set(regimes):
        for ec in european_clusters:
            if reg in european_clusters[ec]:
                mapping[reg] = ec
    return mapping


# regimes where nowcast performance is good / bad wrt UKV
# derived from CRPS and meanerr timeseries at T+2
GOOD_REGIMES = [5, 6, 24] # [4, 5, 9, 11, 19, 22, 24]
BAD_REGIMES = [1, 8, 10] # [1, 2, 7, 10, 12, 20, 26]     

