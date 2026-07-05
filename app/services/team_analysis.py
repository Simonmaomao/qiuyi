"""深度球队分析 - 球星状态/攻防能力/赛事表现"""
from typing import Dict, List

# ===== 各队核心球星 & 状态 =====
PLAYER_STATUS = {
    "巴西": {
        "star": "内马尔(Neymar)",
        "form": "⚡火热",
        "goals_r16": 1,
        "assists_r16": 1,
        "key_pass": 3,
        "shots": 5,
        "injured": False,
        "note": "对日本传射建功, 状态正佳"
    },
    "挪威": {
        "star": "哈兰德(Haaland)",
        "form": "🔥爆棚",
        "goals_r16": 2,
        "assists_r16": 0,
        "key_pass": 1,
        "shots": 6,
        "injured": False,
        "note": "1/16独中两元, 挪威进攻核心"
    },
    "墨西哥": {
        "star": "洛萨诺(Lozano)",
        "form": "✅稳定",
        "goals_r16": 1,
        "assists_r16": 0,
        "key_pass": 2,
        "shots": 3,
        "injured": False,
        "note": "边路突破犀利"
    },
    "英格兰": {
        "star": "凯恩(Kane)",
        "form": "⚡火热",
        "goals_r16": 2,
        "assists_r16": 0,
        "key_pass": 2,
        "shots": 4,
        "injured": False,
        "note": "对刚果金梅开二度"
    },
    "葡萄牙": {
        "star": "C罗(C.Ronaldo)",
        "form": "🔥爆棚",
        "goals_r16": 2,
        "assists_r16": 0,
        "key_pass": 1,
        "shots": 5,
        "injured": False,
        "note": "淘汰赛模式开启, 对克罗地亚进2球"
    },
    "西班牙": {
        "star": "莫拉塔(Morata)",
        "form": "⚡火热",
        "goals_r16": 2,
        "assists_r16": 0,
        "key_pass": 2,
        "shots": 4,
        "injured": False,
        "note": "对奥地利梅开二度, 状态火热"
    },
    "美国": {
        "star": "普利西奇(Pulisic)",
        "form": "✅稳定",
        "goals_r16": 1,
        "assists_r16": 1,
        "key_pass": 2,
        "shots": 3,
        "injured": False,
        "note": "队长核心, 攻防枢纽"
    },
    "比利时": {
        "star": "德布劳内(KDB)",
        "form": "🔥爆棚",
        "goals_r16": 0,
        "assists_r16": 2,
        "key_pass": 4,
        "shots": 2,
        "injured": False,
        "note": "对塞内加尔2助攻, 创造力TOP"
    },
    "阿根廷": {
        "star": "梅西(Messi)",
        "form": "🔥🔥🔥封神",
        "goals_r16": 3,
        "assists_r16": 1,
        "key_pass": 5,
        "shots": 7,
        "injured": False,
        "note": "对佛得角帽子戏法, 球王模式!"
    },
    "埃及": {
        "star": "萨拉赫(Salah)",
        "form": "🔥爆棚",
        "goals_r16": 3,
        "assists_r16": 1,
        "key_pass": 3,
        "shots": 6,
        "injured": False,
        "note": "对澳大利亚2球1助, 状态爆棚"
    },
    "瑞士": {
        "star": "阿坎吉(Akanji)",
        "form": "✅稳定",
        "goals_r16": 0,
        "assists_r16": 0,
        "key_pass": 1,
        "shots": 1,
        "injured": False,
        "note": "后防核心, 防守稳固"
    },
    "哥伦比亚": {
        "star": "J罗(James)",
        "form": "⚡火热",
        "goals_r16": 1,
        "assists_r16": 1,
        "key_pass": 3,
        "shots": 4,
        "injured": False,
        "note": "对加纳传射, 世界杯先生回归"
    },
    "法国": {
        "star": "姆巴佩(Mbappe)",
        "form": "🔥🔥🔥封神",
        "goals_r16": 2,
        "assists_r16": 0,
        "key_pass": 3,
        "shots": 6,
        "injured": False,
        "note": "对瑞典2球, 已晋级8强, 休息充分"
    },
    "摩洛哥": {
        "star": "阿什拉夫(Hakimi)",
        "form": "⚡火热",
        "goals_r16": 0,
        "assists_r16": 1,
        "key_pass": 2,
        "shots": 2,
        "injured": False,
        "note": "边路发动机, 已晋级8强"
    },
}

