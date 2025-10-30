#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财报情感分析系统
使用ChatGLM模型对财务报告进行情感分析，生成0.0-10.0的情感因子评分
"""

import os
# 设置环境变量
os.environ['HF_HOME'] = "/root/autodl-tmp/huggingface_cache"
os.environ['HF_ENDPOINT'] = "https://hf-mirror.com"
os.environ['HF_HUB_DISABLE_TELEMETRY'] = "1"
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = "1000"
import torch
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from transformers import AutoTokenizer, AutoModel
import pandas as pd
import numpy as np



class FinancialSentimentAnalyzer:
    def __init__(self, model_name="THUDM/chatglm2-6b"):
        """初始化情感分析器"""
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = None
        
        # 情感分析提示词模板
        self.sentiment_prompt_template = """
你是一位专业的金融分析师。请仔细分析以下财务报告文本，评估其情感倾向。

评分标准：
- 0.0-3.0：极度消极（重大亏损、法律风险、经营困难等）
- 3.1-5.0：消极（业绩下滑、成本上升、市场担忧等）
- 5.1-7.0：中性（平稳表现、常规经营、无重大利好或利空）
- 7.1-9.0：积极（业绩增长、市场份额提升、新产品成功等）
- 9.1-10.0：极度积极（突破性增长、重大利好、远超预期等）

财务报告文本：
{text}

请按以下格式返回分析结果：
1. 情感评分（0.0-10.0）：[具体分数]
2. 主要情感因素：[列出2-3个关键因素]
3. 详细分析：[简要说明评分理由]

分析结果：
"""
        
        # 批量处理提示词
        self.batch_prompt_template = """
请分析以下{company}在{period}的财务报告，重点关注：

1. 业绩表现（收入、利润、增长情况）
2. 市场前景和战略展望
3. 风险因素和挑战
4. 创新和竞争优势

报告内容：
{text}

