#!/usr/bin/env node
// economy-check.mjs: read a JSON description of a rewards economy and say whether it holds:
// the margin per dollar of revenue, the share paid to users once bonuses are counted, the
// break-even points, and every rule the numbers break.
// It is a planning model. Every input is the app's own figure; nothing here is an estimate
// of what an app will earn. No dependencies, Node 20 or newer.
// Exit codes: 0 the economy holds, 1 a rule is violated, 2 usage or input error.
import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

const USAGE = `Usage:
  node economy-check.mjs <economy.json> [--json]

<economy.json> describes the economy with the app's own numbers:
  currency   coinsPerDollar, redeemCoinsPerDollar, name
  earning    userSharePct, smallestPayoutUsd
  volume     monthlyRevenueUsd, activeUsers, newUsers
  bonuses    a list: per_new_user, per_active_user_per_day, per_active_user_per_month,
             fixed_per_month (coins, takeUpPct), earning_multiplier, referral (pct, coveragePct)
  payout     minimumUsd, feePct, feeFixedUsd, feePaidBy, averagePayoutUsd, redemptionPct
  reversals  ratePct, holdDays, arrival [{ days, pct }], lateRecoveryPct
  costs      otherPctOfRevenue, fixedMonthlyUsd
  cash       outstandingCoins, reserveUsd, receivablesUsd, networkPaymentDelayDays
  targets    minMarginPct, maxEffectiveSharePct, maxBonusPctOfRevenue,
             maxDaysToMinimumPayout, minReversalsInsideHoldPct, maxRoundingLossPct

Required: currency.coinsPerDollar, earning.userSharePct, volume.monthlyRevenueUsd,
payout.minimumUsd. Keys that start with "_" or "$" are ignored, so a file can carry notes.

Options:
  --json   print the full result as JSON instead of text

Exit codes: 0 the economy holds, 1 at least one rule is violated, 2 usage or input error.
`;

const DAYS_PER_MONTH = 30;
const EPSILON = 1e-9;

class UsageError extends Error {}

export class InputError extends Error {
  constructor(problems) {
    super(
      `The economy file has ${problems.length} problem${problems.length === 1 ? '' : 's'}:\n` +
        problems.map((p) => `  - ${p}`).join('\n'),
    );
    this.problems = problems;
  }
}

const pct = { type: 'number', min: 0, max: 100 };
const amount = { type: 'number', min: 0 };
const positive = { type: 'number', above: 0 };

const SECTIONS = {
  currency: {
    name: { type: 'string', def: 'coins' },
    coinsPerDollar: { ...positive, required: true },
    redeemCoinsPerDollar: positive,
  },
  earning: {
    userSharePct: { type: 'number', above: 0, max: 100, required: true },
    smallestPayoutUsd: positive,
  },
  volume: {
    monthlyRevenueUsd: { ...positive, required: true },
    activeUsers: amount,
    newUsers: amount,
  },
  payout: {
    minimumUsd: { ...positive, required: true },
    feePct: { ...pct, def: 0 },
    feeFixedUsd: { ...amount, def: 0 },
    feePaidBy: { type: 'enum', values: ['app', 'user'], def: 'app' },
    averagePayoutUsd: positive,
    redemptionPct: { ...pct, def: 100 },
  },
  reversals: {
    ratePct: { type: 'number', min: 0, below: 100, def: 0 },
    holdDays: { ...amount, def: 0 },
    lateRecoveryPct: { ...pct, def: 0 },
    arrival: { type: 'arrival' },
  },
  costs: {
    otherPctOfRevenue: { ...pct, def: 0 },
    fixedMonthlyUsd: { ...amount, def: 0 },
  },
  cash: {
    outstandingCoins: amount,
    reserveUsd: amount,
    receivablesUsd: { ...amount, def: 0 },
    networkPaymentDelayDays: amount,
  },
  targets: {
    minMarginPct: { type: 'number', max: 100, def: 0 },
    maxEffectiveSharePct: { type: 'number', above: 0 },
    maxBonusPctOfRevenue: amount,
    maxDaysToMinimumPayout: positive,
    minReversalsInsideHoldPct: pct,
    maxRoundingLossPct: { type: 'number', above: 0, max: 100 },
  },
};