# ===== 1/16决赛详细攻防数据 =====
TEAM_DETAILED_STATS = {
    "巴西": {"gf": 2, "ga": 1, "shots": 14, "shots_on": 6, "possession": 58, "pass_acc": 86, "fouls": 12, "cards": 2},
    "挪威": {"gf": 2, "ga": 1, "shots": 11, "shots_on": 5, "possession": 45, "pass_acc": 79, "fouls": 14, "cards": 3},
    "墨西哥": {"gf": 2, "ga": 0, "shots": 13, "shots_on": 5, "possession": 52, "pass_acc": 83, "fouls": 10, "cards": 1},
    "英格兰": {"gf": 2, "ga": 1, "shots": 15, "shots_on": 6, "possession": 61, "pass_acc": 88, "fouls": 8, "cards": 1},
    "葡萄牙": {"gf": 2, "ga": 1, "shots": 12, "shots_on": 5, "possession": 53, "pass_acc": 84, "fouls": 11, "cards": 2},
    "西班牙": {"gf": 3, "ga": 0, "shots": 18, "shots_on": 8, "possession": 68, "pass_acc": 91, "fouls": 6, "cards": 0},
    "美国": {"gf": 2, "ga": 0, "shots": 10, "shots_on": 4, "possession": 48, "pass_acc": 81, "fouls": 13, "cards": 2},
    "比利时": {"gf": 3, "ga": 2, "shots": 16, "shots_on": 7, "possession": 56, "pass_acc": 85, "fouls": 9, "cards": 1},
    "阿根廷": {"gf": 3, "ga": 2, "shots": 17, "shots_on": 8, "possession": 64, "pass_acc": 87, "fouls": 10, "cards": 2},
    "埃及": {"gf": 5, "ga": 3, "shots": 14, "shots_on": 7, "possession": 42, "pass_acc": 76, "fouls": 16, "cards": 4},
    "瑞士": {"gf": 2, "ga": 0, "shots": 9, "shots_on": 4, "possession": 46, "pass_acc": 80, "fouls": 12, "cards": 2},
    "哥伦比亚": {"gf": 1, "ga": 0, "shots": 8, "shots_on": 3, "possession": 51, "pass_acc": 82, "fouls": 15, "cards": 3},
}

# ===== 攻防能力评分(基于1/16表现, 满分100) =====
TEAM_STRENGTH = {
    "巴西": {"attack": 82, "defense": 75, "midfield": 80, "speed": 85, "star_power": 88, "form": 80, "overall": 82},
    "挪威": {"attack": 78, "defense": 68, "midfield": 70, "speed": 76, "star_power": 85, "form": 78, "overall": 76},
    "墨西哥": {"attack": 72, "defense": 76, "midfield": 74, "speed": 78, "star_power": 72, "form": 75, "overall": 74},
    "英格兰": {"attack": 84, "defense": 78, "midfield": 82, "speed": 80, "star_power": 86, "form": 82, "overall": 82},
    "葡萄牙": {"attack": 80, "defense": 72, "midfield": 78, "speed": 76, "star_power": 90, "form": 84, "overall": 80},
    "西班牙": {"attack": 86, "defense": 82, "midfield": 90, "speed": 72, "star_power": 80, "form": 85, "overall": 84},
    "美国": {"attack": 70, "defense": 74, "midfield": 72, "speed": 82, "star_power": 74, "form": 72, "overall": 74},
    "比利时": {"attack": 84, "defense": 68, "midfield": 86, "speed": 78, "star_power": 84, "form": 76, "overall": 80},
    "阿根廷": {"attack": 90, "defense": 65, "midfield": 82, "speed": 76, "star_power": 95, "form": 88, "overall": 84},
    "埃及": {"attack": 76, "defense": 58, "midfield": 66, "speed": 80, "star_power": 82, "form": 82, "overall": 74},
    "瑞士": {"attack": 66, "defense": 78, "midfield": 72, "speed": 68, "star_power": 68, "form": 70, "overall": 70},
    "哥伦比亚": {"attack": 74, "defense": 74, "midfield": 76, "speed": 74, "star_power": 78, "form": 72, "overall": 74},
    "法国": {"attack": 92, "defense": 85, "midfield": 88, "speed": 90, "star_power": 96, "form": 86, "overall": 90},
    "摩洛哥": {"attack": 72, "defense": 70, "midfield": 74, "speed": 82, "star_power": 76, "form": 85, "overall": 76},
}

