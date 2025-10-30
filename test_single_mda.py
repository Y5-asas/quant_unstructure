#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试单个MDA文件的情感分析
"""

import os
import sys
import json
from pathlib import Path

# 设置环境变量
os.environ['HF_HOME'] = "/root/autodl-tmp/huggingface_cache"
os.environ['HF_ENDPOINT'] = "https://hf-mirror.com"
os.environ['HF_HUB_DISABLE_TELEMETRY'] = "1"
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = "1000"

# 添加路径
sys.path.append('/root/quant/ai_analysis')
sys.path.append('/root/quant/backtesting')

from financial_sentiment_analyzer import FinancialSentimentAnalyzer

def test_single_mda():
    """测试单个MDA文件的情感分析"""
    print("🚀 测试单个MDA文件情感分析")
    print("=" * 50)
    
    # 初始化分析器
    analyzer = FinancialSentimentAnalyzer()
    
    # 加载模型
    print("📊 加载ChatGLM模型...")
    if not analyzer.load_model():
        print("❌ 模型加载失败")
        return False
    
    print("✅ 模型加载成功")
    
    # 测试文件路径
    test_files = [
        "/root/quant/data/dogs_of_30_mdna/AAPL/AAPL_2024_Q1_20240330_MDNA.json",
        "/root/quant/data/dogs_of_30_mdna/AAPL/AAPL_2024_Q2_20240629_MDNA.json",
        "/root/quant/data/dogs_of_30_mdna/MSFT/MSFT_2024_Q1_20240331_MDNA.json"
    ]
    
    results = []
    
    for i, file_path in enumerate(test_files, 1):
        if not os.path.exists(file_path):
            print(f"⚠️ 文件不存在: {file_path}")
            continue
            
        print(f"\n📄 测试文件 {i}: {Path(file_path).name}")
        
        try:
            # 读取JSON文件
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取文本内容
            text_content = ""
            if 'sections' in data:
                for section_name, section_content in data['sections'].items():
                    if isinstance(section_content, str):
                        text_content += section_content + "\n"
                    elif isinstance(section_content, dict):
                        for key, value in section_content.items():
                            if isinstance(value, str):
                                text_content += value + "\n"
            
            # 限制文本长度
            if len(text_content) > 2000:
                text_content = text_content[:2000] + "..."
            
            print(f"📝 提取文本长度: {len(text_content)} 字符")
            
            # 分析情感
            result = analyzer.analyze_sentiment(text_content)
            
            if 'error' in result:
                print(f"❌ 分析失败: {result['error']}")
            else:
                print(f"✅ 情感评分: {result['score']:.1f}/10.0")
                print(f"📊 情感因子: {result['score']/10.0:.3f}")
                if 'factors' in result:
                    print(f"🔍 主要因素: {result['factors'][:100]}...")
                
                # 保存结果
                result['file_path'] = file_path
                result['company'] = data.get('meta', {}).get('ticker', 'Unknown')
                result['period'] = f"{data.get('meta', {}).get('fiscal_year', 'Unknown')} {data.get('meta', {}).get('fiscal_period', 'Unknown')}"
                results.append(result)
            
        except Exception as e:
            print(f"❌ 处理文件失败: {e}")
            continue
    
    # 生成汇总报告
    if results:
        print(f"\n📊 汇总报告:")
        print(f"成功分析: {len(results)} 个文件")
        
        scores = [r['score'] for r in results]
        print(f"平均评分: {sum(scores)/len(scores):.2f}")
        print(f"最高评分: {max(scores):.2f}")
        print(f"最低评分: {min(scores):.2f}")
        
        print(f"\n📈 详细结果:")
        for result in results:
            company = result.get('company', 'Unknown')
            period = result.get('period', 'Unknown')
            score = result['score']
            print(f"  {company} {period}: {score:.1f}/10.0")
        
        # 保存结果
        output_file = "/root/quant/data/test_sentiment_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 结果已保存到: {output_file}")
    
    print("\n🎉 测试完成!")
    return True

if __name__ == "__main__":
    test_single_mda()
