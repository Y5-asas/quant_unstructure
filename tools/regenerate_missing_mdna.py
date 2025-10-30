#!/usr/bin/env python3
"""
重新生成缺失的MDNA文件
使用mdna_autobuilder.py来处理所有_cleaned.md文件，生成对应的MDNA文件
"""

import os
import sys
import subprocess
from pathlib import Path

def find_cleaned_files(data_dir, target_tickers=None):
    """
    查找指定ticker的_cleaned.md文件
    """
    cleaned_files = []
    
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.endswith('_cleaned.md'):
                # 如果指定了target_tickers，只处理这些ticker
                if target_tickers:
                    ticker = os.path.basename(root)
                    if ticker in target_tickers:
                        cleaned_files.append(os.path.join(root, file))
                else:
                    cleaned_files.append(os.path.join(root, file))
    
    return cleaned_files

def check_missing_mdna_files(cleaned_files):
    """
    检查哪些cleaned文件缺少对应的MDNA文件
    """
    missing_files = []
    
    for cleaned_file in cleaned_files:
        # 生成对应的MDNA文件名
        base_name = cleaned_file.replace('_cleaned.md', '')
        mdna_json = f"{base_name}_MDNA.json"
        mdna_md = f"{base_name}_MDNA.md"
        
        # 检查是否两个MDNA文件都存在
        if not (os.path.exists(mdna_json) and os.path.exists(mdna_md)):
            missing_files.append(cleaned_file)
    
    return missing_files

def regenerate_mdna_files(missing_files):
    """
    使用mdna_autobuilder.py重新生成MDNA文件
    """
    mdna_autobuilder_path = "/root/quant/data/dogs_of_30_mdna/mdna_autobuilder.py"
    
    if not os.path.exists(mdna_autobuilder_path):
        print(f"❌ 找不到mdna_autobuilder.py: {mdna_autobuilder_path}")
        return False
    
    success_count = 0
    failed_count = 0
    
    for cleaned_file in missing_files:
        try:
            # 从文件路径提取ticker
            path_parts = Path(cleaned_file).parts
            ticker = path_parts[-2]  # 假设目录结构为 .../TICKER/filename
            
            print(f"🔄 处理: {os.path.basename(cleaned_file)} (Ticker: {ticker})")
            
            # 运行mdna_autobuilder.py
            cmd = [
                sys.executable, 
                mdna_autobuilder_path,
                "--input", cleaned_file,
                "--ticker", ticker
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(mdna_autobuilder_path))
            
            if result.returncode == 0:
                print(f"  ✅ 成功生成MDNA文件")
                success_count += 1
            else:
                print(f"  ❌ 生成失败: {result.stderr}")
                failed_count += 1
                
        except Exception as e:
            print(f"  ❌ 处理异常: {e}")
            failed_count += 1
    
    return success_count, failed_count

def main():
    """
    主函数
    """
    print("🔄 开始重新生成缺失的MDNA文件...")
    print("=" * 60)
    
    # 数据目录
    data_dir = "/root/quant/data/dogs_of_30_mdna"
    
    if not os.path.exists(data_dir):
        print(f"❌ 数据目录不存在: {data_dir}")
        return
    
    # 只处理AMZN和CRM的cleaned文件
    target_tickers = ["AMZN", "CRM"]
    print(f"🔍 查找 {target_tickers} 的_cleaned.md文件...")
    cleaned_files = find_cleaned_files(data_dir, target_tickers)
    print(f"📊 找到 {len(cleaned_files)} 个_cleaned.md文件")
    
    if len(cleaned_files) == 0:
        print("❌ 没有找到_cleaned.md文件")
        return
    
    # 检查缺失的MDNA文件
    print("\n🔍 检查缺失的MDNA文件...")
    missing_files = check_missing_mdna_files(cleaned_files)
    print(f"📊 找到 {len(missing_files)} 个缺失MDNA文件的_cleaned.md")
    
    if len(missing_files) == 0:
        print("✅ 所有文件都有对应的MDNA文件")
        return
    
    # 显示一些示例
    print("\n📋 缺失MDNA文件的示例:")
    for i, file_path in enumerate(missing_files[:5]):
        print(f"  {i+1}. {os.path.basename(file_path)}")
    if len(missing_files) > 5:
        print(f"  ... 还有 {len(missing_files) - 5} 个文件")
    
    # 重新生成MDNA文件
    print(f"\n🚀 开始重新生成 {len(missing_files)} 个MDNA文件...")
    success_count, failed_count = regenerate_mdna_files(missing_files)
    
    print(f"\n✅ 重新生成完成!")
    print(f"📊 成功生成: {success_count} 个文件")
    print(f"📊 生成失败: {failed_count} 个文件")
    
    if failed_count > 0:
        print(f"\n⚠️  有 {failed_count} 个文件生成失败，请检查错误信息")

if __name__ == "__main__":
    main()
