"""Zeabur部署入口 - 导入真正的app"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from app.api.server import app
