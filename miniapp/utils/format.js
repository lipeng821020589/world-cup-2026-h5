// utils/format.js - 通用工具
function tierFromScore(score) {
  if (score >= 88) return 'T1';
  if (score >= 78) return 'T2';
  if (score >= 65) return 'T3';
  return 'T4';
}

function tierLabel(tier) {
  return {
    T1: '🏆 争冠',
    T2: '🥈 半决赛',
    T3: '🥉 16 强',
    T4: '🐎 搅局',
  }[tier] || tier;
}

function decimalToAmerican(dec) {
  if (dec < 2.0) return Math.round(-100 / (dec - 1));
  return '+' + Math.round(100 * (dec - 1));
}

function formatDate(dateStr) {
  // '2026-06-11' -> '6/11'
  const m = dateStr.match(/2026-(\d{2})-(\d{2})/);
  return m ? `${parseInt(m[1])}/${parseInt(m[2])}` : dateStr;
}

function getTimeOfDay() {
  const h = new Date().getHours();
  if (h < 6) return '凌晨';
  if (h < 12) return '上午';
  if (h < 18) return '下午';
  return '晚上';
}

module.exports = {
  tierFromScore,
  tierLabel,
  decimalToAmerican,
  formatDate,
  getTimeOfDay,
};
