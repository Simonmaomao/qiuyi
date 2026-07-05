# Zeabur入口 - 将请求转发给实际app
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from app.api.server import app
