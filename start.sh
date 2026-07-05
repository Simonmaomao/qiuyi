#! /bin/bash
# 启动体彩智投服务
cd "$(dirname "$0")"

# 检查依赖
python3 -c "import fastapi" 2>/dev/null || {
    echo "安装依赖..."
    pip3 install -r requirements.txt -q
}

echo "🚀 体彩智投 v2.0 启动中..."
echo "📊 访问地址: http://localhost:8899"
echo ""

# 需要将模块路径加入PYTHONPATH
export PYTHONPATH="$PWD:$PYTHONPATH"
python3 -m app.api.server
