#!/usr/bin/env python3
"""Render all active dashboards from one financial model. --check detects stale output."""
import argparse
import hashlib
import json
import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from finance_model import ROOT, load_plan

NAMES = ('dashboard.html', 'dashboard_ipad.html', 'dashboard_iphone.html')
TOKEN = re.compile(r'\{\{(\w+)(?::(\w+))?\}\}')

def number(value, places=0):
    rounded = Decimal(str(value)).quantize(Decimal(10) ** -places, rounding=ROUND_HALF_UP)
    return f'{rounded:,.{places}f}'

def format_value(value, fmt):
    if fmt == 'json':
        return json.dumps(value)
    if fmt == 'pctnumber':
        return number(value * 100)
    if fmt == 'k':
        return number(value / 1000) + 'k'
    if fmt == 'number':
        return number(value)
    if fmt == 'percent':
        return number(value * 100, 3).rstrip('0').rstrip('.') + '%'
    if fmt == 'raw':
        return str(value)
    currency = '$' if fmt.startswith('usd') else '€' if fmt.startswith('eur') else '£'
    if 'k' in fmt:
        places = 2 if fmt.endswith('1') else 0
        text = number(value / 1000, places)
        return currency + text + 'k'
    # Whole amounts stay compact; fractional money always keeps both decimal
    # places so a value can never render as a bare `.5`.
    places = 2 if fmt.endswith('2') or not float(value).is_integer() else 0
    return currency + number(value, places)

def render_all(plan=None):
    plan = load_plan() if plan is None else plan
    templates = {n: (ROOT / 'templates' / n).read_text() for n in NAMES}
    plan_json = json.dumps(plan, sort_keys=True, indent=2)
    runtime = (ROOT / 'finance_runtime.js').read_text()
    build = hashlib.sha256((plan_json + runtime + ''.join(templates.values())).encode()).hexdigest()[:16]
    def replace(m):
        key, fmt = m.groups()
        if key == 'BUILD': return build
        if key == 'RUNTIME_SCRIPT': return runtime
        if key == 'PLAN_SCRIPT': return 'window.PLAN = Object.freeze(' + plan_json + ');'
        if key not in plan: raise ValueError(f'Unknown finance variable: {key}')
        return format_value(plan[key], fmt)
    return {n: TOKEN.sub(replace, s) for n, s in templates.items()}

def check_generated():
    return [n for n, text in render_all().items() if not (ROOT / n).exists() or (ROOT / n).read_text() != text]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.check:
        stale = check_generated()
        if stale:
            print('Stale finance dashboards: ' + ', '.join(stale) + '; run python3 build_finance.py')
            return 1
        print('All finance dashboards match the canonical model and templates')
    else:
        for name, text in render_all().items():
            target = ROOT / name
            if not target.exists() or target.read_text() != text:
                target.write_text(text)
                print('Rendered ' + name)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