请提供一个0.0-10.0的情感评分，并简要说明主要理由。
格式：
评分：[分数]
理由：[简要说明]
"""
    
    def load_model(self):
        """加载ChatGLM模型"""
        print(f"🔍 正在加载模型: {self.model_name}")
        
        try:
            # 加载tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, 
                trust_remote_code=True
            )
            print("✅ Tokenizer加载成功")
            
            # 加载模型
            self.model = AutoModel.from_pretrained(
                self.model_name, 
                trust_remote_code=True, 
                device_map='auto',
                torch_dtype=torch.float16
            )
            print("✅ 模型加载成功")
            
            self.device = next(self.model.parameters()).device
            print(f"📱 模型运行设备: {self.device}")
            
            return True
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            return False
    
    def extract_financial_content(self, file_path: str) -> str:
        """提取财务报告的关键内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取关键部分
            sections = re.split(r'## ', content)
            key_sections = []
            
            for section in sections:
                # 保留关键财务部分
                if any(keyword in section.lower() for keyword in [
                    'results of operations',
                    'products and services performance',
                    'segment operating performance',
                    'gross margin',
                    'operating expenses',
                    'liquidity and capital resources',
                    'financial condition',
                    'net sales',
                    'operating income',
                    'revenue'
                ]):
                    # 清理表格标记
                    section = re.sub(r'\[表格: Table with.*?\]', '', section)
                    key_sections.append(section.strip())
            
            # 限制内容长度
            combined_content = '\n\n'.join(key_sections[:5])  # 只取前5个部分
            if len(combined_content) > 3000:
                combined_content = combined_content[:3000] + "..."
            
            return combined_content if combined_content else content[:2000]
            
        except Exception as e:
            print(f"❌ 读取文件失败 {file_path}: {e}")
            return ""
    
    def analyze_sentiment(self, text: str, max_retries: int = 3) -> Dict:
        """分析文本情感"""
        if not self.model or not self.tokenizer:
            return {"error": "模型未加载"}
        
        prompt = self.sentiment_prompt_template.format(text=text)
        
        for attempt in range(max_retries):
            try:
                print(f"🔄 尝试分析 (第{attempt + 1}次)...")
                
                # 使用chat方法
                response, _ = self.model.chat(
                    self.tokenizer, 
                    prompt, 
                    history=[],
                    temperature=0.3,  # 降低温度以获得更一致的结果
                    top_p=0.9
                )
                
                # 解析响应
                result = self.parse_sentiment_response(response)
                
                if result and 'score' in result:
                    return result
                    
            except Exception as e:
                print(f"❌ 分析失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                time.sleep(2)  # 等待后重试
        
        return {"error": "分析失败", "raw_response": response if 'response' in locals() else None}
    
    def parse_sentiment_response(self, response: str) -> Optional[Dict]:
        """解析模型响应，提取情感评分"""
        try:
            # 提取评分
            score_match = re.search(r'情感评分.*?(\d+\.?\d*)', response)
            if score_match:
                score = float(score_match.group(1))
                # 确保评分在0-10范围内
                score = max(0.0, min(10.0, score))
            else:
                # 尝试其他格式
                score_match = re.search(r'评分[：:]\s*(\d+\.?\d*)', response)
                if score_match:
                    score = float(score_match.group(1))
                    score = max(0.0, min(10.0, score))
                else:
                    return None
            
            # 提取情感因素
            factors_match = re.search(r'主要情感因素[：:]\s*(.*?)(?=\n\d+\.|$)', response, re.DOTALL)
            factors = factors_match.group(1).strip() if factors_match else ""
            
            # 提取详细分析
            analysis_match = re.search(r'详细分析[：:]\s*(.*)', response, re.DOTALL)
            analysis = analysis_match.group(1).strip() if analysis_match else response
            
            return {
                'score': score,
                'factors': factors,
                'analysis': analysis,
                'raw_response': response
            }
            
        except Exception as e:
            print(f"❌ 解析响应失败: {e}")
            return None
    
    def analyze_single_report(self, file_path: str) -> Dict:
        """分析单个财务报告"""
        print(f"\n📊 分析报告: {file_path}")
        
        # 提取公司信息
        path_parts = Path(file_path).parts
        company = path_parts[-2] if len(path_parts) >= 2 else "Unknown"
        filename = Path(file_path).stem
        
        # 提取财务内容
        content = self.extract_financial_content(file_path)
        if not content:
            return {"error": "无法提取内容"}
        
        print(f"📄 提取内容长度: {len(content)} 字符")
        
        # 分析情感
        result = self.analyze_sentiment(content)
        
        # 添加元数据
        if 'error' not in result:
            result.update({
                'company': company,
                'filename': filename,
                'file_path': file_path,
                'analysis_time': datetime.now().isoformat()
            })
        
        return result
    
    def batch_analyze_reports(self, reports_dir: str, output_file: str = None):
        """批量分析财务报告"""
        print(f"\n🚀 开始批量分析财报...")
        
        # 查找所有精简版报告
        report_files = []
        for root, dirs, files in os.walk(reports_dir):
            for file in files:
                if file.endswith('.json'):
                    report_files.append(os.path.join(root, file))
        
        print(f"📂 找到 {len(report_files)} 份精简报告")
        
        results = []
        successful = 0
        failed = 0
        
        for i, file_path in enumerate(report_files, 1):
            print(f"\n{'='*50}")
            print(f"进度: {i}/{len(report_files)}")
            
            result = self.analyze_single_report(file_path)
            
            if 'error' in result:
                print(f"❌ 分析失败: {result['error']}")
                failed += 1
            else:
                print(f"✅ 分析成功 - 情感评分: {result['score']:.1f}")
                successful += 1
            
            results.append(result)
            
            # 保存中间结果
            if i % 5 == 0 or i == len(report_files):
                self.save_results(results, output_file or f"sentiment_results_temp_{i}.json")
                print(f"💾 已保存中间结果")
        
        # 保存最终结果
        final_output = output_file or "financial_sentiment_results.json"
        self.save_results(results, final_output)
        
        # 生成汇总报告
        self.generate_summary_report(results, "sentiment_analysis_summary.md")
        
        print(f"\n🎉 批量分析完成!")
        print(f"✅ 成功: {successful}")
        print(f"❌ 失败: {failed}")
        print(f"📊 结果已保存到: {final_output}")
        
        return results
    
    def save_results(self, results: List[Dict], filename: str):
        """保存分析结果"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    
    def generate_summary_report(self, results: List[Dict], filename: str):
        """生成汇总报告"""
        # 统计数据
        valid_results = [r for r in results if 'score' in r]
        
        if not valid_results:
            return
        
        scores = [r['score'] for r in valid_results]
        companies = {}
        
        for result in valid_results:
            company = result['company']
            if company not in companies:
                companies[company] = []
            companies[company].append(result['score'])
        
        # 生成报告
        report = "# 财报情感分析汇总报告\n\n"
        report += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 总体统计
        report += "## 总体统计\n\n"
        report += f"- 分析报告总数: {len(valid_results)}\n"
        report += f"- 平均情感评分: {np.mean(scores):.2f}\n"
        report += f"- 最高评分: {max(scores):.2f}\n"
        report += f"- 最低评分: {min(scores):.2f}\n"
        report += f"- 标准差: {np.std(scores):.2f}\n\n"
        
        # 评分分布
        report += "## 评分分布\n\n"
        ranges = [(0, 3), (3, 5), (5, 7), (7, 9), (9, 10)]
        labels = ['极度消极', '消极', '中性', '积极', '极度积极']
        
        for (low, high), label in zip(ranges, labels):
            count = sum(1 for s in scores if low <= s < high)
            report += f"- {label} ({low}-{high}): {count} ({count/len(scores)*100:.1f}%)\n"
        
        # 各公司表现
        report += "\n## 各公司情感评分\n\n"
        for company, company_scores in companies.items():
            avg_score = np.mean(company_scores)
            report += f"### {company}\n"
            report += f"- 平均评分: {avg_score:.2f}\n"
            report += f"- 报告数量: {len(company_scores)}\n"
            report += f"- 评分范围: {min(company_scores):.2f} - {max(company_scores):.2f}\n\n"
        
        # 保存报告
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
    
    def create_sentiment_factor_csv(self, results: List[Dict], filename: str = "sentiment_factors.csv"):
        """生成情感因子CSV文件"""
        rows = []
        
        for result in results:
            if 'score' in result:
                # 从文件名提取时间信息
                filename = result['filename']
                parts = filename.split('_')
                
                # 解析时间和季度
                year = parts[1] if len(parts) > 1 else "Unknown"
                quarter = parts[2] if len(parts) > 2 else "Unknown"
                date = parts[3] if len(parts) > 3 else "Unknown"
                
                row = {
                    'company': result['company'],
                    'year': year,
                    'quarter': quarter,
                    'date': date,
                    'sentiment_score': result['score'],
                    'sentiment_factor': result['score'] / 10.0,  # 归一化到0-1
                    'analysis_time': result.get('analysis_time', ''),
                    'factors': result.get('factors', '').replace('\n', ' ')
                }
                rows.append(row)
        
        # 创建DataFrame并保存
        df = pd.DataFrame(rows)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"📊 情感因子CSV已保存到: {filename}")
        
        return df

def main():
    """主函数"""
    print("🚀 启动财报情感分析系统...")
    print("=" * 60)
    
    # 初始化分析器
    analyzer = FinancialSentimentAnalyzer()
    
    # 加载模型
    if not analyzer.load_model():
        print("❌ 模型加载失败，程序退出")
        return
    
    # 设置输入输出路径
    reports_dir = "../data/dogs_of_30_mdna"
    output_json = "../data/financial_sentiment_analysis.json"
    output_csv = "../data/sentiment_factors.csv"
    
    # 批量分析
    results = analyzer.batch_analyze_reports(reports_dir, output_json)
    
    # 生成CSV文件
    if results:
        analyzer.create_sentiment_factor_csv(results, output_csv)
    
    print("\n🎉 所有分析完成！")

if __name__ == "__main__":
    main()