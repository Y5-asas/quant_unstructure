#!/usr/bin/env python3
"""
专门处理JPM财报MD&A结构的脚本
JPM的MD&A结构不同于其他公司：
- 不是以"Item 2."开头的独立章节
- 而是在"INTRODUCTION"部分下直接包含"Management's discussion and analysis"内容
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
logger = logging.getLogger("JPM_MDNA_Processor")
logger.setLevel(logging.INFO)

# 创建文件处理器
log_filename = "jpm_mdna_processor.log"
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
base_output_dir = "dogs_of_30_mdna/JPM"
os.makedirs(base_output_dir, exist_ok=True)
print(f"JPM输出目录已创建: {base_output_dir}")

# ==================== 2. 命名函数 ====================
def generate_jpm_filename(metadata, suffix: str = "mdna") -> str:
    """
    为JPM财报生成标准化文件名
    """
    report_date = datetime.strptime(metadata.report_date, "%Y-%m-%d")
    year = report_date.year
    
    # 格式化 report_date 为 YYYYMMDD
    report_date_str = report_date.strftime("%Y%m%d")
    
    # 判断报告类型
    if metadata.form_type == "10-K":
        period = "Annual"
    elif metadata.form_type == "10-Q":
        month = report_date.month
        if month in [1, 2, 3]:
            period = "Q1"
        elif month in [4, 5, 6]:
            period = "Q2"
        elif month in [7, 8, 9]:
            period = "Q3"
        elif month in [10, 11, 12]:
            period = "Q4"
        else:
            period = "Unknown"
    else:
        period = "Other"
    
    # 生成最终文件名
    filename = f"JPM_{year}_{period}_{report_date_str}_{suffix}.md"
    return filename

# ==================== 3. JPM特定的MD&A提取逻辑 ====================
def extract_jpm_mdna(elements: List, metadata) -> str:
    """
    专门针对JPM财报结构的MD&A提取逻辑
    """
    print(f"    正在使用JPM特定的MD&A提取逻辑...")
    
    # 构建文档树
    tree_parts = sp.TreeBuilder().build(elements)
    
    # 查找包含MD&A内容的章节
    mdna_content = []
    
    # 策略1: 查找"INTRODUCTION"章节
    introduction_section = None
    for part in tree_parts:
        for section in part.children:
            if isinstance(section.semantic_element, sp.TitleElement):
                title_text = section.semantic_element.text.lower()
                if "introduction" in title_text:
                    introduction_section = section
                    print(f"      找到INTRODUCTION章节: {section.semantic_element.text}")
                    break
        if introduction_section:
            break
    
    if introduction_section:
        # 从INTRODUCTION章节开始提取内容
        print(f"      从INTRODUCTION章节提取MD&A内容...")
        
        # 获取所有后代元素
        descendants = introduction_section.get_descendants()
        
        # 查找MD&A相关的标题和内容
        mdna_sections = []
        current_section = None
        
        for element in descendants:
            if isinstance(element.semantic_element, sp.TitleElement):
                title_text = element.semantic_element.text.lower()
                
                # 检查是否是MD&A相关章节
                if any(keyword in title_text for keyword in [
                    "management", "discussion", "analysis", "financial", "operations",
                    "consolidated", "business", "segment", "risk", "capital"
                ]):
                    current_section = element
                    mdna_sections.append(element)
                    print(f"        找到MD&A相关章节: {element.semantic_element.text}")
                    
            elif isinstance(element.semantic_element, sp.TextElement) and current_section:
                # 添加文本内容
                mdna_content.append(element.semantic_element.text)
    
    # 策略2: 如果没找到INTRODUCTION，搜索所有包含MD&A关键词的章节
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
    
    if not mdna_content:
        print(f"      ❌ 无法提取到任何MD&A内容")
        return None
    
    # 构建Markdown内容
    markdown = f"# JPMorgan Chase & Co. - {metadata.form_type} for {metadata.report_date}\n\n"
    markdown += "## Management's Discussion and Analysis\n\n"
    markdown += "**注意**: 此文件使用JPM特定的MD&A提取逻辑，因为JPM的财报结构与标准格式不同。\n\n"
    
    # 添加提取的内容
    for content in mdna_content:
        markdown += f"{content}\n\n"
    
    return markdown

# ==================== 4. 主处理函数 ====================
def download_and_save_jpm_mdna(ticker: str, form_type: str, limit: int):
    """
    下载JPM财报并提取MD&A保存为Markdown
    """
    print(f"\n--- 开始处理 {ticker} 的 {form_type} 文件 ---")
    
    try:
        # 获取元数据
        metadatas = dl.get_filing_metadatas(
            RequestedFilings(ticker_or_cik=ticker, form_type=form_type, limit=limit)
        )
        print(f"  找到 {len(metadatas)} 份 {form_type} 文件。")
        
        for i, metadata in enumerate(metadatas, start=1):
            try:
                print(f"    [{i}/{len(metadatas)}] 正在处理 {metadata.report_date} ({metadata.form_type})...")
                
                # 下载HTML
                html = dl.download_filing(url=metadata.primary_doc_url).decode('utf-8', errors='ignore')
                
                # 解析HTML
                elements: List = sp.Edgar10QParser().parse(html)
                
                # 使用JPM特定的MD&A提取逻辑
                markdown = extract_jpm_mdna(elements, metadata)
                
                if not markdown:
                    print(f"      ❌ 无法提取MD&A内容，跳过此文件")
                    continue
                
                # 生成文件名
                filename = generate_jpm_filename(metadata, suffix="mdna")
                file_path = os.path.join(base_output_dir, filename)
                
                # 检查文件是否已存在
                if os.path.exists(file_path):
                    print(f"      ⏭️  文件已存在，跳过: {filename}")
                    continue
                
                # 保存文件
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(markdown)
                
                print(f"      ✅ MD&A 已保存至: {file_path}")
                
            except Exception as e:
                print(f"      ❌ 处理 {metadata.report_date} 的文件时出错: {str(e)}")
                logger.error(f"处理文件 {metadata.report_date} 时出错: {str(e)}")
                continue
                
    except Exception as e:
        print(f"  ❌ 获取 {ticker} 的 {form_type} 元数据时出错: {str(e)}")
        logger.error(f"获取元数据时出错: {str(e)}")

# ==================== 5. 执行下载 ====================
if __name__ == "__main__":
    print("开始处理JPM财报MD&A...")
    print("=" * 80)
    print("注意: JPM使用特殊的MD&A结构，不是标准的'Item 2.'格式")
    print("=" * 80)
    
    # 下载JPM的财报
    ticker = "JPM"
    
    # 下载10-Q季报 (15份)
    print(f"\n获取JPM的10-Q季报...")
    download_and_save_jpm_mdna(ticker, "10-Q", limit=15)
    
    # 下载10-K年报 (3份)
    print(f"\n获取JPM的10-K年报...")
    download_and_save_jpm_mdna(ticker, "10-K", limit=3)
    
    print("\n\n✅ JPM财报MD&A处理完成！")
    print(f"所有文件已保存在: {base_output_dir}")
    print("文件结构示例:")
    print("  dogs_of_30_mdna/JPM/")
    print("  ├── JPM_2025_Q2_20250630_mdna.md")
    print("  ├── JPM_2025_Q1_20250331_mdna.md")
    print("  └── ...")
