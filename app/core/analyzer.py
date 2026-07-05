"""v3.0 双验证分析引擎 + 多源数据融合"""
import math
from typing import List, Dict, Tuple
import itertools
from app.services.match_data import TEAM_STATS, MARKET_PROBS, DEVIATION_ANALYSIS, MATCH_RESULTS
from app.services.team_analysis import get_player_analysis, get_team_strength_analysis, MATCH_HIGHLIGHTS, TEAM_DETAILED_STATS

class AnalysisEngine:
    """核心分析引擎: 价值检测 + 胜率计算 + 串关优化 + 多源数据"""
    
    def __init__(self):
        self.knockout_coef = 0.88
        self.total_goals_base = 2.6
        self.team_stats = TEAM_STATS
        self.market_probs = MARKET_PROBS
        self.deviation = DEVIATION_ANALYSIS
    
    def poisson(self, lmbda: float, k: int) -> float:
        """泊松分布概率"""
        return math.exp(-lmbda) * (lmbda ** k) / math.factorial(k)
    
    def calc_true_prob(self, market_odds: List[float]) -> List[float]:
        """从市场赔率计算真实概率"""
        inv = [1/o for o in market_odds]
        total = sum(inv)
        return [i/total for i in inv]
    
    def calc_ev(self, sp: float, true_prob: float) -> float:
        """计算期望值"""
        return sp * true_prob
    
    def calc_value_rate(self, sp: float, true_prob: float) -> float:
        """计算价值率"""
        fair = 1 / true_prob
        return (sp - fair) / fair * 100
    
    def analyze_match(self, match: Dict, market_odds: List[float]) -> Dict:
        """多源分析: 体彩SP + Bet365 + 球队数据 + 赛果"""
        spf_sp = match['spf_sp']
        rq_sp = match['rq_sp']
        handicap = match['handicap']
        
        # 使用Bet365真实概率(优先)或从市场赔率计算
        key = f"{match['home']}vs{match['away']}"
        if key in self.market_probs:
            mp = self.market_probs[key]
            probs = [mp['h'], mp['d'], mp['a']]
        else:
            probs = self.calc_true_prob(market_odds)
        
        ph, pd, pa = probs
        
        # 球队攻防数据
        home_stats = self.team_stats.get(match['home'], {"gf": 0, "ga": 0})
        away_stats = self.team_stats.get(match['away'], {"gf": 0, "ga": 0})
        
        # 偏差分析
        dev = self.deviation.get(key, {})
        
        result = {
            'match_id': match['id'],
            'match_name': f"{match['home']}vs{match['away']}",
            'team_stats': {
                'home': {"gf": home_stats['gf'], "ga": home_stats['ga']},
                'away': {"gf": away_stats['gf'], "ga": away_stats['ga']},
            },
            'market_bias': dev,
            # 深度数据
            'stars': {
                'home': get_player_analysis(match['home']),
                'away': get_player_analysis(match['away']),
            },
            'strength': get_team_strength_analysis(match['home'], match['away']),
            'highlight': MATCH_HIGHLIGHTS.get(key, ''),
            'detail_stats': {
                'home': TEAM_DETAILED_STATS.get(match['home'], {}),
                'away': TEAM_DETAILED_STATS.get(match['away'], {}),
            },
        }
        
        # === 让球不败方向分析 ===
        if handicap > 0:  # 主队受让
            rq_true = ph + pd  # 主不败
            rq_sp_val = rq_sp[0]  # 让球胜
            rq_dir = f"{match['home']}不败"
            rq_label = "让球胜"
        else:  # 主队让球
            rq_true = pd + pa  # 客不败
            rq_sp_val = rq_sp[2]  # 让球负
            rq_dir = f"{match['away']}不败"
            rq_label = "让球负"
        
        rq_ev = self.calc_ev(rq_sp_val, rq_true)
        rq_val_rate = self.calc_value_rate(rq_sp_val, rq_true)
        rq_pass = rq_ev > 0.85 and rq_true > 0.40
        
        result['rq'] = {
            'direction': rq_dir,
            'label': rq_label,
            'sp': rq_sp_val,
            'win_rate': round(rq_true * 100, 1),
            'value_rate': round(rq_val_rate, 1),
            'ev': round(rq_ev, 2),
            'pass': rq_pass
        }
        
        # === SPF客胜方向分析 ===
        # 让球方=主队时, 客胜有SPF价值
        if handicap < 0:
            spf_true = pa  # 客胜
            spf_sp_val = spf_sp[2]
            spf_dir = f"{match['away']}胜"
        else:
            spf_true = ph  # 主胜
            spf_sp_val = spf_sp[0]
            spf_dir = f"{match['home']}胜"
        
        spf_ev = self.calc_ev(spf_sp_val, spf_true)
        spf_val_rate = self.calc_value_rate(spf_sp_val, spf_true)
        spf_pass = spf_ev > 0.80 and spf_true > 0.30
        
        result['spf'] = {
            'direction': spf_dir,
            'sp': spf_sp_val,
            'win_rate': round(spf_true * 100, 1),
            'value_rate': round(spf_val_rate, 1),
            'ev': round(spf_ev, 2),
            'pass': spf_pass
        }
        
        # === 比分分析 ===
        result['scores'] = self.analyze_scores(match, probs)
        
        # === 综合评分 ===
        result['score'] = round(
            (rq_true * 40 + rq_ev * 30 + spf_true * 15 + spf_ev * 15), 1
        )
        
        return result
    
    def analyze_scores(self, match: Dict, probs: List[float]) -> List[Dict]:
        """分析所有比分选项"""
        ph, pd, pa = probs
        
        # 计算每队预期进球
        # 基于淘汰赛修正
        if ph > pa:
            strength = ph / (ph + pa)
            l_total = self.total_goals_base * self.knockout_coef
            lh = l_total * strength
            la = l_total * (1 - strength)
        else:
            strength = pa / (ph + pa)
            l_total = self.total_goals_base * self.knockout_coef
            lh = l_total * (1 - strength)
            la = l_total * strength
        
        scores = []
        for i in range(7):
            for j in range(7):
                if i + j > 6:
                    continue
                prob = self.poisson(lh, i) * self.poisson(la, j)
                if prob > 0.01:  # 概率>1%
                    scores.append({
                        'score': f"{i}-{j}",
                        'prob': round(prob * 100, 1)
                    })
        
        scores.sort(key=lambda x: -x['prob'])
        return scores[:8]  # TOP8
    
    def optimize_parlay(self, analyses: List[Dict], budget: float = 500,
                       min_ev: float = 0.80, max_picks: int = 4) -> List[Dict]:
        """优化串关组合"""
        # 收集所有通过验证的方向
        picks = []
        for a in analyses:
            for key in ['rq', 'spf']:
                d = a[key]
                if d['pass']:
                    picks.append({
                        'name': f"{a['match_name']} {d['direction']}",
                        'sp': d['sp'],
                        'win_rate': d['win_rate'] / 100,
                        'ev': d['ev'],
                        'label': d.get('label', 'SPF'),
                        'match': a['match_name']
                    })
        
        results = []
        for r in range(2, min(max_picks + 1, len(picks) + 1)):
            for combo in itertools.combinations(picks, r):
                sp = 1
                prob = 1
                names = []
                for p in combo:
                    sp *= p['sp']
                    prob *= p['win_rate']
                    names.append(p['name'][:12])
                
                ev = sp * prob
                if ev < min_ev:
                    continue
                
                results.append({
                    'picks': [p['name'] for p in combo],
                    'sp': round(sp, 2),
                    'win_rate': round(prob * 100, 1),
                    'ev': round(ev, 2),
                    'fair_odds': round(1/prob, 1),
                    'payout_100': round(sp * 100)
                })
        
        results.sort(key=lambda x: -x['ev'])
        return results[:15]  # TOP15
    
    def generate_plan(self, analyses: List[Dict], budget: float = 500) -> Dict:
        """生成完整投注方案"""
        parlays = self.optimize_parlay(analyses, budget)
        
        # 核心方案: 较高EV串关
        core = [p for p in parlays if p['ev'] > 0.82 and p['win_rate'] > 10][:3]
        
        # 价值方案: 中等EV串关  
        value = [p for p in parlays if 0.78 <= p['ev'] <= 0.82][:3]
        
        # 博冷方案: 高赔低概率
        fun = [p for p in parlays if p['ev'] > 0.75 and p['win_rate'] < 10][:3]
        
        # 资金分配
        if core:
            core_stake = budget * 0.6
            for p in core:
                p['stake'] = round(core_stake / len(core), 0)
                p['payout'] = round(p['stake'] * p['sp'])
        
        if value:
            val_stake = budget * 0.25
            for p in value:
                p['stake'] = round(val_stake / len(value), 0)
                p['payout'] = round(p['stake'] * p['sp'])
        
        if fun:
            fun_stake = budget * 0.15
            for p in fun:
                p['stake'] = round(fun_stake / len(fun), 0)
                p['payout'] = round(p['stake'] * p['sp'])
        
        return {
            'core': core,
            'value': value,
            'fun': fun,
            'total_stake': budget,
            'max_payout': sum(p.get('payout', 0) for p in core + value + fun)
        }
