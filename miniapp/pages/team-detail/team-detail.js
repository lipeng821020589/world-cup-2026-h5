// pages/team-detail/team-detail.js
const squads = require('../../data/squads.js');
const teamsList = require('../../data/teams_list.js');
const teams = require('../../data/teams.js');
const predictions = require('../../data/predictions.js');

function findGroup(name) {
  for (const letter of 'ABCDEFGHIJKL') {
    if (teams.groups[letter].teams.includes(name)) return letter;
  }
  return null;
}

Page({
  data: {},
  
  onLoad(options) {
    const name = decodeURIComponent(options.name);
    const teamInfo = teamsList.find(t => t.name === name);
    const players = (squads.teams[name] || []).map(p => ({
      ...p,
      flag_emojis: (p.key || '').split('').filter(c => /[\u{1F300}-\u{1F9FF}]|⭐|👋|🆕|🏥/u.test(c)).join(' '),
    }));
    const letter = findGroup(name);
    const ranks = predictions[letter] || [];
    const groupStandings = ranks.map(([n, s]) => ({
      name: n,
      flag: teamsList.find(t => t.name === n)?.flag || '🏳',
      score: s,
      is_self: n === name,
    }));
    const myIndex = ranks.findIndex(([n]) => n === name);
    
    this.setData({
      name,
      flag: teamInfo?.flag || '🏳',
      score: teamInfo?.score || 0,
      tier: teamInfo?.tier || 'T4',
      group: letter,
      group_seed: teams.groups[letter]?.seed,
      group_debut: teams.groups[letter]?.debut || [],
      players,
      groupStandings,
      myRank: myIndex + 1,
    });
    
    wx.setNavigationBarTitle({ title: name });
  },
});