const BONUS_FIELDS = {
  per_new_user: { coins: { ...positive, required: true }, takeUpPct: { ...pct, def: 100 }, requiresEarning: { type: 'boolean', def: false } },
  per_active_user_per_day: { coins: { ...positive, required: true }, takeUpPct: { ...pct, def: 100 }, requiresEarning: { type: 'boolean', def: false } },
  per_active_user_per_month: { coins: { ...positive, required: true }, takeUpPct: { ...pct, def: 100 }, requiresEarning: { type: 'boolean', def: false } },
  fixed_per_month: { coins: { ...positive, required: true } },
  earning_multiplier: { pct: { ...positive, required: true }, coveragePct: { ...pct, def: 100 } },
  referral: { pct: { ...positive, required: true }, coveragePct: { ...pct, def: 100 } },
};

const isObject = (value) => typeof value === 'object' && value !== null && !Array.isArray(value);
const isNote = (key) => key.startsWith('_') || key.startsWith('$');

function readField(value, where, spec, problems) {
  if (value === undefined) {
    if (spec.required) problems.push(`"${where}" is required`);
    return spec.def;
  }
  if (spec.type === 'string') {
    if (typeof value !== 'string' || !value.trim()) problems.push(`"${where}" must be a non-empty string`);
    return value;
  }
  if (spec.type === 'boolean') {
    if (typeof value !== 'boolean') problems.push(`"${where}" must be true or false`);
    return value;
  }
  if (spec.type === 'enum') {
    if (!spec.values.includes(value)) problems.push(`"${where}" must be one of: ${spec.values.join(', ')}`);
    return value;
  }
  if (spec.type === 'arrival') return readArrival(value, where, problems);
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    problems.push(`"${where}" must be a number, got ${JSON.stringify(value)}`);
    return spec.def;
  }
  if (spec.min !== undefined && value < spec.min) problems.push(`"${where}" must be ${spec.min} or more, got ${value}`);
  if (spec.above !== undefined && value <= spec.above) problems.push(`"${where}" must be greater than ${spec.above}, got ${value}`);
  if (spec.max !== undefined && value > spec.max) problems.push(`"${where}" must be ${spec.max} or less, got ${value}`);
  if (spec.below !== undefined && value >= spec.below) problems.push(`"${where}" must be less than ${spec.below}, got ${value}`);
  return value;
}

// The arrival curve is cumulative: of all reversals, the percentage that had arrived
// within N days of the credit. Days must rise and percentages must not fall.
function readArrival(value, where, problems) {
  if (!Array.isArray(value) || value.length === 0) {
    problems.push(`"${where}" must be a list of { "days": N, "pct": P } points`);
    return undefined;
  }
  let lastDays = 0;
  let lastPct = 0;
  for (const [i, point] of value.entries()) {
    const at = `${where}[${i}]`;
    if (!isObject(point) || typeof point.days !== 'number' || typeof point.pct !== 'number') {
      problems.push(`"${at}" must be { "days": N, "pct": P }`);
      return undefined;
    }
    if (!(point.days > lastDays)) problems.push(`"${at}.days" must be greater than the point before it (${lastDays})`);
    if (point.pct < lastPct || point.pct > 100) problems.push(`"${at}.pct" must be between ${lastPct} and 100`);
    lastDays = point.days;
    lastPct = point.pct;
  }
  return value.map(({ days, pct: p }) => ({ days, pct: p }));
}

function readSection(source, where, fields, problems, extra = []) {
  const out = {};
  if (source !== undefined && !isObject(source)) {
    problems.push(`"${where}" must be an object`);
    source = undefined;
  }
  for (const key of Object.keys(source ?? {})) {
    if (!isNote(key) && !extra.includes(key) && !(key in fields)) problems.push(`"${where}.${key}" is not a known field`);
  }
  for (const [name, spec] of Object.entries(fields)) out[name] = readField(source?.[name], `${where}.${name}`, spec, problems);
  return out;
}

