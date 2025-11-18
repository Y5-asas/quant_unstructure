#!/bin/bash
# 每日自动获取道琼斯30成分股数据的脚本
# 使用方法：将此脚本添加到 crontab 中，每天交易结束后运行

# 设置工作目录（请根据实际情况修改）
WORK_DIR="/Users/y5/Downloads/alpha_arena/quant_unstructure"
CONDA_ENV="alpha_arena_env"

# 切换到工作目录
cd "$WORK_DIR" || exit 1

# 激活 conda 环境并运行脚本
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$CONDA_ENV"

# 运行数据获取脚本（仅获取最新数据）
python utils/fetch_dow30_data.py --latest --days 1 --output-dir original_data/

# 记录日志
echo "$(date): 道琼斯30数据更新完成" >> logs/daily_fetch.log

