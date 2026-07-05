"""数据模型"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Match(BaseModel):
    id: str
    home: str
    away: str
    league: str = "世界杯"
    match_time: str
    deadline: str
    handicap: int  # -1, 0, +1
    
    # SPF odds [胜, 平, 负]
    spf_sp: List[float]
    # Handicap odds [让球胜, 让球平, 让球负]
    rq_sp: List[float]
    
    # Market odds (Bet365)
    market_sp: List[float]
    
class Analysis(BaseModel):
    match_id: str
    match_name: str
    
    # 让球不败方向
    rq_direction: str
    rq_sp: float
    rq_win_rate: float
    rq_value_rate: float
    rq_ev: float
    rq_pass: bool
    
    # SPF方向(客胜)
    spf_direction: str
    spf_sp: float
    spf_win_rate: float
    spf_value_rate: float
    spf_ev: float
    spf_pass: bool
    
    # 最佳比分
    best_scores: List[dict]

class Parlay(BaseModel):
    picks: List[dict]
    sp: float
    win_rate: float
    ev: float
    stake: float
    payout: float

class BettingPlan(BaseModel):
    core: List[Parlay]
    value: List[Parlay]
    fun: List[Parlay]
    total_stake: float
    max_payout: float
