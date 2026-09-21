"""Regression checks for one-source finance values; no live financial assumptions."""
import json
import re
import subprocess
import unittest
from html.parser import HTMLParser
from finance_model import ROOT, load_plan
from build_finance import render_all, check_generated

class VisibleNumbers(HTMLParser):
    def __init__(self):
        super().__init__(); self.skip = False; self.literals = []
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'): self.skip = True
    def handle_endtag(self, tag):
        if tag in ('script', 'style'): self.skip = False
    def handle_data(self, text):
        if not self.skip and re.search(r'[£$€]\d', text): self.literals.append(text)

class FinanceTests(unittest.TestCase):
    def test_generated_outputs(self):
        self.assertEqual(check_generated(), [])
        naked_half = re.compile(r'(?:£|\$|€)[0-9,]+\.5(?![0-9kM])')
        for name, html in render_all().items():
            self.assertIsNone(naked_half.search(html), name)
    def test_shared_model_and_no_money_literals(self):
        for name, html in render_all().items():
            models = re.findall(r'window.PLAN = Object.freeze\((\{.*?\})\);', html, re.S)
            self.assertEqual(len(models), 1)
            self.assertEqual(json.loads(models[0]), load_plan())
            parser = VisibleNumbers(); parser.feed((ROOT/'templates'/name).read_text())
            self.assertEqual(parser.literals, [], name)
    def test_mutation_propagates_to_all_devices(self):
        p = load_plan({'sipEmployeeMonthlyGbp': 200, 'sipMatchRatio': 2, 'rentMonthlyGbp': 1300, 'fidelityTaxableMonthlyUsd': 1000})
        self.assertEqual(p['sipMonthlyGbp'], 600)
        self.assertEqual(p['sipAnnualGbp'], 7200)
        self.assertEqual(p['sipEmployeeAnnualGbp'], 2400)
        self.assertAlmostEqual(p['sipNetMonthlyGbp'], 116)
        self.assertEqual(sum(p[k] for k in ('fskaxMonthlyUsd','ftihxMonthlyUsd','fxnaxMonthlyUsd')), 1000)
        self.assertEqual(p['salaryNetMonthlyGbp'] - p['monthlySpendGbp'], p['monthlyLeftoverGbp'])
        for name, html in render_all(p).items():
            self.assertIn('£7,200/yr', html, name)
            self.assertIn('£1,300', html, name)
            self.assertNotIn('£87', html, name)
    def test_runtime_payday_boundaries(self):
        p = load_plan({'sipEmployeeMonthlyGbp':200, 'sipMatchRatio':2})
        js = 'global.window={PLAN:'+json.dumps(p)+'};\n'+(ROOT/'finance_runtime.js').read_text()+'''
const before=window.Finance.sip(new Date(2024,10,23));
const payday=window.Finance.sip(new Date(2024,10,24));
const second=window.Finance.sip(new Date(2024,11,24));
if(before.value!==0 || payday.value!==600 || second.value!==1200) throw Error('SIP payday drift');
if(window.Finance.moveBalance(new Date(2026,7,23))!==window.PLAN.monzoMoveBalanceGbp) throw Error('Move anchor drift');
'''
        result=subprocess.run(['node','-e',js],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

if __name__ == '__main__': unittest.main()
