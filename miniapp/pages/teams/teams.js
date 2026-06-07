// pages/teams/teams.js
const teamsList = require('../../data/teams_list.js');

const TIER_NAMES = { T1: 'T1 争冠', T2: 'T2 半决赛', T3: 'T3 16 强', T4: 'T4 搅局' };

Page({
  data: {
    activeTier: 'ALL',
    tiers: [
      { key: 'ALL', label: '全部' },
      { key: 'T1', label: '🏆 T1' },
      { key: 'T2', label: '🥈 T2' },
      { key: 'T3', label: '🥉 T3' },
      { key: 'T4', label: '🐎 T4' },
    ],
    teams: [],
  },
  
  onLoad() {
    this.filter('ALL');
  },
  
  filter(e) {
    const tier = (typeof e === 'string' ? e : e.currentTarget.dataset.tier);
    const teams = (tier === 'ALL' ? teamsList : teamsList.filter(t => t.tier === tier))
      .sort((a, b) => b.score - a.score)
      .map(t => ({
        ...t,
        tier_label: TIER_NAMES[t.tier] || t.tier,
      }));
    this.setData({ activeTier: tier, teams });
  },
  
  goDetail(e) {
    const name = e.currentTarget.dataset.name;
    wx.navigateTo({ url: `/pages/team-detail/team-detail?name=${encodeURIComponent(name)}` });
  },
});
