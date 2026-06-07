// pages/index/index.js - 首页
const app = getApp();
const events = require('../../data/events.js');
const monteCarlo = require('../../data/monte_carlo.js');
const deathGroups = require('../../data/death_groups.js');
const predictions = require('../../data/predictions.js');
const teamsList = require('../../data/teams_list.js');
const format = require('../../utils/format.js');

Page({
  data: {
    countdowns: [],
    nextEvent: null,
    championProb: [],
    deathGroups: [],
    todayMatches: [],
    topPick: '',
  },
  
  onShow() {
    this.refresh();
  },
  
  refresh() {
    const countdowns = app.globalData.countdowns;
    const nextEvent = countdowns.find(c => !c.past) || countdowns[0];
    
    // 冠军概率降序
    const championProb = Object.entries(monteCarlo.champion_prob)
      .map(([name, prob]) => ({
        name,
        prob,
        flag: teamsList.find(t => t.name === name)?.flag || '🏳',
        bar_width: prob * 2, // 用于进度条
      }))
      .sort((a, b) => b.prob - a.prob);
    
    // 今日/明日比赛
    const matches = require('../../data/matches.js');
    const today = '2026-06-12';
    const todayMatches = (matches.key_matches || []).filter(m => m.date === today);
    
    this.setData({
      countdowns,
      nextEvent,
      championProb,
      deathGroups: deathGroups.slice(0, 3),
      todayMatches,
      topPick: monteCarlo.most_likely_champion,
    });
  },
  
  goToGroup(e) {
    const letter = e.currentTarget.dataset.letter;
    wx.navigateTo({
      url: `/pages/group-detail/group-detail?letter=${letter}`,
    });
  },
  
  goToOdds() {
    wx.switchTab({ url: '/pages/odds/odds' });
  },
});
