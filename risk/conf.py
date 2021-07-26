"""Define settings for package. See summary below.
"""

import os, pathlib


# Gama Parameters
MAX_UNITS_BATTLE = 100
"""Parameter defining maximum units allowed to take place into a battle."""


# define absolute paths
path_root = pathlib.Path(__file__).parent.as_posix()
path_data_folder = os.path.join( path_root, 'data' )
path_data_combact = os.path.join( path_data_folder, 'combact_data.json')