"""比赛数据 - 最新体彩官网 2026-07-06"""
from typing import List, Dict

# 世界杯1/8决赛剩余场次
MATCH_FIDS = {
    "葡萄牙vs西班牙": 1359173,
    "美国vs比利时": 1359180,
    "阿根廷vs埃及": 1359183,
    "瑞士vs哥伦比亚": 1359186,
}

MATCH_RESULTS = []

TEAM_STATS = {
    "葡萄牙": {"gf": 2, "ga": 1},
    "西班牙": {"gf": 3, "ga": 0},
    "美国": {"gf": 2, "ga": 0},
    "比利时": {"gf": 3, "ga": 2},
    "阿根廷": {"gf": 3, "ga": 2},
    "埃及": {"gf": 5, "ga": 3},
    "瑞士": {"gf": 2, "ga": 0},
    "哥伦比亚": {"gf": 1, "ga": 0},
}

MARKET_PROBS = {}

DEVIATION_ANALYSIS = {}