// Check the input and fill in defaults. Throws InputError listing every problem at once.
export function normalize(input) {
  const problems = [];
  if (!isObject(input)) throw new InputError(['the file must contain one JSON object']);
  for (const key of Object.keys(input)) {
    if (!isNote(key) && key !== 'bonuses' && !(key in SECTIONS)) problems.push(`"${key}" is not a known section`);
  }
  const config = {};
  for (const [name, fields] of Object.entries(SECTIONS)) config[name] = readSection(input[name], name, fields, problems);
  config.hasCash = isObject(input.cash);

  config.bonuses = [];
  if (input.bonuses !== undefined && !Array.isArray(input.bonuses)) problems.push('"bonuses" must be a list');
  for (const [i, bonus] of (Array.isArray(input.bonuses) ? input.bonuses : []).entries()) {
    const where = `bonuses[${i}]`;
    if (!isObject(bonus) || !Object.hasOwn(BONUS_FIELDS, bonus.type)) {
      problems.push(`"${where}.type" must be one of: ${Object.keys(BONUS_FIELDS).join(', ')}`);
      continue;
    }
    const fields = readSection(bonus, where, BONUS_FIELDS[bonus.type], problems, ['type', 'name']);
    const name = typeof bonus.name === 'string' && bonus.name.trim() ? bonus.name : `${bonus.type} #${i + 1}`;
    config.bonuses.push({ name, type: bonus.type, ...fields });
    if (bonus.type === 'per_new_user' && config.volume.newUsers === undefined) problems.push(`"${where}" needs "volume.newUsers"`);
    if (bonus.type.startsWith('per_active_user') && config.volume.activeUsers === undefined) problems.push(`"${where}" needs "volume.activeUsers"`);
  }

  const { currency, payout, cash } = config;
  currency.redeemCoinsPerDollar ??= currency.coinsPerDollar;
  payout.averagePayoutUsd ??= payout.minimumUsd;
  if (payout.averagePayoutUsd < payout.minimumUsd) problems.push('"payout.averagePayoutUsd" cannot be below "payout.minimumUsd"');
  if (config.hasCash && (cash.outstandingCoins === undefined || cash.reserveUsd === undefined)) {
    problems.push('"cash" needs both "outstandingCoins" and "reserveUsd"');
  }
  if (problems.length) throw new InputError(problems);
  return config;
}

// Share of reversals (0 to 1) that have arrived by the given day, read off the cumulative
// curve with straight lines between points. Past the last point the curve stays flat.
export function insideHold(arrival, holdDays) {
  if (!arrival || holdDays <= 0) return 0;
  let prev = { days: 0, pct: 0 };
  for (const point of arrival) {
    if (holdDays <= point.days) {
      return (prev.pct + ((point.pct - prev.pct) * (holdDays - prev.days)) / (point.days - prev.days)) / 100;
    }
    prev = point;
  }
  return prev.pct / 100;
}

// The shortest hold, in days, at which the curve reaches the wanted percentage, or null
// when the measured curve never gets there.
export function holdDaysFor(arrival, wantedPct) {
  if (!arrival) return null;
  let prev = { days: 0, pct: 0 };
  for (const point of arrival) {
    if (wantedPct <= point.pct) {
      if (point.pct === prev.pct) return prev.days;
      return Math.ceil(prev.days + ((wantedPct - prev.pct) * (point.days - prev.days)) / (point.pct - prev.pct) - EPSILON);
    }
    prev = point;
  }
  return null;
}

const round = (value, places = 4) => (value === null || !Number.isFinite(value) ? null : Number(value.toFixed(places)));

