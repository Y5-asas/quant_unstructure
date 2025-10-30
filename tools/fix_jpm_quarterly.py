#!/usr/bin/env python3
"""
修复JPM季报中有问题的文件
这些文件只有3行，内容都是目录信息，需要重新生成
"""

from sec_downloader import Downloader
import sec_parser as sp
from sec_downloader.types import RequestedFilings
import os
from datetime import datetime
from typing import List
import logging

# ==================== 1. 配置 ====================
# 日志配置
logger = logging.getLogger("JPM_Quarterly_Fixer")
logger.setLevel(logging.INFO)

# 创建文件处理器
log_filename = "jpm_quarterly_fixer.log"
file_handler = logging.FileHandler(log_filename, mode='a', encoding='utf-8')
file_handler.setLevel(logging.INFO)

# 设置日志格式
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# 控制台输出
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# 下载器配置
dl = Downloader("HKU", "u303637086@connect.hku.hk")

# 输出目录
output_dir = "dogs_of_30_mdna/JPM"
os.makedirs(output_dir, exist_ok=True)

def extract_jpm_mdna_quarterly(elements: List, metadata) -> str:
    """
    专门针对JPM季报的MD&A提取逻辑
    """
    print(f"    正在使用JPM季报特定的MD&A提取逻辑...")
    
    # 构建文档树
    tree_parts = sp.TreeBuilder().build(elements)
    
    # 查找包含MD&A内容的章节
    mdna_content = []
    
    # 策略1: 查找"Item 2"章节（季报中的MD&A）
    item2_section = None
    for part in tree_parts:
        for section in part.children:
            if isinstance(section.semantic_element, sp.TitleElement):
                title_text = section.semantic_element.text.lower()
                if "item 2" in title_text and "management" in title_text:
                    item2_section = section
                    print(f"      找到Item 2 MD&A章节: {section.semantic_element.text}")
                    break
        if item2_section:
            break
    
    if item2_section:
        # 从Item 2章节开始提取内容
        print(f"      从Item 2章节提取MD&A内容...")
        
        # 获取所有后代元素
        descendants = item2_section.get_descendants()
        
        # 查找MD&A相关的标题和内容
        mdna_sections = []
        current_section = None
        
        for element in descendants:
            if isinstance(element.semantic_element, sp.TitleElement):
                title_text = element.semantic_element.text.lower()
                
                # 检查是否是MD&A相关章节
                if any(keyword in title_text for keyword in [
                    "management", "discussion", "analysis", "financial", "operations",
                    "consolidated", "business", "segment", "risk", "capital",
                    "introduction", "executive", "overview"
                ]):
                    current_section = element
                    mdna_sections.append(element)
                    print(f"        找到MD&A相关章节: {element.semantic_element.text}")
                    
            elif isinstance(element.semantic_element, sp.TextElement) and current_section:
                # 添加文本内容
                mdna_content.append(element.semantic_element.text)
    
    # 策略2: 如果没找到Item 2，搜索所有包含MD&A关键词的章节
    if not mdna_content:
        print(f"      策略1失败，尝试策略2: 搜索所有MD&A相关内容...")
        
        for part in tree_parts:
            for section in part.children:
                if isinstance(section.semantic_element, sp.TitleElement):
                    title_text = section.semantic_element.text.lower()
                    
                    # 检查是否是MD&A相关章节
                    if any(keyword in title_text for keyword in [
                        "management", "discussion", "analysis", "financial", "operations",
                        "consolidated", "business", "segment", "risk", "capital"
                    ]):
                        print(f"        找到MD&A相关章节: {section.semantic_element.text}")
                        
                        # 获取该章节的所有内容
                        descendants = section.get_descendants()
                        for element in descendants:
                            if isinstance(element.semantic_element, sp.TextElement):
                                mdna_content.append(element.semantic_element.text)
                            elif isinstance(element.semantic_element, sp.TitleElement):
                                mdna_content.append(f"\n## {element.semantic_element.text}\n")
                            elif isinstance(element.semantic_element, sp.TableElement):
                                # 对于表格元素，尝试获取表格信息，如果失败则使用默认标识
                                try:
                                    if hasattr(element.semantic_element, 'get_summary'):
                                        table_summary = element.semantic_element.get_summary()
                                        mdna_content.append(f"\n[表格: {table_summary}]\n")
                                    else:
                                        mdna_content.append(f"\n[表格内容]\n")
                                except:
                                    mdna_content.append(f"\n[表格内容]\n")
    
    # 策略3: 如果还是没有内容，尝试提取整个文档的MD&A相关部分
    if not mdna_content:
        print(f"      策略2失败，尝试策略3: 提取整个文档的MD&A相关部分...")
        
        # 搜索所有元素，查找包含MD&A关键词的内容
        for part in tree_parts:
            for section in part.children:
                descendants = section.get_descendants()
                for element in descendants:
                    if isinstance(element.semantic_element, sp.TextElement):
                        text = element.semantic_element.text.lower()
                        if any(keyword in text for keyword in [
                            "management", "discussion", "analysis", "financial", "operations"
                        ]):
                            # 获取该元素的父章节标题
                            parent_title = ""
                            if hasattr(element, 'parent') and element.parent:
                                if hasattr(element.parent, 'semantic_element') and isinstance(element.parent.semantic_element, sp.TitleElement):
                                    parent_title = element.parent.semantic_element.text
                            
                            if parent_title:
                                mdna_content.append(f"\n## {parent_title}\n")
                            mdna_content.append(element.semantic_element.text)
    
    if mdna_content:
        # 构建markdown内容
        markdown = f"# JPMorgan Chase & Co. - 10-Q for {metadata.report_date}\n\n"
        markdown += "## Management's Discussion and Analysis\n\n"
        markdown += "**注意**: 此文件使用JPM特定的MD&A提取逻辑，因为JPM的财报结构与标准格式不同。\n\n\n"
        
        # 添加提取的内容
        markdown += "\n\n".join(mdna_content)
        
        return markdown
    else:
        return None

