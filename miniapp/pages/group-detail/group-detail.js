// pages/group-detail/group-detail.js
const teams = require('../../data/teams.js');
const squads = require('../../data/squads.js');
const predictions = require('../../data/predictions.js');
const deathGroups = require('../../data/death_groups.js');
const teamsList = require('../../data/teams_list.js');

function flagOf(name) {
  return teamsList.find(t => t.name === name)?.flag || '🏳';
}

function scoreOf(name) {
  return predictions[Object.keys(predictions).find(l => predictions[l].some(([n]) => n === name))][
    predictions[Object.keys(predictions).find(l => predictions[l].some(([n]) => n === name))]
      .findIndex(([n]) => n === name)
  ][1];
}

function topPlayers(team, n=3) {
  const all = squads.teams[team] || [];
  const starred = all.filter(p => (p.key || '').includes('⭐'));
  return (starred.length ? starred : all).slice(0, n);
}

function predictMatch(t1, t2) {
  const s1 = scoreOf(t1);
  const s2 = scoreOf(t2);
  const gap = Math.abs(s1 - s2);
  if (gap >= 15) return s1 > s2 ? `${t1} 大胜在望` : `${t2} 大胜在望`;
  if (gap >= 5) return s1 > s2 ? `${t1} 略胜一筹` : `${t2} 略胜一筹`;
  return '🔥 势均力敌';
}

function buildMatchups(teamList) {
  if (teamList.length !== 4) return [];
  // A1vA2, A3vA4, A1vA3, A2vA4, A1vA4, A2vA3
  return [
    [teamList[0], teamList[1]],
    [teamList[2], teamList[3]],
    [teamList[0], teamList[2]],
    [teamList[1], teamList[3]],
    [teamList[0], teamList[3]],
    [teamList[1], teamList[2]],
  ].map(([t1, t2], i) => ({
    id: i + 1,
    t1, t1_flag: flagOf(t1), t1_score: scoreOf(t1),
    t2, t2_flag: flagOf(t2), t2_score: scoreOf(t2),
    verdict: predictMatch(t1, t2),
  }));
}

Page({
  data: {},
  
  onLoad(options) {
    const letter = options.letter;
    const info = teams.groups[letter];
    const ranks = predictions[letter];
    const deathInfo = deathGroups.find(d => d.letter === letter);
    
    const teamDetails = ranks.map(([name, score], i) => ({
      name,
      flag: flagOf(name),
      score,
      qual: i < 2,
      tier_label: score >= 88 ? 'T1 争冠' : score >= 78 ? 'T2 半决赛' : score >= 65 ? 'T3 16 强' : 'T4 搅局',
      players: topPlayers(name, 3).map(p => ({
        name: p.name, pos: p.pos, club: p.club, age: p.age,
        key: p.key, notes: p.notes,
      })),
    }));
    
    const matchups = buildMatchups(ranks.map(([n]) => n));
    
    this.setData({
      letter,
      seed: info.seed,
      seed_flag: flagOf(info.seed),
      host: info.host || null,
      debut: info.debut || [],
      death: !!deathInfo,
      death_reason: deathInfo?.reason || '',
      teams: teamDetails,
      matchups,
    });
    
    wx.setNavigationBarTitle({ title: `Group ${letter}` });
  },
});
