#!/usr/bin/env python3
"""
财务报告精简工具
移除冗余内容，保留关键财务数据
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set

class FinancialReportCleaner:
    def __init__(self):
        # 冗余部分的关键词模式
        self.redundant_patterns = [
            r'## Available Information.*?(?=\n##|\n###|$)',
            r'The Company periodically provides certain information for investors.*?(?=\n##|\n###|$)',
            r'The information contained on the websites referenced in this Form.*?(?=\n##|\n###|$)',
            r'Forward-looking statements.*?(?=\n##|\n###|$)',
            r'## Business Seasonality and Product Introductions.*?(?=\n##|\n###|$)',
            r'The Company has historically experienced higher net sales.*?(?=\n##|\n###|$)',
            r'## COVID-19 Update.*?(?=\n##|\n###|$)',
            r'The COVID-19 pandemic has prompted.*?(?=\n##|\n###|$)',
            r'## Critical Accounting Policies and Estimates.*?(?=\n##|\n###|$)',
            r'The preparation of financial statements.*?(?=\n##|\n###|$)',
            r'Refer to Part I, Item 1A.*?Risk Factors.*?(?=\n##|\n###|$)',
            r'Cautionary Note Concerning Factors That May Affect Future Results.*?(?=\n##|\n###|$)',
        ]
        
        # 需要保留的关键部分
        self.essential_sections = [
            'Results of Operations',
            'Products and Services Performance',
            'Segment Operating Performance',
            'Gross Margin',
            'Operating Expenses',
            'Liquidity and Capital Resources',
            'Financial Condition',
            'Performance by Business Segment',
            'Net Sales',
            'Operating Income',
            'Net Income',
        ]
        
        # 财务数据模式
        self.financial_data_patterns = [
            r'\[表格: Table with.*?\]',  # 表格标记
            r'\d{1,3}(?:,\d{3})*\s*million',  # 百万数字
            r'\d{1,3}(?:,\d{3})*\s*billion',  # 十亿数字
            r'\d+\.?\d*%',  # 百分比
            r'increased by \$[\d,]+',  # 增长金额
            r'decreased by \$[\d,]+',  # 减少金额
        ]
    
    def clean_report(self, content: str) -> str:
        """移除冗余内容"""
        cleaned_content = content
        
        # 移除冗余部分
        for pattern in self.redundant_patterns:
            cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.DOTALL)
        
        # 清理多余的空行
        cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content)
        
        return cleaned_content.strip()
    
    def extract_key_financial_data(self, content: str) -> Dict:
        """提取关键财务数据"""
        data = {
            'sections': {},
            'financial_metrics': {},
            'tables': []
        }
        
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            # 检测章节标题
            if line.startswith('## ') or line.startswith('### '):
                if current_section and current_content:
                    data['sections'][current_section] = '\n'.join(current_content).strip()
                
                current_section = line.strip('# ').strip()
                current_content = []
                
                # 只保留关键章节
                if any(essential in current_section for essential in self.essential_sections):
                    continue
                else:
                    current_section = None
            elif current_section:
                current_content.append(line)
                
                # 提取表格
                if '[表格: Table with' in line:
                    data['tables'].append(line.strip())
        
        # 处理最后一个章节
        if current_section and current_content:
            data['sections'][current_section] = '\n'.join(current_content).strip()
        
        # 提取财务指标
        all_text = ' '.join(lines)
        
        # 查找关键财务数字
        revenue_pattern = r'Net sales of \$([\d,]+)\s*million'
        revenue_matches = re.findall(revenue_pattern, all_text)
        if revenue_matches:
            data['financial_metrics']['net_sales'] = [m.replace(',', '') for m in revenue_matches]
        
        # 查找增长率
        growth_pattern = r'increased by (\d+\.?\d*)%'
        growth_matches = re.findall(growth_pattern, all_text)
        if growth_matches:
            data['financial_metrics']['growth_rates'] = growth_matches
        
        return data
    
    def process_all_reports(self, base_dir: str):
        """处理所有财务报告"""
        base_path = Path(base_dir)
        processed_data = {}
        
        for company_dir in base_path.iterdir():
            if company_dir.is_dir():
                company = company_dir.name
                processed_data[company] = {}
                
                for report_file in company_dir.glob('*_mdna.md'):
                    # 提取报告信息
                    filename = report_file.stem
                    parts = filename.split('_')
                    if len(parts) >= 4:
                        year = parts[1]
                        quarter = parts[2]
                        date = parts[3]
                        
                        # 读取报告内容
                        with open(report_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # 清理报告
                        cleaned_content = self.clean_report(content)
                        
                        # 提取关键数据
                        key_data = self.extract_key_financial_data(cleaned_content)
                        
                        # 保存处理后的数据
                        report_key = f"{year}_{quarter}_{date}"
                        processed_data[company][report_key] = {
                            'cleaned_content': cleaned_content,
                            'key_data': key_data,
                            'original_file': str(report_file)
                        }
                        
                        # 创建精简版报告文件
                        output_file = report_file.parent / f"{filename}_cleaned.md"
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(cleaned_content)
        
        # 保存汇总数据
        with open(base_path / 'processed_financial_data.json', 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, indent=2, ensure_ascii=False)
        
        return processed_data
    
    def generate_summary_report(self, processed_data: Dict) -> str:
        """生成汇总报告"""
        summary = "# 财务报告精简汇总\n\n"
        
        for company, reports in processed_data.items():
            summary += f"## {company}\n\n"
            
            for report_key, data in reports.items():
                summary += f"### {report_key}\n\n"
                
                # 添加关键财务指标
                if data['key_data']['financial_metrics']:
                    summary += "**关键财务指标:**\n"
                    for metric, values in data['key_data']['financial_metrics'].items():
                        summary += f"- {metric}: {', '.join(values[:5])}\n"  # 只显示前5个值
                    summary += "\n"
                
                # 添加章节概览
                if data['key_data']['sections']:
                    summary += "**包含章节:**\n"
                    for section in data['key_data']['sections'].keys():
                        summary += f"- {section}\n"
                    summary += "\n"
                
                summary += "---\n\n"
        
        return summary

def main():
    cleaner = FinancialReportCleaner()
    
    # 处理所有报告
    print("开始处理财务报告...")
    processed_data = cleaner.process_all_reports('dogs_of_30_mdna')
    
    # 生成汇总报告
    summary = cleaner.generate_summary_report(processed_data)
    
    # 保存汇总报告
    with open('financial_reports_summary.md', 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print(f"处理完成！共处理 {len(processed_data)} 家公司的报告")
    print("精简版报告保存在原目录，文件名后缀为 _cleaned.md")
    print("汇总数据保存在 processed_financial_data.json")
    print("汇总报告保存在 financial_reports_summary.md")

if __name__ == "__main__":
    main()