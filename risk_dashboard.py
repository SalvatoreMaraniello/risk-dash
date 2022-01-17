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

import risk.battle


### plotting params
COLORS = {
    'attack': '#F93D15',
    'defense': '#1D8ED8'
}

B = risk.battle.Battle( 3, 4)
B.get_probabilities()
B.simulate(n_repeats=10000)
MAX_DICE = 30


class RiskParamViewer(param.Parameterized):
    
    n_attack = param.Integer(default=3, bounds=(1, MAX_DICE))
    n_defense = param.Integer(default=3, bounds=(1, MAX_DICE))
    probabilities = param.Dict(default={"attack": None, "defense": None})

    @param.depends('n_attack', 'n_defense', watch=True)
    def _update_probabilities(self):
        B = risk.battle.Battle( self.n_attack, self.n_defense)
        B.get_probabilities()
        B.simulate(n_repeats=10000)
        self.probabilities = B.probs

    def __init__(self, **params):
        super().__init__(**params)
        self._update_probabilities()
        self.view_total_win_probs()
        self.view_cumultative_distribution()

    def _test_reactive( self):
        return pn.panel( str(self.probabilities))

    def view_total_win_probs( self):

        x_labels = [kk for kk in self.probabilities.keys()]
        y_values = [100*self.probabilities[kk]['total'] for kk in x_labels]
        colors =  [COLORS[kk] for kk in x_labels]

        p = bokeh.plotting.figure(
            title="Win probability",
            y_axis_label = '%',
            x_range=x_labels, 
            aspect_ratio = 2, 
            background = None,
            toolbar_location="right",
            tooltips=[
                ('side', '@x'),
                ('win probability', '@top{0.00}%'),  
            ],
        )

        p.vbar(
            x=x_labels, top=y_values, width=0.5, fill_color=colors, fill_alpha=.7, line_color='.4')
        p.xgrid.grid_line_color = None
        p.y_range.start = 0

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
            title="Units standing at the end of battle...",
            x_axis_label='units standing', 
            y_axis_label='%',
            x_range=data['x_label'], 
            aspect_ratio = 3,
            background = None,
            toolbar_location="below",
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

        p.xgrid.grid_line_color = None
        p.y_range.start = 0
        
        return p


viewer = RiskParamViewer(name='Risk Dash')

attack_units_selector = pn.widgets.IntSlider.from_param(
    viewer.param.n_attack, name='attacking units', step=1, bar_color = COLORS['attack'])

defence_units_selector = pn.widgets.IntSlider.from_param(
    viewer.param.n_defense, name='Defeniding units', step=1, bar_color = COLORS['defense'])

# settings
D = pn.Column(

    f'''# Risk Battle: probabilities calculator\n\n'''
    '''- **attacking** units: number of attacking units at the start of the battle. '''
    ''' This does not include any unit left behind. '''
    ''' E.g., if you are attacking from a territory with 4 units, you should set `attacking units < 4`.\n'''
    ''' - **defending** units: number of units defending the territory.''',

    pn.Row(
        pn.Column(
            attack_units_selector,
            pn.Spacer(height=15),
            defence_units_selector,
            width=300
        ), 
        pn.Spacer(width=10),
        pn.panel( viewer.view_total_win_probs, width=350)
    ),

    pn.Row(
        pn.panel( viewer.view_cumultative_distribution, width=660)
    ),
)


D.servable()
D.save( './risk-dashboard-static.html', resource=INLINE)

