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
    let value = p.monzoMoveBalanceGbp;
    const rate = p.monzoMoveAer / 12;
    for (let d = new Date(...p.moveFirstPaydayDate); d <= asOf; d = new Date(d.getFullYear(), d.getMonth() + 1, p.payday)) {
      value = value * (1 + rate) + p.moveMonthlyGbp;
    }
    return Math.round(value * 100) / 100;
  }
});
