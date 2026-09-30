"""Merge the weekly source-take CSVs in analysis/takes/ into analysis/takes.json.

One CSV per week and kind, named <season>_w<NN>_<performance|matchup>.csv:
  performance = what a source said about the week that was played (job, usage tier, trend)
  matchup     = what a source said about the coming game (outlook tier, stance)
Tiers use the page's scale: Elite / Great / Average / Replacement.
College notes (analysis/cfb/takes/) go to analysis/cfb_takes.json for the Board."""
import csv, glob, json, os, re

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'analysis')
SOURCES = {
    'Gretch': 'Ben Gretch, Stealing Signals / Input Volatility',
    'FP': 'Fantasy Points, The Everything Report (Heath & Barfield)',
    'ETR': 'Establish the Run, Strength in Numbers (Jack Miller)',
    'Kerrane': 'Pat Kerrane, Legendary Upside Walkthrough',
}
takes = []
for path in sorted(glob.glob(os.path.join(HERE, 'takes', '*.csv'))):
    m = re.search(r'(\d{4})_w(\d+)_(performance|matchup)\.csv$', path)
    if not m: continue
    with open(path, newline='') as f:
        for row in csv.DictReader(f):
            row = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items() if v not in (None, '')}
            row.update(season=int(m.group(1)), week=int(row.get('week') or m.group(2)), kind=m.group(3))
            takes.append(row)
with open(os.path.join(HERE, 'takes.json'), 'w') as f:
    json.dump({'sources': SOURCES, 'takes': takes}, f, separators=(',', ':'))
print(f'{len(takes)} takes -> analysis/takes.json')

# College: one CSV per week and position, <season>_w<NN>_<pos>.csv in analysis/cfb/takes/,
# shown in the Board's dropdown on CFB slates on top of the CFBD baseline.
CFB_SOURCES = {'Bauer': 'Nick Bauer, CFB positional breakdowns (X)'}
cfb = []
for path in sorted(glob.glob(os.path.join(HERE, 'cfb', 'takes', '*.csv'))):
    m = re.search(r'(\d{4})_w(\d+)_([a-z]+)\.csv$', path)
    if not m: continue
    with open(path, newline='') as f:
        for row in csv.DictReader(f):
            row = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items() if v not in (None, '')}
            row.update(season=int(m.group(1)), week=int(row.get('week') or m.group(2)))
            row.setdefault('pos', m.group(3).upper())
            cfb.append(row)
with open(os.path.join(HERE, 'cfb_takes.json'), 'w') as f:
    json.dump({'sources': CFB_SOURCES, 'takes': cfb}, f, separators=(',', ':'))
print(f'{len(cfb)} college takes -> analysis/cfb_takes.json')