# ===== 交锋看点 =====
MATCH_HIGHLIGHTS = {
    "巴西vs挪威": "巴西对日本丢球防守有漏洞; 挪威哈兰德2球状态火热; 巴西必须提防哈兰德反击",
    "墨西哥vs英格兰": "英格兰控球占优(61%); 墨西哥防守好(零封); 凯恩vs墨西哥防线是看点",
    "葡萄牙vs西班牙": "伊比利亚德比; C罗2球vs莫拉塔2球; 西班牙传球控制更强(91%传球成功率)",
    "美国vs比利时": "技术流对轰; 比利时德布劳内创造力强; 美国普利西奇边路威胁",
    "阿根廷vs埃及": "梅西3球1助封神状态; 萨拉赫2球1助也不弱; 阿根廷防守差(丢2球)vs埃及进攻强(进5球)",
    "瑞士vs哥伦比亚": "防守对决; 瑞士防守稳固(零封); J罗世界杯状态回归; 小球格局",
}


def get_player_analysis(team: str) -> Dict:
    """获取球队球星分析"""
    return PLAYER_STATUS.get(team, {
        "star": "待分析", "form": "⏳待定", "goals_r16": 0,
        "assists_r16": 0, "key_pass": 0, "shots": 0, "injured": False, "note": ""
    })

def get_team_strength_analysis(home: str, away: str) -> Dict:
    """获取两队实力对比分析"""
    hs = TEAM_STRENGTH.get(home, {})
    aw = TEAM_STRENGTH.get(away, {})
    if not hs or not aw:
        return {}
    
    keys = ['attack', 'defense', 'midfield', 'speed', 'star_power', 'form', 'overall']
    result = {}
    for k in keys:
        diff = hs.get(k, 50) - aw.get(k, 50)
        result[k] = {
            'home': hs.get(k, 50),
            'away': aw.get(k, 50),
            'diff': diff,
            'advantage': home if diff > 5 else (away if diff < -5 else '接近')
        }
    return result

def get_depth_analysis(match_name: str) -> Dict:
    """深度比赛分析(弃用)"""
    parts = match_name.replace('vs', ' VS ').split(' VS ')
    if len(parts) != 2:
        return {}
    home, away = parts[0].strip(), parts[1].strip()
    
    # 球星数据
    hp = get_player_analysis(home)
    ap = get_player_analysis(away)
    
    # 实力对比
    strength = get_team_strength_analysis(home, away)
    
    # 比赛看点
    highlight = MATCH_HIGHLIGHTS.get(match_name, "")
    
    return {
        'home_star': hp,
        'away_star': ap,
        'strength': strength,
        'highlight': highlight,
        'home_form': TEAM_DETAILED_STATS.get(home, {}),
        'away_form': TEAM_DETAILED_STATS.get(away, {}),
    }
