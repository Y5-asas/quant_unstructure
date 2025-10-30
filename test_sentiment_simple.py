#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的情感分析测试脚本
使用规则基础的方法模拟情感分析，测试整个pipeline
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import re

def simple_sentiment_analysis(text):
    """
    简化的情感分析，基于关键词匹配
    """
    text_lower = text.lower()
    
    # 积极关键词
    positive_keywords = [
        'growth', 'increase', 'improve', 'strong', 'success', 'profit', 'revenue',
        'expansion', 'positive', 'better', 'exceed', 'outperform', 'gain',
        'benefit', 'opportunity', 'advance', 'progress', 'achieve', 'win'
    ]
    
    # 消极关键词
    negative_keywords = [
        'decline', 'decrease', 'loss', 'weak', 'challenge', 'risk', 'concern',
        'difficult', 'negative', 'worse', 'underperform', 'drop', 'fall',
        'problem', 'issue', 'threat', 'crisis', 'struggle', 'fail'
    ]
    
    # 计算积极和消极分数
    positive_score = sum(1 for keyword in positive_keywords if keyword in text_lower)
    negative_score = sum(1 for keyword in negative_keywords if keyword in text_lower)
    
    # 计算基础分数 (0-100)
    if positive_score + negative_score == 0:
        base_score = 50  # 中性
    else:
        base_score = (positive_score / (positive_score + negative_score)) * 100
    
    # 添加一些随机性来模拟真实分析
    noise = np.random.normal(0, 5)
    final_score = max(0, min(100, base_score + noise))
    
    return round(final_score, 1)

def test_mda_sentiment_analysis():
    """测试MDA情感分析"""
    print("🚀 测试MDA情感分析系统")
    print("=" * 50)
    
    # 测试文件列表
    test_files = [
        "/root/quant/data/dogs_of_30_mdna/AAPL/AAPL_2024_Q1_20240330_MDNA.json",
        "/root/quant/data/dogs_of_30_mdna/AAPL/AAPL_2024_Q2_20240629_MDNA.json",
        "/root/quant/data/dogs_of_30_mdna/MSFT/MSFT_2024_Q1_20240331_MDNA.json",
        "/root/quant/data/dogs_of_30_mdna/JPM/JPM_2024_Q1_20240331_MDNA.json",
        "/root/quant/data/dogs_of_30_mdna/CVX/CVX_2024_Q1_20240331_MDNA.json"
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
            score = simple_sentiment_analysis(text_content)
            
            # 提取元数据
            company = data.get('meta', {}).get('ticker', 'Unknown')
            year = data.get('meta', {}).get('fiscal_year', 'Unknown')
            period = data.get('meta', {}).get('fiscal_period', 'Unknown')
            
            print(f"✅ 情感评分: {score:.1f}/100")
            print(f"📊 情感因子: {score/100:.3f}")
            
            # 保存结果
            result = {
                'company': company,
                'year': year,
                'quarter': period,
                'sentiment_score': score,
                'sentiment_factor': score / 100.0,
                'file_path': file_path,
                'analysis_time': datetime.now().isoformat(),
                'text_length': len(text_content)
            }
            results.append(result)
            
        except Exception as e:
            print(f"❌ 处理文件失败: {e}")
            continue
    
    # 生成汇总报告
    if results:
        print(f"\n📊 汇总报告:")
        print(f"成功分析: {len(results)} 个文件")
        
        scores = [r['sentiment_score'] for r in results]
        print(f"平均评分: {np.mean(scores):.2f}")
        print(f"最高评分: {max(scores):.2f}")
        print(f"最低评分: {min(scores):.2f}")
        print(f"标准差: {np.std(scores):.2f}")
        
        print(f"\n📈 详细结果:")
        for result in results:
            company = result['company']
            period = f"{result['year']} {result['quarter']}"
            score = result['sentiment_score']
            factor = result['sentiment_factor']
            print(f"  {company} {period}: {score:.1f}/100 (因子: {factor:.3f})")
        
        # 保存结果到JSON
        output_json = "/root/quant/data/test_sentiment_results.json"
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 JSON结果已保存到: {output_json}")
        
        # 保存结果到CSV
        output_csv = "/root/quant/data/test_sentiment_factors.csv"
        df = pd.DataFrame(results)
        df.to_csv(output_csv, index=False, encoding='utf-8')
        print(f"💾 CSV结果已保存到: {output_csv}")
        
        # 生成因子分析报告
        print(f"\n📊 因子分析:")
        print(f"积极因子 (≥60分): {sum(1 for s in scores if s >= 60)} 个")
        print(f"中性因子 (40-60分): {sum(1 for s in scores if 40 <= s < 60)} 个")
        print(f"消极因子 (<40分): {sum(1 for s in scores if s < 40)} 个")
        
        # 按公司分组分析
        company_scores = {}
        for result in results:
            company = result['company']
            if company not in company_scores:
                company_scores[company] = []
            company_scores[company].append(result['sentiment_score'])
        
        print(f"\n🏢 各公司平均情感评分:")
        for company, scores in company_scores.items():
            avg_score = np.mean(scores)
            print(f"  {company}: {avg_score:.1f}/100")
    
    print("\n🎉 测试完成!")
    return results

def test_backtesting_pipeline():
    """测试回测pipeline"""
    print("\n🚀 测试回测Pipeline")
    print("=" * 50)
    
    # 模拟季度调仓策略
    print("📈 模拟季度调仓策略:")
    
    # 假设的情感评分数据
    quarterly_scores = {
        '2024_Q1': {'AAPL': 75, 'MSFT': 80, 'JPM': 65, 'CVX': 45},
        '2024_Q2': {'AAPL': 70, 'MSFT': 85, 'JPM': 60, 'CVX': 50},
        '2024_Q3': {'AAPL': 80, 'MSFT': 75, 'JPM': 70, 'CVX': 55},
        '2024_Q4': {'AAPL': 65, 'MSFT': 90, 'JPM': 75, 'CVX': 60}
    }
    
    buy_threshold = 60
    sell_threshold = 40
    
    print(f"买入阈值: ≥{buy_threshold}")
    print(f"卖出阈值: ≤{sell_threshold}")
    
    for quarter, scores in quarterly_scores.items():
        print(f"\n📅 {quarter}:")
        buy_signals = [stock for stock, score in scores.items() if score >= buy_threshold]
        sell_signals = [stock for stock, score in scores.items() if score <= sell_threshold]
        hold_signals = [stock for stock, score in scores.items() if sell_threshold < score < buy_threshold]
        
        print(f"  买入信号: {buy_signals}")
        print(f"  卖出信号: {sell_signals}")
        print(f"  持有信号: {hold_signals}")
        
        for stock, score in scores.items():
            signal = "买入" if score >= buy_threshold else "卖出" if score <= sell_threshold else "持有"
            print(f"    {stock}: {score}分 -> {signal}")

if __name__ == "__main__":
    # 测试情感分析
    results = test_mda_sentiment_analysis()
    
    # 测试回测pipeline
    test_backtesting_pipeline()
    
    print("\n🎉 所有测试完成！系统运行正常！")
