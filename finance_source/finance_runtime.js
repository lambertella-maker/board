// Shared date-sensitive calculations. PLAN is embedded by build_finance.py.
window.Finance = Object.freeze({
  money(value) {
    const places = Number.isInteger(value) ? 0 : 2;
    return Number(value).toLocaleString('en-GB', { minimumFractionDigits: places, maximumFractionDigits: 2 });
  },
  sip(asOf) {
    const p = window.PLAN;
    const start = new Date(...p.sipStartDate);
    const months = (asOf.getFullYear() - start.getFullYear()) * 12 + asOf.getMonth() - start.getMonth();
    const completed = Math.max(0, months + (asOf.getDate() >= p.payday ? 1 : 0));
    return { completed, value: completed * p.sipMonthlyGbp };
  },
  moveBalance(asOf) {
    const p = window.PLAN;
    // Monthly planning estimate through the June 2027 move, within Chase's first term.
    // Existing Monzo principal stays put; only new contributions go to Chase.
    let monzo = p.monzoMoveBalanceGbp;
    let chase = 0;
    const monzoRate = Math.pow(1 + p.monzoMoveAer, 1 / 12) - 1;
    const chaseRate = Math.pow(1 + p.chaseRegularSaverAer, 1 / 12) - 1;
    for (let d = new Date(...p.moveFirstPaydayDate); d <= asOf; d = new Date(d.getFullYear(), d.getMonth() + 1, p.payday)) {
      monzo *= 1 + monzoRate;
      chase = chase * (1 + chaseRate) + p.moveMonthlyGbp;
    }
    return Math.round((monzo + chase) * 100) / 100;
  }
});
