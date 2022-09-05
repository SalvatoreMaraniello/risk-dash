'''
Simple dashboard to visualise risk statistics.
'''

import param
import bokeh.io
import bokeh.models
import bokeh.plotting
import bokeh.transform
from bokeh.resources import INLINE
import panel as pn
import numpy as np 

import risk.battle, risk.combact

### plotting params
COLORS = {
    'attack': '#F93D15',
    'defense': '#1D8ED8'
}




class RiskParamViewer(param.Parameterized):
    
    MAX_DICE = 15

    # for probabilities visualisation
    n_attack = param.Integer(default=3, bounds=(0, MAX_DICE))
    n_defense = param.Integer(default=3, bounds=(0, MAX_DICE))
    probabilities = param.Dict(default={"attack": None, "defense": None})

    # for interactive simulation
    roll_action = param.Action(lambda x: x.param.trigger('roll_action'), label='Roll dice!')
    last_roll = param.Dict(
        default={
            "attack": { "dice": [], "won": 0, "lost": 0},
            "defense": { "dice": [], "won": 0, "lost": 0}
            }
        )

    @param.depends('n_attack', 'n_defense', watch=True)
    def _update_probabilities(self):
        B = risk.battle.Battle( self.n_attack, self.n_defense)
        B.get_probabilities()
        self.probabilities = B.probs

    def __init__(self, **params):
        super().__init__(**params)
        self._update_probabilities()
        self.view_total_win_probs()
        self.view_cumultative_distribution()

    @param.depends('roll_action', watch=True)
    def roll( self):

        n_attack = min( 3, self.n_attack)
        n_defense = min( 3, self.n_defense)
        n = min( n_attack, n_defense)
        
        # Simulate dice roll
        A = risk.combact.roll_and_sort( n_attack, 1)
        D = risk.combact.roll_and_sort( n_defense, 1)

        # Compare and count
        a_wins = int( (A[:,:n]>D[:,:n]).sum( axis=1)[0] )

        # update params
        self.last_roll['attack'] = {
            "dice": list(A[0, :n_attack]),
            "won": a_wins,
            "lost": n_attack - a_wins
        }
        self.last_roll['defense'] = {
            "dice": list(D[0, :n_defense]),
            "won": n_defense - a_wins,
            "lost": a_wins
        }
        
        self.n_attack = max(0, self.n_attack - n_defense + a_wins)
        self.n_defense = max(0, self.n_defense - a_wins)

        return A, D, a_wins


    def _test_reactive( self):
        return pn.panel( str(self.probabilities))

    def view_total_win_probs( self):

        data = { 'side': [kk for kk in self.probabilities.keys()]}
        data['probs'] = [100*self.probabilities[kk]['total'] for kk in data['side']]
        data['prob_rads'] =  [np.pi*self.probabilities[kk]['total'] for kk in data['side']]
        data['start_angle'] = np.cumsum( [0] + list(data['prob_rads'])[:-1])
        data['end_angle'] = np.cumsum( list(data['prob_rads']))
        data['colors'] = [COLORS[kk] for kk in data['side']]

        p = bokeh.plotting.figure(
            title="Win odds",
            x_range=(-1, 1), y_range=(0,1),
            aspect_ratio = 1.7, 
            background = None,
            toolbar_location=None,
            tooltips=[ ('side', '@side'), ('win probability', '@probs{0.00}%') ],
        )

        p.annular_wedge(
            x=0, y=0, inner_radius=0.3, outer_radius=0.8,
            direction='anticlock', start_angle='start_angle', end_angle='end_angle', 
            color = 'colors', source=data,
            line_color = 'white', line_width=2, alpha=.8)

        p.axis.axis_label = None
        p.axis.visible = False
        p.ygrid.visible = False
        p.xgrid.visible = False
        # p.grid.grid_line_color = None
        p.outline_line_color = None

        return p


    def view_cumultative_distribution( self):

        max_units_standing = max(self.n_attack, self.n_defense)
        data = {
             'x_label': ["\u2265 %.1d" %uu for uu in range(1, max_units_standing+1)],   
            }
        data['x_label'][-1] = str(max_units_standing)

        # fill arrays with zeros
        for key in self.probabilities.keys():
            max_units_here = len(self.probabilities[key]['cumdistr']['probs'])
            data[key] = np.zeros((max_units_standing,))
            data[key][:max_units_here] = 100.*self.probabilities[key]['cumdistr']['probs']
        source = bokeh.models.ColumnDataSource( data)

        p = bokeh.plotting.figure(
            title="To the last blood battle",
            x_axis_label='units standing', 
            y_axis_label='%',
            x_range=data['x_label'], 
            # aspect_ratio = 3,
            # height=300,
            background = None,
            toolbar_location=None,
            tooltips=[
                ('units', '@x_label'),
                ('attack', '@attack{0.00}%'),
                ('defense', '@defense{0.00}%'),
            ],
        )
        p.vbar(
            x=bokeh.transform.dodge('x_label', -0.08, range=p.x_range), top='attack', width=0.15, 
            source=source, color=COLORS['attack'], legend_label="attack", alpha=.6)
        p.vbar(
            x=bokeh.transform.dodge('x_label', 0.08, range=p.x_range), top='defense', width=0.15, 
            source=source, color=COLORS['defense'], legend_label="defense", alpha=.6)

        p.grid.grid_line_color = None
        p.y_range.start = 0
        
        return p

    
    def view_last_roll( self):

        max_units_standing = 3 # max(self.last_roll['attack']['dice'], self.n_defense)
        data = { 'y_label': ["die %.1d" %uu for uu in range(1, max_units_standing+1)]}

        # fill arrays with zeros
        for key in self.last_roll.keys():
            dice = self.last_roll[key]['dice']
            if len(dice)<max_units_standing:
                dice += [None] * (max_units_standing - len(dice))
            data[key] = dice

        source = bokeh.models.ColumnDataSource( data)

        p = bokeh.plotting.figure(
            title="Roll outcome",
            x_axis_label='die value',
            y_range=data['y_label'], 
            aspect_ratio = 1.7,
            background = None,
            toolbar_location=None,
            tooltips=[
                ('attack', '@attack{0}'),
                ('defense', '@defense{0}'),
            ],
        )
        p.hbar(
            y=bokeh.transform.dodge('y_label', -0.08, range=p.y_range), right='attack', height=0.15, 
            source=source, color=COLORS['attack'], alpha=.6)
        p.hbar(
            y=bokeh.transform.dodge('y_label', 0.08, range=p.y_range), right='defense', height=0.15, 
            source=source, color=COLORS['defense'],  alpha=.6)

        p.ygrid.grid_line_color = None
        p.x_range.start = 0
        p.x_range.end = 6.2

        return p

    
    def print_last_roll( self):
        rows, total_won = [], 0
        for key, it in self.last_roll.items():
            # if len(it['dice'])==0:
            #     return 'Battle is over!'
            total_won += it['won']
            rows.append( f'''- {key.capitalize()} wins {it['won']}''' )
        if total_won==0:
            return ''
        return '\n\n'.join( rows)
        

       
            


    

