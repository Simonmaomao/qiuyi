# 球弈 工作流手册

> 从修改到上线的标准流程 + 故障排查 + 新赛段适配

## 一、日常更新工作流

### 1. 更新比赛数据

```
比赛数据更新涉及 3 个文件:
  app/services/collector.py   → 赔率数据 (_fallback_data)
  app/services/match_data.py  → 球队/对阵/赛程
  static/index.html           → 前端比分 SP_MAP + 时间标签
```

**步骤**:

```bash
# 1. 从竞彩官网获取最新赔率
浏览器打开 https://m.sporttery.cn/mjc/jsq/zqspf/
记录每场比赛的 SPF 和 RQ 赔率

# 2. 更新 collector.py _fallback_data()
编辑 app/services/collector.py，更新赔率字典

# 3. 更新 match_data.py
编辑 app/services/match_data.py，更新 MATCH_FIDS 和 TEAM_STATS

# 4. 更新前端 index.html
编辑 static/index.html：
  - SP_MAP 比分赔率
  - labs 时间标签数组
  - 进度条阶段标记
  - 头部轮次文案

# 5. 构建 ES5 版本并部署
python3 deploy.py  # 自动 gzip+base64+TAT 推送
```

### 2. 新赛段适配清单

- [ ] `collector.py`: `_fallback_data()` 更新为新赛段队伍
- [ ] `match_data.py`: `MATCH_FIDS` → 新比赛ID
- [ ] `analyzer.py`: 按赛段调整 EV 阈值 (见下表)
- [ ] `index.html`: 进度条 + 轮次标签 + 时间
- [ ] `index.html`: `SP_MAP` 比分赔率
- [ ] `index.html`: `labs` 数组 (比赛时间)
- [ ] `data/review.json`: 上轮比分写入

### 3. ES5 检查清单

部署前必须确保 0 ES6 残留:
```bash
grep -c 'const \|let \|async \|=>' static/index.html
# 必须输出 0
```

---

## 二、部署命令速查

### 本地验证
```bash
cd ~/Desktop/ticai-smart
python3 -m uvicorn main:app --port 8899
curl http://localhost:8899/api/analysis
curl -X POST http://localhost:8899/api/plan -H 'Content-Type: application/json' -d '{"budget":500}'
```

### 远程部署 (TAT)
```python
# 单文件小文件 (<5KB .py)
python3 deploy_small.py

# HTML大文件 (需gzip)
python3 deploy_html.py
```

### 远程验证
```bash
curl http://124.220.72.141:8899/api/analysis
curl -X POST http://124.220.72.141:8899/api/plan -H 'Content-Type: application/json' -d '{"budget":500}'
```

### 远程重启
```bash
# 通过 TAT 执行
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 2
Set-Location C:\qiuyi
$env:PYTHONIOENCODING="utf-8"
Start-Process python -ArgumentList "-X","utf8","-m","uvicorn","main:app","--host","0.0.0.0","--port","8899" -NoNewWindow
```

---

## 三、故障排查

| 现象 | 诊断命令 | 常见原因 | 解决 |
|:---|:---|:---|:---|
| 页面"加载中" | `curl http://IP:8899/` | JS ES6 语法错误 | `grep 'const\|let\|=>\|async'` 检查 |
| 页面白屏 | `curl -I http://IP:8899/` | 服务未启动/GBK崩溃 | TAT 重启服务 |
| ERR_CONNECTION_REFUSED | `curl http://IP:8899/` | 进程僵死 | TAT 强杀+重启 |
| 方案为空 | `curl -X POST ../api/plan` | EV阈值过高 | 按赛段下调 min_ev |
| API 500 | `curl http://IP:8899/api/analysis` | 后端 import 错误 | 服务器 `pip install` 缺失包 |
| 服务启动但无数据 | 同上 | `_fallback_data` 为空 | 检查 collector.py |
| 比分推荐错误 | 看浏览器控制台 | `SP_MAP` 键名不匹配 | 对比 match_data 队伍名 |

---

## 四、EV 阈值速查

| 赛段 | 对阵数 | min_ev | core > | value 范围 |
|:---|:---:|:---:|:---:|:---:|
| 小组赛 | 48 | 0.80 | 0.82 | 0.78-0.82 |
| 1/8 | 8 | 0.80 | 0.82 | 0.78-0.82 |
| 1/4 | 4 | 0.68 | 0.70 | 0.65-0.70 |
| 半决赛 | 2 | 0.55 | 0.58 | — |
| 决赛 | 1 | 0.50 | 0.53 | — |

修改位置: `app/core/analyzer.py` L152 (min_ev), L185-187 (core/value/fun)

---

## 五、服务器信息

| 项目 | 值 |
|:---|:---|
| IP | 124.220.72.141 |
| 端口 | 8899 |
| 目录 | C:\qiuyi\ |
| 实例ID | lhins-g139mvmy |
| 地域 | ap-shanghai |
| Python | 3.8 |
| 启动 | uvicorn main:app --host 0.0.0.0 --port 8899 |

---

## 六、自动化

- **cron**: 每日 10:00 / 18:00 自动更新数据
- **技能**: `qiuyi-deploy` (Hermes skill)
- **仓库**: github.com/Simonmaomao/qiuyi
