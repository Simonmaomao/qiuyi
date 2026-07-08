"""v3.0 双验证分析引擎 + 多源数据融合"""
import math
from typing import List, Dict, Tuple
import itertools
from app.services.match_data import TEAM_STATS, MARKET_PROBS, DEVIATION_ANALYSIS, MATCH_RESULTS
from app.services.team_analysis import get_player_analysis, get_team_strength_analysis, MATCH_HIGHLIGHTS, TEAM_DETAILED_STATS

class AnalysisEngine:
    """核心分析引擎: 价值检测 + 胜率计算 + 串关优化 + 多源数据"""
    
    def __init__(self):
        self.knockout_coef = 0.82  # ⚡调低: 淘汰赛防守优先, 进球减少
        self.total_goals_base = 2.5  # ⚡调低: 实际进球低于预期
        self.team_stats = TEAM_STATS
        self.market_probs = MARKET_PROBS
        self.deviation = DEVIATION_ANALYSIS
        self.ev_threshold = 0.82  # ⚡调低: 更多选项通过筛选
        self.win_rate_threshold = 35  # ⚡调低: 降低胜率门槛
        self.score_ev_threshold = 0.65  # ⚡调低: 比分推荐更积极
    
    def poisson(self, lmbda: float, k: int) -> float:
        return math.exp(-lmbda) * (lmbda ** k) / math.factorial(k)
    
    def calc_true_prob(self, market_odds: List[float]) -> List[float]:
        inv = [1/o for o in market_odds]
        total = sum(inv)
        return [i/total for i in inv]
    
    def _calc_all_options(self, sp_list, market_probs, labels):
        """计算三个选项(胜/平/负)的完整分析"""
        results = []
        for i in range(3):
            sp = sp_list[i] if sp_list and i < len(sp_list) else 0
            mp = market_probs[i] if market_probs and i < len(market_probs) else 0.33
            win_rate = round(mp * 100, 1)
            ev = round(sp * win_rate / 100, 2) if sp > 0 else 0
            results.append({
                'label': labels[i],
                'sp': sp,
                'win_rate': win_rate,
                'ev': ev,
                'recommended': ev > self.ev_threshold and win_rate > self.win_rate_threshold
            })
        best = max(results, key=lambda x: x['ev'] * x['win_rate'] / 100) if any(r['ev'] > 0 for r in results) else results[0]
        for r in results:
            r['best'] = (r['label'] == best['label'])
        return results, best

    def analyze_match(self, match, market_odds):
        """分析单场比赛 - 返回全部3个选项"""
        home = match['home']
        away = match['away']
        spf_sp = match.get('spf_sp', [0, 0, 0])
        rq_sp = match.get('rq_sp', [0, 0, 0])
        handicap = match.get('handicap', 0)
        key = f"{home}vs{away}"
        
        # 球队数据
        home_stats = self.team_stats.get(home, {"gf": 0, "ga": 0})
        away_stats = self.team_stats.get(away, {"gf": 0, "ga": 0})
        dev = self.deviation.get(key, {})
        
        # 市场概率
        total_spf = sum(1/max(o, 0.01) for o in spf_sp if o > 0)
        spf_market = [1/max(o, 0.01)/total_spf if o > 0 else 0.33 for o in spf_sp]
        total_rq = sum(1/max(o, 0.01) for o in rq_sp if o > 0)
        rq_market = [1/max(o, 0.01)/total_rq if o > 0 else 0.33 for o in rq_sp]
        
        # 淘汰赛修正: 提高平局概率(防守优先), 降低强队大胜概率
        # 让球平选项被低估 (Mexico让球平教训)
        spf_market[1] = spf_market[1] * 1.15  # 平局+15%
        spf_market[0] = spf_market[0] * 0.92  # 主胜-8%
        spf_market[2] = spf_market[2] * 0.92  # 客胜-8%
        # 让球市场也做类似修正
        rq_market[1] = rq_market[1] * 1.12  # 让球平+12%
        # 重新归一化
        spf_total = sum(spf_market)
        spf_market = [p/spf_total for p in spf_market]
        rq_total = sum(rq_market)
        rq_market = [p/rq_total for p in rq_market]
        
        # SPF三个选项
        spf_labels = [f'{home}胜', '平局', f'{away}胜']
        spf_options, spf_best = self._calc_all_options(spf_sp, spf_market, spf_labels)
        
        # 让球三个选项
        if handicap > 0:  # 客队受让
            rq_labels = [f'{away}+{handicap}负', f'{away}+{handicap}平', f'{away}+{handicap}胜']
        elif handicap < 0:  # 主队让球
            rq_labels = [f'{home}{handicap}胜', f'{home}{handicap}平', f'{home}{handicap}负']
        else:
            rq_labels = ['不让球胜', '不让球平', '不让球负']
        rq_options, rq_best = self._calc_all_options(rq_sp, rq_market, rq_labels)
        
        # 比分分析 - 使用体彩SPF赔率计算概率(无市场赔率时)
        scores = []
        if market_odds:
            probs = self.calc_true_prob(market_odds)
        else:
            # 从体彩SPF赔率反推概率
            total = sum(1/max(o,0.01) for o in spf_sp)
            probs = [1/max(o,0.01)/total for o in spf_sp] if total > 0 else [0.4, 0.3, 0.3]
        ph, pd, pa = probs
        # 淘汰赛防守修正: 强队进攻效率打折扣 (巴西被爆冷教训)
        fav_adjust = 0.92 if abs(ph - pa) > 0.15 else 1.0  # 一方明显占优时调低预期
        if ph > pa:
            strength = ph / (ph + pa) * fav_adjust
            l_total = self.total_goals_base * self.knockout_coef
            lh = l_total * strength
            la = l_total * (1 - strength)
        else:
            strength = pa / (ph + pa) * fav_adjust
            l_total = self.total_goals_base * self.knockout_coef
            lh = l_total * (1 - strength)
            la = l_total * strength
        for i in range(7):
            for j in range(7):
                if i + j > 6: continue
                prob = self.poisson(lh, i) * self.poisson(la, j)
                if prob > 0.01:
                    scores.append({'score': f"{i}-{j}", 'prob': round(prob * 100, 1)})
        scores.sort(key=lambda x: -x['prob'])
        
        return {
            'match_id': match.get('id', ''),
            'match_name': f"{home}vs{away}",
            'handicap': handicap,
            'team_stats': {
                'home': {"gf": home_stats.get('gf',0), "ga": home_stats.get('ga',0)},
                'away': {"gf": away_stats.get('gf',0), "ga": away_stats.get('ga',0)},
            },
            'market_bias': dev,
            'stars': {
                'home': get_player_analysis(home),
                'away': get_player_analysis(away),
            } if 'get_player_analysis' in dir() else {},
            'strength': get_team_strength_analysis(home, away) if 'get_team_strength_analysis' in dir() else {},
            'highlight': MATCH_HIGHLIGHTS.get(key, ''),
            'detail_stats': {
                'home': TEAM_DETAILED_STATS.get(home, {}),
                'away': TEAM_DETAILED_STATS.get(away, {}),
            },
            'spf_options': spf_options,
            'spf_best': spf_best,
            'rq_options': rq_options,
            'rq_best': rq_best,
            'scores': scores[:8],
            'score': round((spf_best.get('win_rate',50) * 40 + spf_best.get('ev',0.5) * 30 + rq_best.get('win_rate',50) * 20 + rq_best.get('ev',0.5) * 10) / 100, 1)
        }

    def optimize_parlay(self, analyses: List[Dict], budget: float = 500,
                       min_ev: float = 0.68, max_picks: int = 4) -> List[Dict]:
        picks = []
        for a in analyses:
            for opt_key in ['spf_options', 'rq_options']:
                for opt in a[opt_key]:
                    if opt['recommended']:
                        picks.append({
                            'name': f"{a['match_name']} {opt['label']}",
                            'sp': opt['sp'],
                            'win_rate': opt['win_rate'] / 100,
                            'ev': opt['ev'],
                            'match': a['match_name']
                        })
        results = []
        for r in range(2, min(max_picks + 1, len(picks) + 1)):
            for combo in itertools.combinations(picks, r):
                sp = 1; prob = 1; names = []
                for p in combo:
                    sp *= p['sp']; prob *= p['win_rate']; names.append(p['name'][:12])
                ev = sp * prob
                if ev < min_ev: continue
                results.append({
                    'picks': [p['name'] for p in combo],
                    'sp': round(sp, 2),
                    'win_rate': round(prob * 100, 1),
                    'ev': round(ev, 2),
                    'payout': round(sp * 100)
                })
        results.sort(key=lambda x: -x['ev'])
        return results[:15]

    def generate_plan(self, analyses: List[Dict], budget: float = 500) -> Dict:
        parlays = self.optimize_parlay(analyses, budget)
        core = [p for p in parlays if p['ev'] > 0.70 and p['win_rate'] > 10][:3]
        value = [p for p in parlays if 0.65 <= p['ev'] <= 0.70][:3]
        fun = [p for p in parlays if p['ev'] > 0.60 and p['win_rate'] < 10][:3]
        if core:
            cs = budget * 0.6
            for p in core:
                p['stake'] = round(cs / len(core), 0)
                p['payout'] = round(p['stake'] * p['sp'])
        if value:
            vs = budget * 0.25
            for p in value:
                p['stake'] = round(vs / len(value), 0)
                p['payout'] = round(p['stake'] * p['sp'])
        if fun:
            fs = budget * 0.15
            for p in fun:
                p['stake'] = round(fs / len(fun), 0)
                p['payout'] = round(p['stake'] * p['sp'])
        return {
            'core': core, 'value': value, 'fun': fun,
            'total_stake': budget,
            'max_payout': sum(p.get('payout', 0) for p in core + value + fun)
        }
