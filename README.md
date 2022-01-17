# Risk statistics dashboard
*S. Maraniello*, Jul-2021

A daskboard to calculate risk statistics.


## Preliminary

Make environment:

```sh
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

## Build documentation

```sh
cd docs
make html
```


## Launch the dashboard
```sh
panel serve --autoreload --show risk_dashboard.py 
```