viewer = RiskParamViewer(name='Risk Dash')

attack_units_selector = pn.widgets.IntSlider.from_param(
    viewer.param.n_attack, name='Attacking units', step=1, bar_color = COLORS['attack'])

defence_units_selector = pn.widgets.IntSlider.from_param(
    viewer.param.n_defense, name='Defending units', step=1, bar_color = COLORS['defense'])

roll_button = pn.widgets.Button.from_param(
    viewer.param.roll_action, name='🎲  Roll dice!', button_type='primary', width=100
)


# settings
D = pn.Column(

    f'''# Risk Battle Simulator\n''',

    '''Set the number of attacking and defending units. Roll dice to simulate a battle. '''
    '''The dashboard will automatically update win/lose probabilities as units are lost!\n\n'''
    '''**Note:** attacking units do not include any units left behind.''',

    pn.Row(
        pn.Column(
            '### Settings:',
            pn.panel( attack_units_selector, width=180, align='start'),
            defence_units_selector,
            pn.Spacer(height=2),
            pn.panel( viewer.view_total_win_probs, width=200, align='center'),
            pn.Spacer(height=4),
            width=300, 
            background = '#D5DBDB'
        ), 
        pn.Spacer(width=100),
        pn.Column(
            pn.panel( viewer.view_last_roll, width=240),
            pn.Spacer(height=4),
            pn.Row(
                pn.panel( roll_button, aligh='center'),
                pn.panel( viewer.print_last_roll ),
            ),
            width=320
        )
 
        
    ),

    pn.layout.Divider(),
    pn.panel( viewer.view_cumultative_distribution, width=800, height=280),
   

    width=800
)


D.servable()
D.save( './risk-dashboard-static.html', 
    resource=INLINE, 
    embed=True, 
    embed_states={ 
        attack_units_selector: [2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15],
        defence_units_selector: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15]
        }
    )

