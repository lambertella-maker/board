"""Canonical finance inputs and derived values. Existing assumptions, not new advice."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def load_plan(overrides=None):
    p = json.loads((ROOT / 'finance_inputs.json').read_text())
    p.update(overrides or {})
    p['subscriptionsMonthlyGbp'] = p['ukSubscriptionsMonthlyGbp'] + p['chatgptBudgetGbp'] + p['amazonPrimeMonthlyGbp']
    p['monthlySpendGbp'] = sum(p[k] for k in ('rentMonthlyGbp', 'groceriesMonthlyGbp', 'eatingOutMonthlyGbp', 'shoppingMonthlyGbp', 'transportMonthlyGbp', 'subscriptionsMonthlyGbp', 'utilitiesExPhoneMonthlyGbp', 'phoneMonthlyGbp', 'otherMonthlyGbp'))
    p['monthlyLeftoverGbp'] = p['salaryNetMonthlyGbp'] - p['monthlySpendGbp']
    p['salaryGrossMonthlyGbp'] = p['salaryGrossGbp'] / 12
    p['salaryNetAnnualGbp'] = p['salaryNetMonthlyGbp'] * 12
    p['salaryNextMeritGbp'] = p['salaryGrossGbp'] * (1 + p['meritAssumption'])
    p['pensionEmployeeMonthlyGbp'] = p['salaryGrossGbp'] * p['pensionEmployeeRate'] / 12
    p['pensionEmployeeAnnualGbp'] = p['pensionEmployeeMonthlyGbp'] * 12
    p['pensionTotalRate'] = p['pensionEmployeeRate'] + p['pensionEmployerRate']
    p['pensionMonthlyGbp'] = p['salaryGrossGbp'] * p['pensionTotalRate'] / 12
    p['pensionAnnualGbp'] = p['pensionMonthlyGbp'] * 12
    p['pensionMatchReturn'] = p['pensionEmployerRate'] / p['pensionEmployeeRate']
    p['sipEmployerMonthlyGbp'] = p['sipEmployeeMonthlyGbp'] * p['sipMatchRatio']
    p['sipMonthlyGbp'] = p['sipEmployeeMonthlyGbp'] + p['sipEmployerMonthlyGbp']
    p['sipNetMonthlyGbp'] = p['sipEmployeeMonthlyGbp'] * (1 - p['sipIncomeTaxRate'] - p['sipNiRate'])
    for key in ('Employee', 'Employer', 'Net'):
        p[f'sip{key}AnnualGbp'] = p[f'sip{key}MonthlyGbp'] * 12
    p['sipAnnualGbp'] = p['sipMonthlyGbp'] * 12
    p['sipUpsideAnnualGbp'] = p['sipAnnualGbp'] * (1 + p['sipScenarioGrowthRate'] * (1 - p['sipScenarioUsGainsRate']))
    p['sipDownsideAnnualGbp'] = p['sipAnnualGbp'] * (1 - p['sipScenarioGrowthRate'])
    p['sipHoldMonths'] = p['sipHoldYears'] * 12
    p['firePensionMonthlyGbp'] = p['pensionMonthlyGbp']
    p['fireAccessibleMonthlyGbp'] = p['fidelityTaxableMonthlyUsd'] * p['fxGbpPerUsd']
    p['fireRothMonthlyGbp'] = p['rothBrokerageMonthlyUsd'] * p['fxGbpPerUsd']
    p['rothRemaining2026Usd'] = max(0, p['rothLimit2026Usd'] - p['rothContributed2026Usd'])
    p['emergencyAnchorGbp'] = p['atomBalanceGbp'] + p['monzoEfBalanceGbp']
    p['flexibleCashMonthlyGbp'] = p['monthlyLeftoverGbp'] - p['wiseMonthlyGbp'] - p['moveMonthlyGbp']
    p['investReturn'] = sum(p[f'{fund}Weight'] * p[f'{fund}Return'] for fund in ('fskax', 'ftihx', 'fxnax'))
    # Whole-dollar display reconciles to the total: final allocation receives rounding remainder.
    p['fskaxMonthlyUsd'] = int(p['fidelityTaxableMonthlyUsd'] * p['fskaxWeight'] + .5)
    p['ftihxMonthlyUsd'] = int(p['fidelityTaxableMonthlyUsd'] * p['ftihxWeight'] + .5)
    p['fxnaxMonthlyUsd'] = p['fidelityTaxableMonthlyUsd'] - p['fskaxMonthlyUsd'] - p['ftihxMonthlyUsd']
    p['gymNetMonthlyGbp'] = p['gymGrossMonthlyGbp'] - p['gymNiSavedMonthlyGbp']
    p['taxTotalAllowanceGbp'] = p['taxAllowanceGbp'] + p['taxWfhAllowanceGbp']
    p['ilrFeeProjectedGbp'] = p['ilrFeeCurrentGbp'] * (1 + p['ilrFeeGrowth']) ** p['ilrFeeYears']
    p['usStateFullAnnualGbp'] = p['usStateFullAnnualUsd'] * p['fxGbpPerUsd']
    p['fireSliderMidGbp'] = (p['fireSliderMinGbp'] + p['fireSliderMaxGbp']) / 2
    p['advisorFeeMultiple'] = p['advisorExpenseRatio'] / p['fskaxExpenseRatio']
    p['pensionTaxableShare'] = 1 - p['pensionTaxFreeShare']
    return p
