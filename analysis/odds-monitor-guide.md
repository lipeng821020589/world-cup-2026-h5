# 赔率监控指南 (Odds Monitor Guide)

> 监控脚本：`scripts/odds_monitor.py`  
> 基线数据：`data/odds_baseline.json`  
> 历史快照：`data/odds_history.jsonl`  
> 报警频率：每 4 小时（早 8 / 中 12 / 下午 4 / 晚 8）  
> 报警阈值：赔率变化 > 5%  
> 报警渠道：当前会话（weixin / 飞书）

---

## 🎯 工作流

```
   4h 周期: 8:00 → 12:00 → 16:00 → 20:00
        ↓
   cron 触发 (systemEvent)
        ↓
   main session 跑 odds_monitor.py
        ↓
   抓取赔率 (the-odds-api 优先 → 回退 baseline)
        ↓
   对比上次 (JSONL 末条)
        ↓
   变化 > 5% ? ──── 是 ───→ message 工具发微信
        │                    格式: 简报 + 解读
        └─── 否 ───→ 静默
```

## 🚀 用法

### 1. 首次设置（已完成）
```bash
cd /Work/world-cup-2026
python3 scripts/odds_monitor.py   # 创建 baseline + 首次历史
```

### 2. 手动更新赔率
你看到某博彩公司的新赔率后，告诉我即可。我会：
- 更新 `data/odds_baseline.json`
- 重跑监控，输出变化

或者你自己执行：
```bash
# 编辑 baseline
nano /Work/world-cup-2026/data/odds_baseline.json
# 重跑监控
python3 /Work/world-cup-2026/scripts/odds_monitor.py
```

### 3. 用真实 API（the-odds-api.com）
注册免费 key（500 calls/月）后：
```bash
export ODDS_API_KEY=your_key_here
python3 scripts/odds_monitor.py --api-key $ODDS_API_KEY
```

### 4. 自定义报警阈值
```bash
# 更严格：> 2% 就报
python3 scripts/odds_monitor.py --threshold 2
# 更宽松：> 10% 才报
python3 scripts/odds_monitor.py --threshold 10
```

## 📊 赔率变化方向解读

| 变化 | 含义 | 市场信号 |
|------|------|---------|
| 📉 赔率下降 | 隐含概率上升 | 博彩公司更看好，**钱流入** |
| 📈 赔率上升 | 隐含概率下降 | 博彩公司不看好，**钱流出** |
| ➡️ 不变 | 无人下注 | 维持现状 |

**例**：
- 法国：6.50 → 5.50（↓ 15.4%）= 赔率跌 15%，市场更看好
- 摩洛哥：51 → 26（↓ 49%）= 摩洛哥夺冠概率 1.9% → 3.8%，市场大热

## 📈 历史数据用途

`data/odds_history.jsonl` 每行一条记录：
```json
{
  "timestamp": "2026-06-06T21:26:31",
  "source": "baseline",
  "odds": {"Argentina": 6.50, ...},
  "changes_from_prev": [...]
}
```

**后续可做的分析**：
- 📉 画每队赔率走势图（matplotlib）
- 🔍 检测"反向操作"信号（赔率下降但实际实力未变 → 内部消息泄漏）
- 📊 找市场情绪最一致的 5 队（赔率变化方向一致）

## 🛠 故障排查

| 现象 | 原因 | 解决 |
|------|------|------|
| 脚本找不到 baseline | 首次未运行 | 跑 `python3 scripts/odds_monitor.py` |
| 历史文件损坏 | 多次崩溃 | 删除 `data/odds_history.jsonl` 重跑 |
| 监控无变化但实际赔率动了 | 用的还是旧 baseline | 用 `--update` 强制更新 |
| API 401 | 没 key / key 失效 | 改用 baseline 模式（不传 --api-key） |
| 微信没收到报警 | weixin 消息被屏蔽 | 看 main session 输出，报警有发但被吞 |

## 📅 揭幕前时间线

| 日期 | 事件 | 监控频率 |
|------|------|---------|
| 6/7-6/10 | 揭幕前最后 4 天 | 4h 一次（已设） |
| 6/11 揭幕 | 墨西哥 vs 南非 | 改为 1h 一次 |
| 6/11-6/26 小组赛 | 48 进 32 | 1h 一次 |
| 6/27-7/4 淘汰赛首轮 | 16 强 → 8 强 | 30min 一次 |
| 7/5-7/15 8 强→决赛 | 4 强 | 30min 一次 |
| 7/19 决赛 | 阿根廷 vs 法国？ | 实时 |

**注意**：小组赛期间**单场赔率**比**夺冠赔率**更重要。要不要加单场监控？

## 💡 进阶功能

### 套利检测
如果同一队在不同博彩公司赔率差 > 5%，存在套利空间。脚本已留 hook。

### 关键日期提醒
```python
# 在 main() 加
if datetime.now() == '2026-06-11 14:00:00':
    send('🏆 揭幕战 5 小时后！墨西哥 vs 南非')
```

### 大额下注预警
赔率突然跌 30%+ 通常是大额下注信号，要警惕"假赔率"（博彩公司试探市场）。

## 📁 相关文件

- `scripts/odds_monitor.py` — 主脚本
- `scripts/odds_tracker.py` — 静态分析 + 价值计算
- `data/odds_baseline.json` — 当前赔率基线
- `data/odds_history.jsonl` — 历史快照
- `analysis/odds-baseline.md` — 静态基线文档
- `reports/odds-monitor-*.txt` — 每次跑的报告
- `reports/odds-analysis-*.txt` — 价值分析报告
