# 2026 世界杯微信小程序 - 实施计划

## 🎯 目标

把 `/Work/world-cup-2026` 的数据 + 预测，封装成微信小程序，让手机随时看。

## 📦 我能交付的（无需 AppID/服务器）

| 项 | 状态 |
|----|------|
| 完整小程序源码（4 个页面 + 数据层） | ✅ |
| 本地 H5 预览版（浏览器可看） | ✅ |
| 数据导出（小程序可直接 import 的 JSON） | ✅ |
| 微信开发者工具导入说明 | ✅ |
| 截图预览 | ✅ |

## 🚧 用户需要做的（必须）

| 步骤 | 说明 |
|------|------|
| 1. 下载微信开发者工具 | https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html |
| 2. 注册小程序 AppID | https://mp.weixin.qq.com/（个人订阅号也行） |
| 3. 导入项目 | 选 `/Work/world-cup-2026/miniapp/` 目录 |
| 4. 真机预览 | 工具里点"预览"扫码 |

## 🏗️ 架构

```
miniapp/
├── app.js                    # 小程序入口
├── app.json                  # 全局配置
├── app.wxss                  # 全局样式
├── project.config.json       # 开发者工具配置
├── sitemap.json              # SEO
│
├── pages/                    # 4 个页面
│   ├── index/                # 首页（揭幕倒计时 + 焦点）
│   ├── groups/               # 12 小组列表
│   ├── group-detail/         # 小组详情（动态 ID）
│   ├── teams/                # 48 队列表
│   ├── team-detail/          # 球队详情（动态 ID）
│   └── odds/                 # 赔率监控
│
├── components/               # 复用组件
│   └── countdown/            # 倒计时组件
│
├── data/                     # 静态数据 (从 world-cup-2026/data 复制)
│   ├── teams.js
│   ├── squads.js
│   ├── venues.js
│   ├── matches.js
│   └── groups.js             # 12 份生成的小组分析
│
└── utils/                    # 工具
    └── format.js
```

## 🎨 页面设计

### 首页 (index)
- 顶部：揭幕战倒计时（大字）
- 中部：今日比赛 / 下一场
- 下部：冠军预测 TOP 3（柱状图）
- 底部：底部导航（首页 / 小组 / 球队 / 赔率）

### 小组列表 (groups)
- 12 个卡片，按 A-L 排列
- 每个卡片：组名 + 4 队旗帜 + 出线预测
- 点击进详情

### 小组详情 (group-detail)
- 4 队实力对比
- 6 场对决预测
- 关键球员
- 关注点

### 球队详情 (team-detail)
- 球队信息
- 实力分 + 档位
- 5 大关键球员
- 同组对手

### 赔率 (odds)
- 夺冠赔率 TOP 20
- 价值分析（凯利）
- 死亡之组 + 黑马
