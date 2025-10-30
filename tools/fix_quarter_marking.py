#!/usr/bin/env python3
"""
修复季度标记问题
将文件名中的"Unknown"替换为正确的季度标记（Q1, Q2, Q3, Q4）
"""

import os
import re
from datetime import datetime
from pathlib import Path

def get_quarter_from_date(date_str):
    """
    根据日期字符串确定季度
    日期格式: YYYYMMDD
    """
    try:
        # 解析日期
        date_obj = datetime.strptime(date_str, "%Y%m%d")
        month = date_obj.month
        
        # 根据月份确定季度
        if month in [1, 2, 3]:
            return "Q1"
        elif month in [4, 5, 6]:
            return "Q2"
        elif month in [7, 8, 9]:
            return "Q3"
        elif month in [10, 11, 12]:
            return "Q4"
        else:
            return "Unknown"
    except:
        return "Unknown"

def fix_filename_quarter(filename):
    """
    修复文件名中的季度标记
    例如: AAPL_2020_Unknown_20201226_mdna.md -> AAPL_2020_Q4_20201226_mdna.md
    """
    # 匹配模式: TICKER_YEAR_Unknown_DATE_*
    pattern = r'^([A-Z]+)_(\d{4})_Unknown_(\d{8})_(.*)$'
    match = re.match(pattern, filename)
    
    if match:
        ticker, year, date_str, suffix = match.groups()
        quarter = get_quarter_from_date(date_str)
        
        if quarter != "Unknown":
            new_filename = f"{ticker}_{year}_{quarter}_{date_str}_{suffix}"
            return new_filename
    
    return filename

def rename_files_in_directory(directory):
    """
    重命名目录中的所有文件
    """
    renamed_count = 0
    
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if "Unknown" in filename:
                old_path = os.path.join(root, filename)
                new_filename = fix_filename_quarter(filename)
                
                if new_filename != filename:
                    new_path = os.path.join(root, new_filename)
                    
                    try:
                        os.rename(old_path, new_path)
                        print(f"✅ 重命名: {filename} -> {new_filename}")
                        renamed_count += 1
                    except Exception as e:
                        print(f"❌ 重命名失败: {filename} - {e}")
    
    return renamed_count

def main():
    """
    主函数
    """
    print("🔧 开始修复季度标记问题...")
    print("=" * 60)
    
    # 数据目录
    data_dir = "/root/quant/data/dogs_of_30_mdna"
    
    if not os.path.exists(data_dir):
        print(f"❌ 数据目录不存在: {data_dir}")
        return
    
    # 统计重命名前的文件数量
    unknown_files = []
    for root, dirs, files in os.walk(data_dir):
        for filename in files:
            if "Unknown" in filename:
                unknown_files.append(os.path.join(root, filename))
    
    print(f"📊 找到 {len(unknown_files)} 个包含'Unknown'的文件")
    
    if len(unknown_files) == 0:
        print("✅ 没有需要修复的文件")
        return
    
    # 显示一些示例
    print("\n📋 示例文件:")
    for i, file_path in enumerate(unknown_files[:5]):
        print(f"  {i+1}. {os.path.basename(file_path)}")
    if len(unknown_files) > 5:
        print(f"  ... 还有 {len(unknown_files) - 5} 个文件")
    
    # 直接执行修复
    print(f"\n🚀 开始修复 {len(unknown_files)} 个文件...")
    
    # 执行重命名
    renamed_count = rename_files_in_directory(data_dir)
    
    print(f"\n✅ 修复完成!")
    print(f"📊 成功重命名: {renamed_count} 个文件")
    print(f"📊 剩余未处理: {len(unknown_files) - renamed_count} 个文件")

if __name__ == "__main__":
    main()