// The core calculation. Takes the parsed JSON, returns the verdict as data.
export function checkEconomy(input) {
  const c = normalize(input);
  const revenue = c.volume.monthlyRevenueUsd;
  const reversalRate = c.reversals.ratePct / 100;
  const share = c.earning.userSharePct / 100;
  const redeemRate = c.currency.redeemCoinsPerDollar;
  // How much a coin is worth going out compared with what it cost coming in.
  const rateRatio = c.currency.coinsPerDollar / redeemRate;
  const redemption = c.payout.redemptionPct / 100;
  const target = c.targets.minMarginPct / 100;

  const within = insideHold(c.reversals.arrival, c.reversals.holdDays);
  // Part of each reversed credit that is never taken back: it arrived after the hold and
  // the balance was already gone.
  const uncollected = (1 - within) * (1 - c.reversals.lateRecoveryPct / 100);
  const standing = 1 - reversalRate * (1 - uncollected);

  let multiplier = 0;
  let referral = 0;
  let fixedCoins = 0;
  let freeCoins30 = 0;
  const bonusLines = [];
  for (const b of c.bonuses) {
    let coins = 0;
    if (b.type === 'earning_multiplier' || b.type === 'referral') {
      const part = (b.pct / 100) * (b.coveragePct / 100);
      if (b.type === 'referral') referral += part;
      else multiplier += part;
      coins = revenue * share * c.currency.coinsPerDollar * part * standing;
    } else {
      const takeUp = (b.takeUpPct ?? 100) / 100;
      if (b.type === 'per_new_user') coins = c.volume.newUsers * takeUp * b.coins;
      else if (b.type === 'per_active_user_per_day') coins = c.volume.activeUsers * DAYS_PER_MONTH * takeUp * b.coins;
      else if (b.type === 'per_active_user_per_month') coins = c.volume.activeUsers * takeUp * b.coins;
      else coins = b.coins;
      fixedCoins += coins;
      // What one account collects in its first 30 days without completing anything.
      if (b.type !== 'fixed_per_month' && !b.requiresEarning) {
        freeCoins30 += b.type === 'per_active_user_per_day' ? b.coins * DAYS_PER_MONTH : b.coins;
      }
    }
    bonusLines.push({ name: b.name, type: b.type, coinsPerMonth: round(coins, 0), usdPerMonth: round(coins / redeemRate, 2) });
  }

  const variablePerDollar = share * rateRatio * (1 + multiplier + referral);

  const netRevenue = revenue * (1 - reversalRate);
  const offerRewards = revenue * share * rateRatio * standing;
  const earningBonuses = revenue * share * rateRatio * (multiplier + referral) * standing;
  const fixedBonuses = fixedCoins / redeemRate;
  const issued = offerRewards + earningBonuses + fixedBonuses;
  const uncollectedReversals = revenue * variablePerDollar * reversalRate * uncollected;

  const feeRate = (averageUsd) => (c.payout.feePaidBy === 'app' ? c.payout.feePct / 100 + c.payout.feeFixedUsd / averageUsd : 0);
  const fee = feeRate(c.payout.averagePayoutUsd);
  const feeAtMinimum = c.payout.feePct / 100 + c.payout.feeFixedUsd / c.payout.minimumUsd;
  const otherCosts = revenue * (c.costs.otherPctOfRevenue / 100) + c.costs.fixedMonthlyUsd;
  const marginAt = (redeemed, feeUsed = fee) => netRevenue - issued * redeemed * (1 + feeUsed) - otherCosts;

  const margin = marginAt(redemption);
  const marginFull = marginAt(1);
  const marginFullWorstFee = marginAt(1, feeRate(c.payout.minimumUsd));
  const effectiveSharePct = (issued / netRevenue) * 100;
  const bonusPctOfRevenue = ((earningBonuses + fixedBonuses) / netRevenue) * 100;

  // Break-even points: each one moves a single input and leaves the rest as given.
  const payFactor = redemption * (1 + fee);
  const fixedOut = fixedBonuses * payFactor + c.costs.fixedMonthlyUsd;
  const otherPct = c.costs.otherPctOfRevenue / 100;
  const perShare = rateRatio * (1 + multiplier + referral) * standing * payFactor;
  const shareAt = (wanted) => ((revenue * (1 - reversalRate - otherPct - wanted) - fixedOut) / (revenue * perShare)) * 100;
  const variableMargin = 1 - reversalRate - share * perShare - otherPct;
  const revenueAt = (wanted) => (fixedOut <= EPSILON ? 0 : variableMargin - wanted > EPSILON ? fixedOut / (variableMargin - wanted) : null);
  const reversalDrag = 1 - variablePerDollar * payFactor * (1 - uncollected);
  const reversalAt = (wanted) => {
    if (reversalDrag <= EPSILON) return null;
    const rate = (1 - variablePerDollar * payFactor - fixedOut / revenue - otherPct - wanted) / reversalDrag;
    return rate * 100;
  };
  const headroomCoins = ((margin - target * revenue) / payFactor) * redeemRate;
  const redemptionCeiling = issued * (1 + fee) > EPSILON ? ((netRevenue - otherCosts - target * revenue) / (issued * (1 + fee))) * 100 : null;

  const smallestReward = c.earning.smallestPayoutUsd === undefined ? null : c.earning.smallestPayoutUsd * c.currency.coinsPerDollar * share;
  const roundingLossPct = smallestReward && smallestReward >= 1 ? 100 / smallestReward : null;
  const perUserMonthly = c.volume.activeUsers ? issued / c.volume.activeUsers : null;
  const daysToMinimum = perUserMonthly ? (c.payout.minimumUsd / perUserMonthly) * DAYS_PER_MONTH : null;

  const liabilityUsd = c.hasCash ? c.cash.outstandingCoins / redeemRate : null;
  const gapDays = c.hasCash && c.cash.networkPaymentDelayDays !== undefined ? Math.max(0, c.cash.networkPaymentDelayDays - c.reversals.holdDays) : null;
  const paidPerMonth = issued * redemption * (1 + fee);
  const workingCapital = gapDays === null ? null : (paidPerMonth / DAYS_PER_MONTH) * gapDays;

  const violations = [];
  const warnings = [];
  const usd = (value, places = 2) => `$${value.toLocaleString('en-US', { minimumFractionDigits: places, maximumFractionDigits: places })}`;
  const p = (value) => `${round(value, 1)}%`;
  const name = c.currency.name;

  if (marginFull < -EPSILON) {
    violations.push({
      rule: 'pays-more-than-it-earns',
      message: `If every ${name} balance is redeemed, each $1 of revenue costs ${usd(1 - marginFull / revenue, 3)}. The app has promised more than it earns.`,
    });
  }
  if (margin / revenue < target - EPSILON) {
    violations.push({
      rule: 'margin-below-target',
      message: `The expected margin is ${p((margin / revenue) * 100)} of revenue. The target is ${p(c.targets.minMarginPct)}.`,
    });
  } else if (redemption < 1 && marginFull / revenue < target - EPSILON && marginFull >= -EPSILON) {
    warnings.push({
      rule: 'margin-relies-on-unredeemed-coins',
      message: `The target margin is met only while no more than ${p(redemptionCeiling)} of ${name} are redeemed. At full redemption the margin is ${p((marginFull / revenue) * 100)}.`,
    });
  }
  if (c.targets.maxEffectiveSharePct !== undefined && effectiveSharePct > c.targets.maxEffectiveSharePct + EPSILON) {
    violations.push({
      rule: 'effective-share-over-target',
      message: `Users receive ${p(effectiveSharePct)} of the revenue that is kept once bonuses are counted. The limit is ${p(c.targets.maxEffectiveSharePct)}.`,
    });
  }
  if (c.targets.maxBonusPctOfRevenue !== undefined && bonusPctOfRevenue > c.targets.maxBonusPctOfRevenue + EPSILON) {
    violations.push({
      rule: 'bonus-budget-over-target',
      message: `Bonuses cost ${p(bonusPctOfRevenue)} of the revenue that is kept. The budget is ${p(c.targets.maxBonusPctOfRevenue)}.`,
    });
  }
  if (rateRatio > 1 + EPSILON) {
    warnings.push({
      rule: 'redeem-rate-below-earn-rate',
      message: `${c.currency.coinsPerDollar} ${name} are credited per $1 but only ${redeemRate} buy $1 at cash-out. The real user share is ${p(share * rateRatio * 100)}, not ${p(c.earning.userSharePct)}.`,
    });
  }
  if (smallestReward !== null && smallestReward < 1 - EPSILON) {
    violations.push({
      rule: 'smallest-reward-is-zero',
      message: `The smallest payout (${usd(c.earning.smallestPayoutUsd, 3)}) is worth ${round(smallestReward, 3)} ${name}, which rounds down to nothing. Raise the rate, add decimals or hide offers that small.`,
    });
  } else if (roundingLossPct !== null) {
    const limit = c.targets.maxRoundingLossPct ?? 1;
    if (roundingLossPct > limit + EPSILON) {
      (c.targets.maxRoundingLossPct === undefined ? warnings : violations).push({
        rule: 'rounding-loss',
        message: `The smallest reward is ${round(smallestReward, 2)} ${name}, so rounding down can take up to ${p(roundingLossPct)} of it. The limit is ${p(limit)}.`,
      });
    }
  }
  if (freeCoins30 / redeemRate >= c.payout.minimumUsd - EPSILON) {
    violations.push({
      rule: 'bonus-only-payout',
      message: `An account that completes nothing collects ${round(freeCoins30, 0)} ${name} in 30 days (${usd(freeCoins30 / redeemRate)}), which reaches the ${usd(c.payout.minimumUsd)} payout minimum. Lower the bonuses, raise the minimum, or release them only after real earnings.`,
    });
  }
  if (reversalRate > 0 && c.reversals.holdDays <= 0) {
    violations.push({
      rule: 'no-hold',
      message: `${p(c.reversals.ratePct)} of revenue is reversed and there is no hold, so every reversal can arrive after the payout.`,
    });
  } else if (reversalRate > 0 && !c.reversals.arrival) {
    warnings.push({
      rule: 'no-arrival-data',
      message: 'No reversal arrival curve is given, so every reversal is counted as arriving after the hold. Measure the curve from the ledger.',
    });
  }
  if (c.targets.minReversalsInsideHoldPct !== undefined && reversalRate > 0 && within * 100 < c.targets.minReversalsInsideHoldPct - EPSILON) {
    const needed = holdDaysFor(c.reversals.arrival, c.targets.minReversalsInsideHoldPct);
    violations.push({
      rule: 'hold-misses-target',
      message:
        `A ${c.reversals.holdDays} day hold catches ${p(within * 100)} of reversals. The target is ${p(c.targets.minReversalsInsideHoldPct)}` +
        (needed === null ? ', which the measured curve never reaches.' : `, which needs ${needed} days.`),
    });
  }
  if (c.payout.feePaidBy === 'user' && feeAtMinimum >= 1 - EPSILON) {
    violations.push({
      rule: 'fee-consumes-minimum-payout',
      message: `At the ${usd(c.payout.minimumUsd)} minimum the fee is ${usd(feeAtMinimum * c.payout.minimumUsd)}, so the user receives nothing.`,
    });
  }
  if (c.payout.feePaidBy === 'app' && marginFull >= -EPSILON && marginFullWorstFee < -EPSILON) {
    warnings.push({
      rule: 'fees-at-minimum-payout',
      message: `If every payout were at the ${usd(c.payout.minimumUsd)} minimum, fees would be ${p(feeAtMinimum * 100)} of each payout and the app would lose money at full redemption.`,
    });
  }
  if (c.targets.maxDaysToMinimumPayout !== undefined) {
    if (daysToMinimum === null) {
      warnings.push({ rule: 'minimum-payout-not-checked', message: 'Set "volume.activeUsers" to check how long the payout minimum takes to reach.' });
    } else if (daysToMinimum > c.targets.maxDaysToMinimumPayout + EPSILON) {
      violations.push({
        rule: 'minimum-payout-too-far',
        message: `An average active user needs about ${Math.ceil(daysToMinimum)} days to reach the ${usd(c.payout.minimumUsd)} minimum. The target is ${c.targets.maxDaysToMinimumPayout} days.`,
      });
    }
  }
  if (c.hasCash) {
    const owed = liabilityUsd * (1 + fee);
    const cover = c.cash.reserveUsd + c.cash.receivablesUsd;
    if (cover < owed - EPSILON) {
      violations.push({
        rule: 'liability-not-covered',
        message: `Users hold ${name} worth ${usd(owed)} including fees. Cash plus receivables is ${usd(cover)}.`,
      });
    }
    if (workingCapital !== null && c.cash.reserveUsd < workingCapital - EPSILON) {
      violations.push({
        rule: 'payment-gap-not-funded',
        message: `Users can cash out ${gapDays} days before the networks pay. That needs ${usd(workingCapital)} of cash, and the reserve is ${usd(c.cash.reserveUsd)}.`,
      });
    }
  } else {
    warnings.push({ rule: 'cash-not-checked', message: 'No "cash" section: the liability of unspent balances and the payment gap were not checked.' });
  }

  const perDollar = (value) => round(value / revenue);
  return {
    ok: violations.length === 0,
    currency: { name, coinsPerDollar: c.currency.coinsPerDollar, redeemCoinsPerDollar: redeemRate },
    perDollarOfRevenue: {
      keptAfterReversals: perDollar(netRevenue),
      offerRewards: perDollar(offerRewards * redemption),
      bonuses: perDollar((earningBonuses + fixedBonuses) * redemption),
      payoutFees: perDollar(issued * redemption * fee),
      otherCosts: perDollar(otherCosts),
      margin: perDollar(margin),
      marginIfEveryCoinIsRedeemed: perDollar(marginFull),
    },
    monthly: {
      revenueUsd: round(revenue, 2),
      netRevenueUsd: round(netRevenue, 2),
      issuedToUsersUsd: round(issued, 2),
      paidToUsersUsd: round(paidPerMonth, 2),
      uncollectedReversalsUsd: round(uncollectedReversals, 2),
      marginUsd: round(margin, 2),
      liabilityAddedUsd: round(issued * (1 - redemption), 2),
    },
    share: {
      nominalPct: round(c.earning.userSharePct, 2),
      effectivePct: round(effectiveSharePct, 2),
      bonusPctOfRevenue: round(bonusPctOfRevenue, 2),
    },
    bonuses: bonusLines,
    breakEven: {
      targetMarginPct: c.targets.minMarginPct,
      maxUserSharePct: round(shareAt(target), 2),
      userSharePctAtZeroMargin: round(shareAt(0), 2),
      minMonthlyRevenueUsd: round(revenueAt(target), 2),
      maxReversalRatePct: round(reversalAt(target), 2),
      bonusHeadroomCoinsPerMonth: round(headroomCoins, 0),
      maxRedemptionPct: round(redemptionCeiling, 2),
    },
    hold: {
      days: c.reversals.holdDays,
      reversalsInsidePct: round(within * 100, 2),
      daysForTarget: c.targets.minReversalsInsideHoldPct === undefined ? null : holdDaysFor(c.reversals.arrival, c.targets.minReversalsInsideHoldPct),
    },
    payout: {
      minimumUsd: c.payout.minimumUsd,
      minimumCoins: Math.ceil(c.payout.minimumUsd * redeemRate - EPSILON),
      feePctAtAveragePayout: round((c.payout.feePct / 100 + c.payout.feeFixedUsd / c.payout.averagePayoutUsd) * 100, 2),
      feePctAtMinimumPayout: round(feeAtMinimum * 100, 2),
      feePaidBy: c.payout.feePaidBy,
      daysToMinimum: daysToMinimum === null ? null : Math.ceil(daysToMinimum - EPSILON),
      bonusOnlyCoinsIn30Days: round(freeCoins30, 0),
    },
    rounding: { smallestRewardCoins: round(smallestReward, 3), worstLossPct: round(roundingLossPct, 2) },
    cash: c.hasCash
      ? {
          liabilityUsd: round(liabilityUsd, 2),
          coverUsd: round(c.cash.reserveUsd + c.cash.receivablesUsd, 2),
          paymentGapDays: gapDays,
          workingCapitalUsd: round(workingCapital, 2),
        }
      : null,
    violations,
    warnings,
  };
}

