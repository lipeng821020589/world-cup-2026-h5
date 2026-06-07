// pages/groups/groups.js
const teams = require('../../data/teams.js');
const predictions = require('../../data/predictions.js');
const deathGroups = require('../../data/death_groups.js');
const teamsList = require('../../data/teams_list.js');

const LETTERS = 'ABCDEFGHIJKL'.split('');

function flagOf(name) {
  return teamsList.find(t => t.name === name)?.flag || '🏳';
}

function buildGroupCards() {
  const deathLetters = new Set(deathGroups.map(d => d.letter));
  return LETTERS.map(letter => {
    const info = teams.groups[letter];
    const ranks = predictions[letter]; // [[name, score], ...]
    return {
      letter,
      seed: info.seed,
      seed_flag: flagOf(info.seed),
      host: info.host || null,
      death: deathLetters.has(letter),
      teams: ranks.map(([name, score], i) => ({
        name,
        flag: flagOf(name),
        score,
        qual: i < 2,
      })),
    };
  });
}

Page({
  data: {
    cards: buildGroupCards(),
  },
  
  goToDetail(e) {
    const letter = e.currentTarget.dataset.letter;
    wx.navigateTo({ url: `/pages/group-detail/group-detail?letter=${letter}` });
  },
});
