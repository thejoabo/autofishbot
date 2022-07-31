#------------------------ IMPORTS --------------------------#
from random import randint, Random
from math import erf, sqrt, exp, tau


#------------------------ CONSTANTS --------------------------#
SIGMA = 0.12289
'''
OVER constant is used to increase the user cooldown in order to reduce
the events where a cooldown alert is triggered in order to maximize
performance but still preserving the bell curve sigma.
'''
OVER = 0.5 
SEED = randint(10**6, 10**7) #maybe store this seed ?

#------------------------- CLASSES ---------------------------#
'''
See: https://github.com/thejoabo/virtualfisher-bot/discussions/12
The essential part of this class is the new() function. All the other 
functions are just for analysis and, for now, shall not be used.
In addition, I decided to reduce at max the imports for the gaussian 
number generator (and analysis stuff), therefore, I won't be using numpy
or other libraries.

Also, there is a major flaw in this method, the sleep() function is 
not precise at all (on windows) when it comes to the milliseconds needed
to assure the correct deviation (even when subtracting the request/processing
poison). The problem is that if I increase the accuracy using a custom 
sleep method the CPU usage becomes too high, and since the program basically
runs all the time sleeping (between the requests), it would be unbearable to
the user to use this autobot.

Tests on my machine: 
- Profile: https://prnt.sc/eLzgM8rp7myP
- CPU: Normal sleep (~0.01%) | 
       Sleep with perf_counter(): custom (~24.70%) | 
       Sleep with only time(): zeta (~24.70%)
The best result was using this function (custom):
def sleep(length : float) -> None:
    now = perf_counter()
    end = now + length
    while now < end:
        now = perf_counter()
'''
class Cooldown:
    def __init__(self, ucd : float) -> None:
        self.mu = ucd + OVER
        self.sigma = SIGMA
        self.variance = self.sigma ** 2.0
        self.values = []
        self.incooldown = False
        self.seed = SEED
        self.generator = Random(self.seed)
        
    def new(self, c_mu : float = None, standalone = True) -> float:
        _mu = c_mu if c_mu else self.mu
        value = self.generator.gauss(_mu, self.sigma)
        if standalone:
            self.values.append(value)
        return value
    
    def pdf(self, value) -> float:
        return exp((value - self.mu) ** 2.0 / (-2.0 * self.variance)) / sqrt(tau * self.variance)
    
    def cdf(self, n) -> float:
        return 0.5 * (1.0 + erf( (n - self.mu) / (self.sigma * sqrt(2.0) ) ))
    
    def zscore(self, n) -> float:
        return (n - self.mu) / self.sigma
    
    def calc_sigma(self, sample = []) -> float:
        sample = sample if sample != [] else self.values
        n = len(sample)
        if n > 1:
            return (sum((x-(sum(sample)/n))**2 for x in sample)/(n - 1))**0.5
        else: return 0
        
    def calc_mean(self, sample = []) -> float:
        sample = sample if sample != [] else self.values
        if len(sample) > 0:
            return sum(sample)/len(sample)
        else: return 0
        
    def calc_a_cdf(self) -> float:
        cdfs = [self.cdf(x) for x in self.values]
        cdfs = sorted(cdfs)
        n = len(cdfs)
        i = n // 2 
        if n % 2 == 1: 
            return cdfs[i]
        else: 
            return (cdfs[i - 1] + cdfs[i]) / 2
        
    def calc_a_zscore(self) -> float:
        zscores = [self.zscore(x) for x in self.values]
        zscores = sorted(zscores)
        n = len(zscores)
        i = n // 2 
        if n % 2 == 1: 
            return zscores[i]
        else: 
            return (zscores[i - 1] + zscores[i]) / 2
        
    def calc_a_pdf(self) -> float:
        zscores = [self.pdf(x) for x in self.values]
        zscores = sorted(zscores)
        n = len(zscores)
        i = n // 2 
        if n % 2 == 1: 
            return zscores[i]
        else: 
            return (zscores[i - 1] + zscores[i]) / 2
    
    def evaluate(self) -> None:
        print(f'{len(self.values)} values:')
        print(f'sigma: {self.calc_sigma(), self.sigma}')
        print(f'average cdf: {self.calc_a_cdf()}')
        print(f'average pdf: {self.calc_a_pdf()}')
        print(f'average zscore: {self.calc_a_zscore()}')
        print(f'mean: {self.calc_mean(), self.mu}')
        return