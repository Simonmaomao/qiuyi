"""数据缓存 - 自动更新"""
import json
import os
import time
from datetime import datetime

CACHE_FILE = os.path.join(os.path.dirname(__file__), '../../data/cache.json')

class DataCache:
    """自动更新数据缓存"""
    
    _instance = None
    _data = None
    _last_fetch = 0
    _cache_ttl = 600  # 10分钟自动刷新
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_data(self, force_refresh=False):
        """获取缓存数据，过期自动刷新"""
        now = time.time()
        if force_refresh or not self._data or (now - self._last_fetch) > self._cache_ttl:
            self._refresh()
        return self._data
    
    def _refresh(self):
        """刷新数据"""
        # 尝试从缓存文件读取
        cached = self._load_cache()
        if cached and (time.time() - cached.get('timestamp', 0)) < self._cache_ttl:
            self._data = cached
            self._last_fetch = cached.get('timestamp', time.time())
            return
        
        # 使用当前内存数据(下次浏览器访问时会更新)
        if not self._data:
            self._data = self._default_data()
        
        self._last_fetch = time.time()
        self._save_cache(self._data)
    
    def update_from_browser(self, match_data):
        """从浏览器更新数据"""
        self._data = {
            'matches': match_data,
            'timestamp': time.time(),
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        }
        self._last_fetch = time.time()
        self._save_cache(self._data)
    
    def _load_cache(self):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def _save_cache(self, data):
        try:
            os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
            with open(CACHE_FILE, 'w') as f:
                json.dump(data, f, ensure_ascii=False)
        except:
            pass
    
    def _default_data(self):
        """默认数据"""
        return {
            'matches': [
                {'id':'周日091','home':'巴西','away':'挪威','handicap':-1,
                 'spf_sp':[1.55,3.68,4.70],'rq_sp':[3.08,3.00,2.12]},
                {'id':'周日092','home':'墨西哥','away':'英格兰','handicap':1,
                 'spf_sp':[3.22,3.00,2.06],'rq_sp':[1.60,3.33,4.90]},
                {'id':'周一093','home':'葡萄牙','away':'西班牙','handicap':1,
                 'spf_sp':[3.83,3.30,1.77],'rq_sp':[1.82,3.48,3.42]},
                {'id':'周一094','home':'美国','away':'比利时','handicap':1,
                 'spf_sp':[2.44,3.26,2.42],'rq_sp':[1.42,4.40,5.05]},
                {'id':'周二095','home':'阿根廷','away':'埃及','handicap':1,
                 'spf_sp':[1.23,4.65,10.00],'rq_sp':[1.89,3.35,3.32]},
                {'id':'周二096','home':'瑞士','away':'哥伦比亚','handicap':1,
                 'spf_sp':[2.91,2.82,2.32],'rq_sp':[1.46,3.75,5.65]},
            ],
            'timestamp': time.time(),
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        }
