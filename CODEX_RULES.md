# Dashboard Editing Rules

## Superseded States

When a dashboard value, label, rule, or UI state is changed, remove all superseded fallbacks and stale branches everywhere in the live dashboard variants unless the product explicitly requires multiple valid conditional states.

This applies to:
- visible HTML defaults
- JavaScript fallback branches and conditionals
- helper copy, badges, and labels
- repeated text across `dashboard.html`, `dashboard_mobile.html`, `dashboard_ipad.html`, and `dashboard_iphone.html`

Default rule:
- Do not leave the old value behind in an `else` branch, preload value, or fallback string.
- Only preserve multiple branches when the intended behavior truly requires distinct states.
