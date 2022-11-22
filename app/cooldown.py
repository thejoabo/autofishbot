#------------------------ IMPORTS --------------------------#
from __future__ import annotations

from . import *
from random import randint, Random, uniform
from statistics import mean, stdev, variance

#from scipy.stats import norm


#------------------------ CONSTANTS --------------------------#
SIGMA = 0.12289
'''
Do NOT change Sigma value
See: https://github.com/thejoabo/virtualfisher-bot/discussions/12
'''
MARGIN = uniform(0.1, 0.35)
'''
The MARGIN constant is used to increase the overall cooldown in order 
to reduce the values less than user's cooldown, maximizing performance 
and preserving a legitimate gauss function. I strongly recommend not to
change this value.
'''


#------------------------- CLASSES ---------------------------#
@dataclass(slots=True)
class CooldownManager:
    '''
    Simplified cooldown manager.
    Disclaimer: The value generator itself is valid, but the sleep() function is not precise at all (on windows) 
    when it comes to the milliseconds needed to assure the correct deviation (even when subtracting 
    the request/processing poison). The problem is that if I increase the accuracy using
    a custom sleep method the CPU usage becomes too high, and since the program basically
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
    user_cooldown: float
    mu: float = None
    sigma: float = SIGMA
    margin: float = MARGIN
    generator: Random = field(init=False, repr=False)
    seed: int = randint(10**5, 10**7)
    dataset: list[int] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        self.mu = self.margin + self.user_cooldown
        self.generator = Random(self.seed)
    
    @property
    def last(self) -> float:
        '''Returns the last generated (by the new() function) cooldown value.'''
        try:
            value = self.dataset[-1]
            return value
        except IndexError:
            return None

    def analysis(self) -> tuple:
        '''Returns the dataset sample's stdev (+ diff), mean (+ diff) and variance'''
        if len(self.dataset) > 2:
            sample_stdev = stdev(self.dataset)
            sample_mean = mean(self.dataset)
            return (
                (sample_stdev, self.sigma - sample_stdev), 
                (sample_mean, self.mu - sample_mean), 
                variance(self.dataset)
            )
            
    # def pvalue(self, value: float) -> float:
    #     '''Returns value p-value (two-tailed test).'''
    #     if has_scipy:
    #         return norm.sf(abs(((value - self.mu) / self.sigma))) * 2
    #         #print(f'[!] {value} is ~{pvalue*100}% likely to happen in this distribution. Mean diff: ~{round(value - cooldown.mu, 4)}')
    #     else:
    #         return None

    def new(self) -> float:
        '''Standard value generator, uses default mu and sigma.'''
        value = self.generator.gauss(self.mu, self.sigma)
        self.dataset.append(value)
        return value
    
    def custom(self, mu: float, sigma: float = None) -> float:
        '''Generates new custom cooldown value.'''
        if not sigma:
            sigma = uniform(1, 3)
        return self.generator.gauss(mu, sigma)

# --------- INIT ---------#
if __name__ == "__main__":
    cooldown = CooldownManager(2.7)
    print(cooldown)
    for _ in range(10**3):
        cooldown.new()
    print(cooldown.analysis())
    