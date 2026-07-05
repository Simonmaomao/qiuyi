"""FastAPI 服务 - 自动更新"""
import json
import threading
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

from app.services.collector import DataCollector, MATCH_FIDS
from app.core.analyzer import AnalysisEngine
from app.services.match_data import MATCH_RESULTS, TEAM_STATS, MARKET_PROBS, DEVIATION_ANALYSIS
from app.services.cache import DataCache

app = FastAPI(title="球弈", version="3.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

collector = DataCollector()
engine = AnalysisEngine()
cache = DataCache()

class PlanRequest(BaseModel):
    budget: float = 500

class BrowserData(BaseModel):
    matches: list

# ===== 后台自动更新 =====

@app.get("/api/matches")
def get_matches():
    """获取所有比赛赔率"""
    try:
        matches = collector.fetch_ticai()
        # 如果有浏览器更新的数据, 使用缓存
        cached = cache.get_data()
        if cached and cached.get('matches'):
            matches = cached['matches']
        return {"success": True, "data": matches, "updated": cached.get('date','') if cached else ''}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/browser-update")
def browser_update(data: BrowserData):
    """从浏览器更新数据"""
    cache.update_from_browser(data.matches)
    return {"success": True, "date": cache._data.get('date','')}

@app.get("/api/cache-status")
def cache_status():
    """缓存状态"""
    c = cache.get_data()
    return {
        "success": True,
        "matches_count": len(c.get('matches',[])) if c else 0,
        "last_update": c.get('date','') if c else '无',
        "age_seconds": int(time.time() - c.get('timestamp',0)) if c else -1,
    }

@app.get("/api/analysis")
def get_analysis():
    """获取所有比赛分析"""
    matches = collector.fetch_ticai()
    if not matches:
        return {"success": False, "error": "暂无比赛数据"}
    
    results = []
    for m in matches:
        key = f"{m['home']}vs{m['away']}"
        fid = MATCH_FIDS.get(key)
        market_odds = None
        if fid:
            market_odds = collector.fetch_odds_500(fid)
        
        if not market_odds:
            # 使用默认近似值
            h = 1.0 / (m['spf_sp'][0] * 0.65) if m['spf_sp'][0] > 0 else 2.0
            d = 1.0 / (m['spf_sp'][1] * 0.65) if m['spf_sp'][1] > 0 else 3.0
            a = 1.0 / (m['spf_sp'][2] * 0.65) if m['spf_sp'][2] > 0 else 4.0
            total = h + d + a
            market_odds = [1/h*total, 1/d*total, 1/a*total]
        
        analysis = engine.analyze_match(m, market_odds)
        results.append(analysis)
    
    results.sort(key=lambda x: -x['score'])
    return {"success": True, "data": results}

@app.post("/api/plan")
def get_plan(req: PlanRequest):
    """生成投注方案"""
    resp = get_analysis()
    if not resp.get("success") or not resp.get("data"):
        return {"success": False, "error": "无法生成方案"}
    
    plan = engine.generate_plan(resp["data"], req.budget)
    return {"success": True, "data": plan}

@app.get("/api/champion")
def get_champion():
    """夺冠赔率分析"""
    odds = collector.fetch_champion_odds()
    if not odds:
        return {"success": False, "error": "暂无数据"}
    
    total_prob = sum(1/o['sp'] for o in odds)
    results = []
    for o in odds:
        results.append({
            'team': o['team'],
            'sp': o['sp'],
            'implied_prob': round(1/o['sp']*100, 1),
            'fair_prob': round(1/o['sp']/total_prob*100, 1) if total_prob > 0 else 0
        })
    results.sort(key=lambda x: x['sp'])
    return {"success": True, "data": results}

@app.get("/api/champion-deep")
def get_champion_deep():
    """夺冠深度分析: 进决赛概率+夺冠概率+决赛对阵"""
    # 数据
    final_prob = {
        "法国": 0.50, "阿根廷": 0.22, "巴西": 0.15, "西班牙": 0.12,
        "英格兰": 0.10, "哥伦比亚": 0.06, "葡萄牙": 0.04, "摩洛哥": 0.03,
        "美国": 0.03, "比利时": 0.03, "墨西哥": 0.02, "挪威": 0.02,
        "瑞士": 0.02, "埃及": 0.01
    }
    final_win = {
        "法国": 0.55, "阿根廷": 0.42, "西班牙": 0.45, "巴西": 0.40,
        "英格兰": 0.35, "哥伦比亚": 0.20, "葡萄牙": 0.30, "摩洛哥": 0.15,
        "美国": 0.15, "比利时": 0.25, "墨西哥": 0.20, "挪威": 0.15,
        "瑞士": 0.15, "埃及": 0.05
    }
    odds_map = {"法国":2.40,"阿根廷":6.00,"西班牙":6.25,"英格兰":8.00,"巴西":9.75,
                "葡萄牙":10.50,"摩洛哥":24.00,"美国":25.00,"哥伦比亚":30.00,
                "比利时":35.00,"墨西哥":35.00,"挪威":45.00,"瑞士":47.00,"埃及":350.00}
    
    # 各队分析
    teams = []
    for team, fp in sorted(final_prob.items(), key=lambda x: -x[1]):
        fw = final_win[team]
        champ = round(fp * fw * 100, 1)
        implied = round(1/odds_map[team]*100, 1)
        teams.append({
            "team": team, "sp": odds_map[team],
            "final_prob": round(fp*100, 1),
            "final_win_rate": round(fw*100, 1),
            "champion_prob": champ,
            "implied_prob": implied,
            "value": round(champ - implied, 1),
            "emoji": {"法国":"🇫🇷","阿根廷":"🇦🇷","西班牙":"🇪🇸","英格兰":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","巴西":"🇧🇷",
                     "葡萄牙":"🇵🇹","摩洛哥":"🇲🇦","美国":"🇺🇸","哥伦比亚":"🇨🇴","比利时":"🇧🇪",
                     "墨西哥":"🇲🇽","挪威":"🇳🇴","瑞士":"🇨🇭","埃及":"🇪🇬"}.get(team, "")
        })
    
    # 可能决赛对阵
    upper = ["法国","西班牙","葡萄牙","摩洛哥","美国","比利时"]
    lower = ["阿根廷","巴西","英格兰","哥伦比亚","墨西哥","挪威","瑞士","埃及"]
    finals = []
    for u in upper:
        for l in lower:
            prob = final_prob[u] * final_prob[l]
            if prob > 0.01:
                finals.append({
                    "final": f"{u} vs {l}",
                    "prob": round(prob*100, 1),
                    "upper": u, "lower": l
                })
    finals.sort(key=lambda x: -x['prob'])
    
    return {"success": True, "data": {
        "teams": teams,
        "top_finals": finals[:8]
    }}

@app.get("/api/schedules")
def get_schedules():
    """赛程赛果"""
    data = collector.fetch_schedules()
    return {"success": True, "data": data}

@app.get("/api/results")
def get_results():
    """全部赛果"""
    return {"success": True, "data": MATCH_RESULTS}

@app.get("/api/team-stats")
def get_team_stats():
    """球队数据"""
    return {"success": True, "data": TEAM_STATS}

@app.get("/api/market-bias")
def get_market_bias():
    """体彩vs市场偏差"""
    return {"success": True, "data": DEVIATION_ANALYSIS}

@app.get("/")
def index():
    return FileResponse("static/index.html")

app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8899)
