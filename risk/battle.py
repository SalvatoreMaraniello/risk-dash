"""Tools for simulating Rsk battles
"""

import numpy as np

import risk.conf
from risk.combact import Combact






class Battle():
    """Class allowing simulation risk battles and compute their statistics. A battle is defined as
    a sequence of combacts between `n_attack` attacking units and `n_defende` defending units. The
    battle ends whenever one of the two sides is left with zero units.
    
    Attributes:
        n_attack (int): number of attacking units at the start of the battle. This does not 
            include any unit left behind. E.g., if you are attacking from a territory with 4
            units, you should set `n_attack<4`.
        n_defend (int): number of defending units.
        combact (risk.combact.Combact): combact simulator.
        prob_win (dict): dictionary with summary probabilities.
        _path_to_stats (str): Path to precomputed combact stats data.
        Probs (np.array, optional): Arrays of size `(max_number_combats, n_attack+1, n_defend+1)` 
            storing the probabilities of a battle. The element `(cc,ii,jj)` represents the probability
            that at combact (round) `cc-th` it will be observed a scenario in which attack and defense
            have units `ii` and `jj`, respectively.
        probs (dict): Dictionary with probabilities summary. Default to {}
        n_repeats (int, options): number of repetitions during numerical simulation of the battle. 
            Defaults to 1.
        Units_count (np.array, optional): Arrays of size `(n_combacts, n_attack+1, n_defend+1)` storing 
            the results of a numerical simulation. The element `(kk,ii,jj)` represents the number of 
            battles which, at completion of combact `kk`, saw `ii` attacking units and `jj` defending 
            units. Defaults to None.
    """

    def __init__( self, n_attack: int, n_defend: int, path_to_stats: str = None):
        """Initialise class.

        Args:
            n_attack (int): number of attacking units at the start of the battle. This does not 
                include any unit left behind. E.g., if you are attacking from a territory with 4
                units, you should set `n_attack<4`.
            n_defend (int): number of defending units.
            path_to_stats (str, optional): [description]. Defaults to `None` sets path to 
                `risk.conf.path_data_combact`.
        """

        assert n_attack>0 and n_defend>0, 'Attacking/Defending units must be at least 1'
        assert max(n_attack, n_defend) <= risk.conf.MAX_UNITS_BATTLE,\
            f'Attacking/Defending units must be below `risk.conf.MAX_UNITS_BATTLE = {risk.conf.MAX_UNITS_BATTLE}`'
        
        self.n_attack = n_attack
        self.n_defend = n_defend
        
        # Combact class
        self._conbact = Combact( path_to_stats)

        # numerical simulator
        self.n_repeats = 1
        self.Units_count = None

        # probabilities analysis
        self.max_combacts = None
        self.Probs = None
        self.probs = {}


    def simulate( self, n_repeats: int = None, print_progress: bool = True):
        """Run a battle simulation `n_repeats` times building `self.Units_count` and `self.prob_win`.

        Args:
            n_repeats (int, optional): number of times the simulation is repeated. Defaults to 
            None. In this case, `self.repeats` is used.
            print_progress (bool): if True, print progress of calculation. Defaults to True.
        """   

        def _print( msg):
            if print_progress:
                print( msg)
        
        if n_repeats:
            self.n_repeats = n_repeats

        ### units count per combact
        self.Units_count = np.zeros( (1, self.n_attack+1, self.n_defend+1), dtype=int)
        self.Units_count[0, self.n_attack, self.n_defend] = self.n_repeats

        # units available to fight - these are arrays, as different battles may take different outcomes
        n_attack_now = self.n_attack * np.ones((self.n_repeats,), dtype=int)
        n_defend_now = self.n_defend * np.ones((self.n_repeats,), dtype=int)

        n_ongoing = self.n_repeats
        while n_ongoing>0:
            # compute unique combinations attack vs defend
            N_combact = np.vstack( ( np.clip( n_attack_now, 0, 3), np.clip( n_defend_now, 0, 3))).T
            perm_list, total_list = np.unique(N_combact, axis=0, return_counts=True)

            for perm, total in zip( perm_list, total_list):
                n_attack_combact=perm[0]
                n_defend_combact=perm[1]
                print( f'Round {len(self.Units_count)}, attack vs defense {n_attack_combact, n_defend_combact}: {total}' )
                if n_attack_combact==0 or n_defend_combact==0:
                    continue

                a_wins = self._conbact.simulate( n_attack_combact, n_defend_combact, total)

                mask = np.logical_and( N_combact[:,0]==perm[0], N_combact[:,1]==perm[1])
                n_attack_now[mask] -= ( min(n_defend_combact, n_attack_combact) - a_wins)
                n_defend_now[mask] -= a_wins

            # store count
            N_status = np.vstack( (n_attack_now, n_defend_now)).T
            perm_list, total_list = np.unique(N_status, axis=0, return_counts=True)
            Units_count_combact = np.zeros( (1, self.n_attack+1, self.n_defend+1), dtype=int)

            for perm, total in zip( perm_list, total_list):
                ii, jj = perm
                Units_count_combact[0,ii,jj] = total
            self.Units_count = np.vstack( (self.Units_count, Units_count_combact) )

            # count over battles
            n_ongoing = sum(n_attack_now*n_defend_now!=0)



    def get_probabilities( self, min_prob: float = 1e-8):
        """Compute probabilities of risk battle. The function builds `self.Probs` and `self.prob_win`.

        Args:
            min_prob (float): if True, print progress of calculation. Defaults to True.
        """   

        # combact counter
        counter = 0

        self.Probs = np.zeros( (1, self.n_attack+1, self.n_defend+1))
        self.Probs[0, self.n_attack, self.n_defend] = 1.0

        while self.Probs[counter,1:,1:].sum() > min_prob:
            Probs_new = np.zeros( (1, self.n_attack+1, self.n_defend+1))

            for ii,jj in zip(*np.where( self.Probs[counter,:,:]>0.0)):
                if ii*jj == 0:
                    continue

                # determine attack/defend side
                n_attack, n_defend = min(3, ii), min(3, jj)
                max_units_lost = min(n_attack, n_defend)

                # get probabilities of attack side winning
                a_wins_probs = self._conbact.A_wins_prob[ n_attack-1, n_defend-1, :max_units_lost+1]

                for a_wins in range(max_units_lost+1):
                    ii_new = max(0, ii-(max_units_lost-a_wins))
                    jj_new = max(0, jj-a_wins)
                    print(f'\t({ii_new},{jj_new})')
                    Probs_new[0, ii_new, jj_new] += self.Probs[counter, ii, jj]*a_wins_probs[a_wins]

            self.Probs = np.vstack( (self.Probs, Probs_new))
            counter += 1

        self.max_combacts = counter
        self.get_probabilities_summary()


    def get_probabilities_summary( self):
        """Compute summary of battles probabilities. The function builds/updates `self.probs`.
        """   
        self.probs = {
            "attack": {
                "total": self.Probs[:,:,0].sum(),
                "distr": {
                    "units": [ii for ii in range(self.n_attack+1)],
                    "probs": self.Probs[:,:,0].sum(axis=0)
                }
            },
            "defense": {
                "total": self.Probs[:,0,:].sum(),
                "distr": {
                    "units": [ii for ii in range(self.n_defend+1)],
                    "probs": self.Probs[:,0,:].sum(axis=0)
                }
            }
        }



if __name__=='__main__':
    B = Battle(n_attack=3, n_defend=2)

    B.get_probabilities()
    B.simulate(n_repeats=10000)
    print(B.probs)

    # verify - total probabilities
    print(f"Prob. attack wins (numerical vs exact): {B.Units_count[-1,:,0].sum()/B.n_repeats} vs {B.probs['attack']['total']}")
    print(f"Prob. defence wins (numerical vs exact): {B.Units_count[-1,0,:].sum()/B.n_repeats} vs {B.probs['defense']['total']}")

    # verify - specific
    print("Prob. attack wins with 2 units (numerical vs exact): " +
        f"{B.Units_count[-1,2,0]/B.n_repeats} vs {B.probs['attack']['distr']['probs'][2]}")
    print("Prob. attack wins with at least 2 units (numerical vs exact): " +
        f"{B.Units_count[-1,2:,:].sum()/B.n_repeats} vs {B.probs['attack']['distr']['probs'][2:].sum()}")

