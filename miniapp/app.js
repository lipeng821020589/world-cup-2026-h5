// app.js - 小程序入口
App({
  onLaunch() {
    // 启动日志
    console.log('🏆 2026 世界杯小程序启动');
    
    // 获取系统信息
    const sysInfo = wx.getSystemInfoSync();
    this.globalData.statusBarHeight = sysInfo.statusBarHeight;
    this.globalData.windowWidth = sysInfo.windowWidth;
    
    // 启动时立即更新倒计时
    this.updateCountdown();
    
    // 每分钟更新倒计时
    this.countdownTimer = setInterval(() => {
      this.updateCountdown();
    }, 60000);
  },
  
  onShow() {
    this.updateCountdown();
  },
  
  onHide() {
    // 不清 timer，隐藏也继续算
  },
  
  updateCountdown() {
    const targets = require('./data/countdown_targets.js');
    const now = Date.now();
    this.globalData.countdowns = targets.map(t => {
      const target = new Date(t.date).getTime();
      const diff = Math.max(0, target - now);
      const days = Math.floor(diff / 86400000);
      const hours = Math.floor((diff % 86400000) / 3600000);
      const mins = Math.floor((diff % 3600000) / 60000);
      return {
        id: t.id,
        name: t.name,
        days, hours, mins,
        total_seconds: Math.floor(diff / 1000),
        past: diff <= 0,
      };
    });
  },
  
  globalData: {
    statusBarHeight: 20,
    windowWidth: 375,
    countdowns: [],
  }
});
