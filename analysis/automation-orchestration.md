# 2026 世界杯自动化编排 (TaskFlow + Cron)

> 整合 cron 3 个任务为一个 TaskFlow 作业
> 创建于 2026-06-07

## 🎯 总目标

**owner session = main (openclaw-weixin)**  
**trigger 模式 = cron (每日 02:00 + 揭幕战前 21h + 比赛日 5min)**  
**return = 微信汇报**

## 📊 流程图

```
┌─────────────────────────────────────────────────┐
│  0. main session (主)                            │
│     - 微信渠道 openclaw-weixin                   │
│     - accountId: 29af01ca3c16-im-bot             │
└─────────────────────────────────────────────────┘
                      ↓
   ┌──────────────────┼──────────────────┐
   ↓                  ↓                  ↓
┌─────────┐     ┌─────────┐      ┌─────────┐
│ Cron 1  │     │ Cron 2  │      │ Cron 3  │
│ 02:00   │     │ 6/11 12:00│    │ 6/12 起 │
│ 每日    │     │ 一次性  │      │ 每5分钟 │
│ 赛程更新│     │ 揭幕提醒│      │ 比分监控│
└─────────┘     └─────────┘      └─────────┘
   ↓                  ↓                  ↓
┌─────────────────────────────────────────────────┐
│  1. TaskFlow: worldcup-data-pipeline             │
│     controllerId: worldcup-2026/pipeline         │
│     goal: 维持 H5 实时可用 + 推送通知            │
└─────────────────────────────────────────────────┘
                      ↓
   ┌──────────────────┼──────────────────┐
   ↓                  ↓                  ↓
fetch_fixtures   push_to_github    notify_weixin
   ↓                  ↓                  ↓
   └──── save JSON ───┴── git push ────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  2. stateJson (持久化)                           │
│     lastFixturesUpdate: "2026-06-07T..."         │
│     liveMatches: [{home, away, score, status}]   │
│     notifSent: ["6/11 12:00"]                    │
└─────────────────────────────────────────────────┘
```

## 🛠 三个 Cron (已落地)

### Cron 1: 每日 02:00 赛程更新
- **id**: `457d621f-6bee-4f14-be81-e93b017773eb`
- **session**: isolated (独立 session)
- **流程**:
  1. `python3 fetch_real_fixtures.py` → 更新 `data/fixtures_2026.json`
  2. 复制到 `miniapp-h5/` 和 `/tmp/h5-deploy/`
  3. `git push` 到公网
  4. 微信汇报"✅ 赛程已更新 (N 场)"

### Cron 2: 揭幕战倒计时 21h
- **id**: `ef338446-b717-4318-b9d0-eab92af37a7f`
- **at**: 2026-06-11T12:00:00+08:00
- **deleteAfterRun**: true (一次性)
- **流程**: 推送揭幕战情报到微信

### Cron 3: 比赛日实时比分
- **id**: `0b06193c-c238-4419-9450-2d8f1b57adc2`
- **every**: 300000ms (5min)
- **anchor**: 2026-06-12T00:00:00Z (6/12 08:00 北京)
- **流程**:
  1. fetch 赛程
  2. 过滤 `status != 'NS'`
  3. 有 LIVE/FT → 推 + 微信
  4. 无 → 静默

## 🔁 TaskFlow 数据流 (概念)

```typescript
// 伪代码 - 实际用 cron trigger + 共享 data/fixtures_2026.json
flow.createManaged({
  controllerId: "worldcup-2026/pipeline",
  goal: "实时赛程 + 比分推送",
  stateJson: {
    lastUpdate: null,
    liveMatches: [],
    notifLog: [],
  }
});

// 子任务: fetch_fixtures
flow.runTask({ name: "fetch_fixtures", runtime: "shell" });

// 子任务: push_to_github  
flow.runTask({ name: "push_to_github", runtime: "shell" });

// 子任务: notify_weixin (条件触发)
flow.runTask({ name: "notify_weixin", condition: "has_live" });

// 失败处理
flow.setWaiting({ reason: "network_error" });
```

## 📋 当前 active jobs (6/7 15:46)

| 名称 | 下次运行 | 状态 |
|------|---------|------|
| 赛程每日更新 | 6/8 02:00 | enabled |
| 揭幕战倒计时 | 6/11 12:00 | enabled |
| 比赛日实时比分 | 6/12 08:00 | enabled |
| 赔率变动提醒 (4h) | 6/7 20:00 | enabled (原) |
| CIRCT 死活 | 每 30 min | enabled (原) |
| 英语学习 (3) | - | enabled (原) |

## 🎯 优化建议

1. **共享 stateJson**: 把 liveMatches/notifLog 写到 `data/state.json` (3 个 cron 都读)
2. **fail-safe**: fetch 失败时用上次的 fixtures (不要清空)
3. **多渠道**: 同时推飞书 / 微信 / 邮件 (不只是微信)
4. **deadline**: 7/20 决赛后所有 cron 自动禁用
