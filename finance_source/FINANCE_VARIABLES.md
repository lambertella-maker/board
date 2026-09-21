# Finance variables

Edit `finance_inputs.json` for a balance, contribution, rate, budget category, or scenario assumption. Related totals are calculated in `finance_model.py`; shared date-sensitive SIP and Move Pot balances are calculated in `finance_runtime.js`. Currency, units, and purpose are explicit in the keys. Equal amounts with different purposes (for example move target and annual SIP contribution) remain distinct.

Edit layout/copy in `templates/dashboard.html`, `templates/dashboard_ipad.html`, or `templates/dashboard_iphone.html`. Use `{{variable:gbp}}`, `{{variable:usd}}`, `{{variable:percent}}`, or the other formats in `build_finance.py`. Use `window.PLAN.variable` in calculations. Never edit the generated dashboard files directly.

Run from `/Users/ellalambert/Desktop/Finances`:

```sh
python3 build_finance.py
python3 test_finance_model.py
python3 all_cylinders_check.py
```

The publisher refuses stale generated output or failed tests. All three published HTML files embed the same generated model and shared runtime so they work as standalone pages, without an additional data fetch. Their repeated rendered numbers are generated output, not independently maintained inputs. Source files are also backed up under `finance_source/` in the publishing repository.

Scope: Ella's active desktop, iPad, and iPhone dashboards. Archives, historical Markdown snapshots, Decision Studio, and other people's dashboards are separate and were not converted. CSS dimensions, formatting constants, historical dates, and identifiers are not financial inputs. Tax/legal snapshots and planning assumptions were preserved from existing sources; this refactor does not refresh their validity.

Reconciliations: budget total is now the sum of its categories; FIRE contributions follow active monthly investments; current Chase UK display and net-worth use one balance; current investment-value cards share live estimates while explicitly dated anchor notes retain their snapshot purpose; the Move Pot and SIP share one calculation across devices.