// Plain text for a terminal. Everything in it comes from the result of checkEconomy().
export function formatReport(r) {
  const usd = (value, places = 2) => {
    if (value === null) return 'n/a';
    const text = Math.abs(value).toLocaleString('en-US', { minimumFractionDigits: places, maximumFractionDigits: places });
    return `${value < 0 ? '-' : ''}$${text}`;
  };
  const pctText = (value) => (value === null ? 'n/a' : `${Number(value.toFixed(1))}%`);
  const count = (value) => (value === null ? 'n/a' : value.toLocaleString('en-US'));
  const row = (label, value, note = '') => `  ${label.padEnd(38)}${String(value).padStart(12)}${note ? `   ${note}` : ''}`;
  const d = r.perDollarOfRevenue;
  const b = r.breakEven;
  const name = r.currency.name;
  const lines = [
    `Economy check: ${name}, ${count(r.currency.coinsPerDollar)} credited per $1 of payout, ${count(r.currency.redeemCoinsPerDollar)} per $1 at cash-out`,
    '',
    'Per $1.00 of revenue',
    row('kept after reversals', usd(d.keptAfterReversals, 3)),
    row('offer rewards paid out', usd(-d.offerRewards, 3)),
    row('bonuses paid out', usd(-d.bonuses, 3)),
    row('payout fees', usd(-d.payoutFees, 3)),
    row('other costs', usd(-d.otherCosts, 3)),
    row('margin', usd(d.margin, 3), pctText(d.margin * 100)),
    row('margin if every coin is redeemed', usd(d.marginIfEveryCoinIsRedeemed, 3), pctText(d.marginIfEveryCoinIsRedeemed * 100)),
    '',
    'Paid to users',
    row('user share on each conversion', pctText(r.share.nominalPct)),
    row('effective share with bonuses', pctText(r.share.effectivePct), 'of revenue kept after reversals'),
    row('bonuses', pctText(r.share.bonusPctOfRevenue), 'of revenue kept after reversals'),
    ...r.bonuses.map((x) => row(`  ${x.name}`, usd(x.usdPerMonth), `${count(x.coinsPerMonth)} ${name} a month`)),
    '',
    `Break-even (target margin ${pctText(b.targetMarginPct)})`,
    row('highest user share', b.maxUserSharePct === null ? 'n/a' : b.maxUserSharePct < 0 ? 'none' : pctText(b.maxUserSharePct)),
    row('user share at zero margin', b.userSharePctAtZeroMargin === null ? 'n/a' : b.userSharePctAtZeroMargin < 0 ? 'none' : pctText(b.userSharePctAtZeroMargin)),
    row('lowest monthly revenue', b.minMonthlyRevenueUsd === null ? 'never' : usd(b.minMonthlyRevenueUsd)),
    row('highest reversal rate', b.maxReversalRatePct === null ? 'n/a' : b.maxReversalRatePct < 0 ? 'none' : pctText(b.maxReversalRatePct)),
    row('room for more bonuses', b.bonusHeadroomCoinsPerMonth === null ? 'n/a' : count(b.bonusHeadroomCoinsPerMonth), `${name} a month`),
    row('highest redemption', b.maxRedemptionPct === null ? 'n/a' : b.maxRedemptionPct >= 100 ? '100%' : b.maxRedemptionPct < 0 ? 'none' : pctText(b.maxRedemptionPct)),
    '',
    'Hold and payout',
    row('hold', `${r.hold.days} days`, `catches ${pctText(r.hold.reversalsInsidePct)} of reversals`),
    row('reversals never collected', usd(r.monthly.uncollectedReversalsUsd), 'a month'),
    row('payout minimum', usd(r.payout.minimumUsd), `${count(r.payout.minimumCoins)} ${name}`),
    row('days to reach it', r.payout.daysToMinimum === null ? 'n/a' : count(r.payout.daysToMinimum), 'average active user'),
    row('fee at the minimum payout', pctText(r.payout.feePctAtMinimumPayout), `paid by the ${r.payout.feePaidBy}`),
    '',
    'Unspent balances',
    row('added to the liability', usd(r.monthly.liabilityAddedUsd), 'a month, owed until redeemed or expired'),
  ];
  if (r.cash) {
    lines.push(row('owed to users now', usd(r.cash.liabilityUsd)), row('cash plus receivables', usd(r.cash.coverUsd)));
    if (r.cash.workingCapitalUsd !== null) lines.push(row('cash needed for the payment gap', usd(r.cash.workingCapitalUsd), `${r.cash.paymentGapDays} days`));
  }
  for (const [title, list] of [['Violations', r.violations], ['Warnings', r.warnings]]) {
    lines.push('', `${title} (${list.length})`);
    for (const item of list) lines.push(`  [${item.rule}] ${item.message}`);
    if (!list.length) lines.push('  none');
  }
  lines.push('', r.ok ? 'VERDICT: the economy holds.' : `VERDICT: the economy does not hold. ${r.violations.length} rule${r.violations.length === 1 ? ' is' : 's are'} violated.`);
  return lines.join('\n');
}

export function run(argv) {
  const args = argv.filter((a) => a !== '--json');
  const json = args.length !== argv.length;
  if (args.length !== 1 || args[0].startsWith('--')) throw new UsageError(USAGE);
  let text;
  try {
    text = readFileSync(args[0], 'utf8');
  } catch {
    throw new UsageError(`Cannot read the file "${args[0]}".`);
  }
  let input;
  try {
    input = JSON.parse(text);
  } catch (err) {
    throw new UsageError(`"${args[0]}" is not valid JSON: ${err.message}`);
  }
  const result = checkEconomy(input);
  return { result, output: json ? JSON.stringify(result, null, 2) : formatReport(result) };
}

function main() {
  try {
    const { result, output } = run(process.argv.slice(2));
    console.log(output);
    process.exitCode = result.ok ? 0 : 1;
  } catch (err) {
    if (!(err instanceof UsageError) && !(err instanceof InputError)) throw err;
    console.error(err.message);
    process.exitCode = 2;
  }
}

if (import.meta.url === pathToFileURL(process.argv[1] || '').href) main();
