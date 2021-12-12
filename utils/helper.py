import random
from math import exp, log
import math

def confine(num, start=0, end=100):
    if num < start:
        return start
    elif num > end:
        return end
    else:
        return num


def correlated_lognorm(corr, source, mu, sigma):
        return corr * source + \
               (1 - corr) * random.lognormvariate(log(mu), log(sigma))


def get_stat(data):
    # mean = sum(data) / len(data)
    # ema
    g = 0.8
    mean = data[0]
    for c in data[1:]:
        mean = g * c + (1 - g) * mean

    sigma = (sum(((d-mean)**2 for d in data)) / len(data)) ** 0.5
    return mean, sigma


def gaussian_pdf(x, mu, sigma):
    '''
    value of gaussian pdf, given x and mu and sigma.
    peak heights are normalized with 1
    '''
    return exp(-1 * (x - mu)**2 / 2 / sigma**2) / (sigma * math.sqrt(2 * math.pi))