def process_jpm_quarterly_filing(ticker: str, form_type: str, report_date: str, filing_date: str, url: str):
    """
    处理单个JPM季报文件
    """
    print(f"正在处理 {ticker} 的 {form_type} 文件: {report_date}")
    
    try:
        # 下载HTML
        html = dl.download_filing(url=url).decode('utf-8', errors='ignore')
        
        # 解析HTML
        elements: List = sp.Edgar10QParser().parse(html)
        
        # 提取MD&A
        mdna_content = extract_jpm_mdna_quarterly(elements, type('Metadata', (), {
            'report_date': report_date,
            'filing_date': filing_date,
            'form_type': form_type
        })())
        
        if mdna_content:
            # 生成文件名
            filename = f"{ticker}_{report_date.replace('-', '_')}_mdna.md"
            filepath = os.path.join(output_dir, filename)
            
            # 保存到文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(mdna_content)
            
            print(f"  ✅ MD&A已保存到: {filename}")
            logger.info(f"成功处理文件 {report_date}: {filename}")
            return True
        else:
            print(f"  ❌ 未能提取到MD&A内容")
            logger.warning(f"未能提取到MD&A内容: {report_date}")
            return False
            
    except Exception as e:
        print(f"  ❌ 处理 {report_date} 的文件时出错: {str(e)}")
        logger.error(f"处理文件 {report_date} 时出错: {str(e)}")
        return False

def main():
    """
    主函数：修复有问题的JPM季报文件
    """
    print("开始修复JPM季报中有问题的文件...")
    print("=" * 80)
    
    # 从filing_urls.txt中获取JPM的财报信息
    urls_file = "filing_urls.txt"
    if not os.path.exists(urls_file):
        print(f"❌ 找不到文件: {urls_file}")
        return
    
    # 读取filing_urls.txt文件
    jpm_urls = []
    with open(urls_file, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
        
        current_ticker = None
        for i, line in enumerate(lines):
            if line.startswith('公司: '):
                current_ticker = line.split(': ')[1].strip()
            elif line.startswith('10-Q - ') and current_ticker == 'JPM':
                # 提取日期
                date_part = line.split('10-Q - ')[1].strip()
                report_date = date_part
                
                # 查找对应的URL（下一行）
                if i + 1 < len(lines) and lines[i + 1].startswith('网址: '):
                    url = lines[i + 1].split('网址: ')[1].strip()
                    
                    # 只处理需要修复的特定日期
                    if any(target_date in report_date for target_date in ['2020-09-30', '2021-03-31', '2021-06-30', '2021-09-30', '2025-03-31', '2025-06-30']):
                        jpm_urls.append({
                            'ticker': 'JPM',
                            'form_type': '10-Q',
                            'report_date': report_date,
                            'filing_date': report_date,
                            'url': url
                        })
                        print(f"找到需要修复的JPM季报: {report_date} -> {url}")
    
    print(f"找到 {len(jpm_urls)} 个需要修复的JPM季报文件")
    
    if not jpm_urls:
        print("❌ 没有找到需要修复的JPM季报文件")
        return
    
    # 处理每个文件
    success_count = 0
    for url_info in jpm_urls:
        success = process_jpm_quarterly_filing(
            url_info['ticker'],
            url_info['form_type'],
            url_info['report_date'],
            url_info['filing_date'],
            url_info['url']
        )
        if success:
            success_count += 1
    
    print(f"\n✅ 修复完成！")
    print(f"成功修复: {success_count}/{len(jpm_urls)} 个文件")
    logger.info(f"修复完成: {success_count}/{len(jpm_urls)} 个文件")

if __name__ == "__main__":
    main()
