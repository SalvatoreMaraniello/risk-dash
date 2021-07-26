"""Tools for combact simulation.

A risk combact is defined as a roll of a dice between an attacking and a defening side. This
module contains tools to:

1. simulate a combact (possibly using precomputed probability distributions)

2. compute statistics of a combact

3. update precomputed statistics
"""

import numpy as np
import itertools
import json

import risk.conf


a_wins_outcomes = (0, 1, 2, 3)
"""Possible outcomes of a combact. This is defines the number of units lost by the defending side.
"""


def _check_dice_in_combat( n_dice: int):
    """Check number of dice in a combact is between 1 and 3. Raise `ValueError` if not.
    """

    if n_dice<1 and n_dice>3:
        raise ValueError(
            f"Number of dice rolled must be between 1 and 3 (included). {n_dice} dice were rolled!"
            )


def roll_and_sort(n_dice: int, n_repeats: int = 1) -> np.array:
    """Roll ans sort (in descending order) a set of (at most 3) dice `n_repeats` times.  

    Args:
        n_dice (int): number of dice to roll. This is a number between 1 and 3. 
        n_repeats (int, optional): number of times the simulation is repeated. Defaults to 1.

    Returns:
        D (np.array): array of shape `(n_repeats, n_dice)` whose i-th row represents the outcome of
            the i-th repetition.
    """

    _check_dice_in_combat(n_dice)

    Outcomes = np.random.choice( (1, 2, 3, 4, 5, 6), (n_repeats, n_dice) )
    return np.sort(Outcomes)[:,::-1]
    

def simulate_combact( n_attack: int, n_defend: int, n_repeats: int = 1):
    """Simulate a risk combact between `n_attack` attacking units and `n_defend` defening units. 
    The function simulates a roll of dice, and returns the amount of units loss by the defening 
    side - number of units destroyed by the attacking side. The simulation can be repeated multiple
    times.

    Args:
        n_attack (int): number of dices used during the attack. This is a number between 1 and 3. 
        n_defend (int): number of dices on the defending side.  This is a number between 1 and 3.
        n_repeats (int, optional): number of times the simulation is repeated. Defaults to 1.
    
    Returns:
        (np.array): array of integers showing, for each repetition, the amount of units destroyed by
            the attacking side.
    """

    # define comparison size
    n = min( n_attack, n_defend)
    
    # Simulate dice roll
    A = roll_and_sort( n_attack, n_repeats)[:,:n]
    D = roll_and_sort( n_defend, n_repeats)[:,:n]
    
    # Compare and count
    a_wins = (A>D).sum( axis=1)
    return a_wins


