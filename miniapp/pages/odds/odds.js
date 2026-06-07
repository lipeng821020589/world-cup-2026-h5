// pages/odds/odds.js
const odds = require('../../data/odds_baseline.js');
const teamsList = require('../../data/teams_list.js');
const monteCarlo = require('../../data/monte_carlo.js');
const format = require('../../utils/format.js');

function buildOddsList() {
  return Object.entries(odds)
    .filter(([k]) => !k.startsWith('_'))
    .map(([team, dec]) => {
      const t = teamsList.find(x => x.name === team);
      const implied = (1 / dec) * 100;
      const myProb = (monteCarlo.final4_prob[team] || 0) / 100; // 简化
      const value = myProb / (1 / dec);
      return {
        team,
        flag: t?.flag || '🏳',
        score: t?.score || 0,
        dec: dec.toFixed(2),
        american: format.decimalToAmerican(dec),
        implied: implied.toFixed(1),
        myProb: (myProb * 100).toFixed(1),
        value: value.toFixed(2),
        valueMark: value > 1.0 ? '🟢' : value > 0.7 ? '🟡' : '🔴',
        tier: t?.tier || 'T4',
      };
    })
    .sort((a, b) => a.dec - b.dec);
}

Page({
  data: {
    oddsList: buildOddsList(),
    championProb: Object.entries(monteCarlo.champion_prob)
      .map(([name, prob]) => ({ name, prob, flag: teamsList.find(t => t.name === name)?.flag || '🏳' }))
      .sort((a, b) => b.prob - a.prob),
  },
});
