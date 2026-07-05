"""自我复盘学习引擎 - 每日自动优化"""
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

REVIEW_FILE = os.path.join(os.path.dirname(__file__), '../../data/review.json')
PARAMS_FILE = os.path.join(os.path.dirname(__file__), '../../data/params.json')

class SelfLearning:
    """自我复盘学习系统"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.reviews = self._load(REVIEW_FILE, {
                'daily': [],        # 每日复盘记录
                'predictions': [],  # 历史预测记录
                'accuracy': {       # 各玩法准确率统计
                    'rq_win': {'correct': 0, 'total': 0, 'rate': 0},
                    'spf_win': {'correct': 0, 'total': 0, 'rate': 0},
                    'score_exact': {'correct': 0, 'total': 0, 'rate': 0},
                    'score_direction': {'correct': 0, 'total': 0, 'rate': 0},
                },
                'strategy_weights': {  # 策略权重（动态调整）
                    'ev_threshold': 0.85,
                    'win_rate_threshold': 40,
                    'score_ev_threshold': 0.7,
                    'rq_weight': 1.0,
                    'spf_weight': 0.6,
                    'score_weight': 0.3,
                }
            })
            self.params = self._load(PARAMS_FILE, {
                'last_learn_date': '',
                'learn_count': 0,
                'optimizations': [],
            })
    
    def _load(self, path, default):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except:
            return default
    
    def _save(self, path, data):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def save_predictions(self, analyses: List[Dict]):
        """保存今日预测记录"""
        today = datetime.now().strftime('%Y-%m-%d')
        record = {
            'date': today,
            'time': datetime.now().strftime('%H:%M'),
            'matches': []
        }
        for m in analyses:
            # 取比分TOP3
            top_scores = [(s['score'], s['prob']) for s in m.get('scores', [])[:3]]
            record['matches'].append({
                'match': m['match_name'],
                'rq_direction': m['rq']['direction'],
                'rq_sp': m['rq']['sp'],
                'rq_win_rate': m['rq']['win_rate'],
                'rq_ev': m['rq']['ev'],
                'rq_recommended': m['rq']['pass'],
                'spf_direction': m['spf']['direction'],
                'spf_sp': m['spf']['sp'],
                'spf_win_rate': m['spf']['win_rate'],
                'spf_ev': m['spf']['ev'],
                'top_scores': top_scores,
            })
        
        # 去重：同一天不重复保存
        existing = [r for r in self.reviews['predictions'] if r['date'] != today]
        existing.append(record)
        self.reviews['predictions'] = existing[-30:]  # 保留最近30天
        self._save(REVIEW_FILE, self.reviews)
    
    def record_result(self, match_name: str, results: Dict):
        """记录比赛实际结果，用于复盘"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 找到今天的预测记录
        for p in self.reviews['predictions']:
            if p['date'] != today:
                continue
            for m in p['matches']:
                if m['match'] == match_name:
                    # 记录实际结果
                    m['actual_result'] = results
                    m['reviewed'] = True
                    
                    # 更新准确率
                    acc = self.reviews['accuracy']
                    
                    # 让球方向
                    if results.get('rq_correct') is not None:
                        acc['rq_win']['total'] += 1
                        if results['rq_correct']:
                            acc['rq_win']['correct'] += 1
                    
                    # SPF方向
                    if results.get('spf_correct') is not None:
                        acc['spf_win']['total'] += 1
                        if results['spf_correct']:
                            acc['spf_win']['correct'] += 1
                    
                    # 计算各玩法准确率
                    for k in ['rq_win', 'spf_win', 'score_exact', 'score_direction']:
                        t = acc[k]['total']
                        if t > 0:
                            acc[k]['rate'] = round(acc[k]['correct'] / t * 100, 1)
                    
                    self._save(REVIEW_FILE, self.reviews)
                    return True
        return False
    
    def daily_review(self) -> Dict:
        """每日复盘分析"""
        today = datetime.now().strftime('%Y-%m-%d')
        acc = self.reviews['accuracy']
        
        # 计算今日待复盘比赛
        pending = 0
        reviewed = 0
        for p in self.reviews['predictions']:
            if p['date'] == today:
                for m in p['matches']:
                    if m.get('reviewed'):
                        reviewed += 1
                    else:
                        pending += 1
        
        # 策略优化建议
        suggestions = []
        if acc['rq_win']['total'] >= 5:
            rq_rate = acc['rq_win']['rate']
            if rq_rate < 40:
                suggestions.append(f"⚠️ 让球推荐准确率仅{rq_rate}%，建议提高EV门槛至0.90+")
            elif rq_rate > 65:
                suggestions.append(f"✅ 让球推荐准确率{rq_rate}%，保持当前策略")
        
        if acc['spf_win']['total'] >= 5:
            spf_rate = acc['spf_win']['rate']
            if spf_rate > rq_rate + 10:
                suggestions.append(f"💡 SPF准确率({spf_rate}%)优于让球，可适当提高SPF权重")
        
        # 自动调整策略参数
        self._auto_tune(acc)
        
        return {
            'date': today,
            'total_predictions': sum(len(p['matches']) for p in self.reviews['predictions'] if p['date'] == today),
            'reviewed': reviewed,
            'pending': pending,
            'accuracy': acc,
            'strategy_weights': self.reviews['strategy_weights'],
            'suggestions': suggestions,
            'params': self.params,
        }
    
    def _auto_tune(self, acc):
        """自动调整策略参数（自我学习核心）"""
        weights = self.reviews['strategy_weights']
        changed = False
        today = datetime.now().strftime('%Y-%m-%d')
        
        if today == self.params['last_learn_date']:
            return  # 每天只优化一次
        
        # 根据让球准确率调整EV阈值
        if acc['rq_win']['total'] >= 5:
            if acc['rq_win']['rate'] < 45:
                old = weights['ev_threshold']
                weights['ev_threshold'] = min(1.0, old + 0.03)
                self.params['optimizations'].append({
                    'date': today, 'type': 'ev_threshold',
                    'from': old, 'to': weights['ev_threshold'],
                    'reason': f'让球准确率{acc["rq_win"]["rate"]}%偏低，提高门槛'
                })
                changed = True
            elif acc['rq_win']['rate'] > 70:
                old = weights['ev_threshold']
                weights['ev_threshold'] = max(0.7, old - 0.02)
                changed = True
        
        # 根据SPF准确率调整权重
        if acc['spf_win']['total'] >= 3 and acc['rq_win']['total'] >= 3:
            if acc['spf_win']['rate'] > acc['rq_win']['rate'] + 15:
                old = weights['spf_weight']
                weights['spf_weight'] = min(1.0, old + 0.1)
                weights['rq_weight'] = max(0.5, weights['rq_weight'] - 0.05)
                self.params['optimizations'].append({
                    'date': today, 'type': 'spf_weight',
                    'from': old, 'to': weights['spf_weight'],
                    'reason': f'SPF({acc["spf_win"]["rate"]}%)优于让球({acc["rq_win"]["rate"]}%)，提升权重'
                })
                changed = True
        
        if changed:
            self.params['last_learn_date'] = today
            self.params['learn_count'] += 1
            self._save(PARAMS_FILE, self.params)
            self._save(REVIEW_FILE, self.reviews)
    
    def get_optimized_params(self) -> Dict:
        """获取优化后的分析参数"""
        w = self.reviews['strategy_weights']
        return {
            'ev_threshold': w['ev_threshold'],
            'win_rate_threshold': w['win_rate_threshold'],
            'score_ev_threshold': w['score_ev_threshold'],
            'rq_weight': w['rq_weight'],
            'spf_weight': w['spf_weight'],
            'score_weight': w['score_weight'],
            'learn_count': self.params['learn_count'],
        }
    
    def get_review_history(self, days=7) -> List:
        """获取最近N天的复盘历史"""
        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        return [r for r in self.reviews['daily'] if r['date'] >= cutoff]