class Combact():
    """Class allowing simulation risk combacts and compute their statistics.

    Attributes:
        n_repeats (int): number of times the simulation is repeated.
        _path_to_stats (str): Path to precomputed stats data.
        a_wins_outcomes(tuple): possible outcomes for attacking side (number of units destroyed)
        A_wins_count (np.array): Array of integers with shape `(3,3,4)` whose `(ii,jj,kk)` element 
            contains the number of times the defended lost kk units when attacked by ii units and 
            defending with jj units.
        A_wins_prob (np.array): Similar to `A_wins_count` but storing probabilities.
        A_wins_ci (np.array): Similar to `A_wins_count` but storing half-size confidence interval,
            as estimated using the normal approximation.
    """

    def __init__( self, path_to_stats: str = None):
        """Initialise class.

        Args:
            path_to_stats (str, optional): [description]. Defaults to `None` sets path to `risk.conf.path_data_combact`.
        """

        if not path_to_stats:
            path_to_stats = risk.conf.path_data_combact

        self._path_to_stats = path_to_stats
        self.a_wins_outcomes = a_wins_outcomes
        n_outcomes = len(a_wins_outcomes)

        self.n_repeats = 0
        self.A_wins_count = np.zeros( (3,3,n_outcomes), dtype=int) 
        self.A_wins_prob = np.zeros( (3,3,n_outcomes))
        self.A_wins_ci = np.zeros( (3,3,n_outcomes))   

        # read stats by default
        self.load_stats()
        self.verify_stats()


    def get_stats( self, n_repeats: int, batch_size: int = None, print_progress: bool = True, reset: bool = False):
        """Run a combact simulation `n_repeats` times, and update statistics in the `A_wins_*` 
        attributes. Note that the new simulations will add to those already run.

        Args:
            n_repeats (int): number of times the simulation is repeated.
            print_progress (bool): if True, print progress of calculation. Defaults to True.
        """

        def _print( msg):
            if print_progress:
                print( msg)

        if reset:
            self.A_wins_count = 0*self.A_wins_count
            self.n_repeats = 0

        if not batch_size:
            batch_size = n_repeats
        if batch_size>n_repeats:
            batch_size = n_repeats

        n_run = 0
        while n_run < n_repeats:
            n_run += batch_size

            for n_attack, n_defend in itertools.product( [1,2,3], [1,2,3]):
                _print(f"Simulating (attack vs defend): {n_attack} vs {n_defend}")

                # count attack wins
                a_wins = self.simulate(n_attack, n_defend, batch_size, use_stats=False)
                unique, _counts = np.unique(a_wins, return_counts=True)
                
                # count outcomes of attacking side winning 0, 1, 2, 3 units
                counts = np.zeros((4,), dtype=int)
                counts[unique] = _counts.astype(int)

                # store into matrices
                ii, jj = n_attack-1, n_defend-1
                self.A_wins_count[ii,jj,:] += counts

        # compute probabilities and (half-size) confidence intervals
        self.n_repeats += n_repeats
        self.A_wins_prob = self.A_wins_count/self.n_repeats
        self.A_wins_ci = 1.96*np.sqrt(  self.A_wins_prob*(1.-self.A_wins_prob) ) / np.sqrt(self.n_repeats)


    def simulate( self, n_attack: int, n_defend: int, n_repeats: int = 1, use_stats: bool = True):
        """Simulate a risk combact between `n_attack` attacking units and `n_defend` defening units. 
        The function simulates a roll of dice, and returns the amount of units loss by the defening 
        side - number of units destroyed by the attacking side. The simulation can be repeated multiple
        times and can use precomputed statistics.

        

        Args:
            n_attack (int): number of dices used during the attack. This is a number between 1 and 3. 
            n_defend (int): number of dices on the defending side.  This is a number between 1 and 3.
            n_repeats (int, optional): number of times the simulation is repeated. Defaults to 1.
        
        Returns:
            (np.array): array of integers showing, for each repetition, the amount of units destroyed by
                the attacking side.
        """

        if use_stats:
            # get win probabilities of attacking side
            prob = self.A_wins_prob[n_attack-1, n_defend-1, :]
            return np.random.choice( self.a_wins_outcomes, (n_repeats,), p=prob)
   
        else:
            return simulate_combact(n_attack, n_defend, n_repeats)


    def dump_stats( self):
        """Save combact stats to `self._path_to_stats`"""

        if self.n_repeats == 0:
            raise RuntimeError("No stats to be saved. Run `self.get_stats` first.")

        data = {
            "simulations": self.n_repeats,
            "attack_units": {
                ii+1 : {
                    "defend_units": {
                        jj+1: {
                            "defence_loses_units": self.a_wins_outcomes,
                            "count": [ int(cc) for cc in self.A_wins_count[ii,jj,:]],
                            "prob": list(self.A_wins_prob[ii,jj,:]),
                            "ci": list(self.A_wins_ci[ii,jj,:])
                        } for jj in range (3)
                    } 
                } for ii in range(3)
            }
        }
        with open(self._path_to_stats, "w") as fp:
            json.dump( data, fp)


    def load_stats( self):
        """Load combact stats to `self._path_to_stats`"""

        with open(self._path_to_stats, "r") as fp:
            data = json.load( fp)
        
        self.n_repeats = data["simulations"]
        for n_attack, a_data in data["attack_units"].items():
            ii = int(n_attack)-1
            for n_defend, stats in a_data["defend_units"].items():
                jj = int(n_defend)-1
                self.A_wins_count[ii,jj,:] = stats["count"]
                self.A_wins_prob[ii,jj,:] = stats["prob"]
                self.A_wins_ci[ii,jj,:] = stats["ci"]


    def verify_stats( self):
        """Verify loaded stats are correct."""

        assert np.all(self.A_wins_count.sum(axis=2) == self.n_repeats),\
            "Events count does not match number of simulations"

        p_tol = 1e-14 # 1./self.n_repeats
        assert np.max(np.abs( self.A_wins_prob.sum(axis=2) - 1.0))<p_tol,\
            "Probabilities do not sum to 1"
        
        ci_max = 1.96*np.sqrt(0.25)/np.sqrt(self.n_repeats)
        assert ci_max-np.max(self.A_wins_ci)>0.0, "Confidence intervals too large!"






if __name__ == '__main__':
    C = Combact()

    C.get_stats(n_repeats=0, batch_size=0, print_progress=True, reset=False)
    C.verify_stats()

    # C.get_stats(n_repeats=5000000, batch_size=5000000, print_progress=True, reset=False)
    # C.dump_stats()