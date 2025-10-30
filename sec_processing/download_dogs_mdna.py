from sec_downloader import Downloader
import sec_parser as sp
from sec_downloader.types import RequestedFilings
import os
from datetime import datetime
from typing import List
import logging

# ==================== 1. 配置 ====================
# --- 日志配置 ---
# 创建一个日志器
logger = logging.getLogger("SEC_Downloader")
logger.setLevel(logging.INFO)

# 创建一个文件处理器，将日志写入文件
log_filename = "sec_downloader.log"
file_handler = logging.FileHandler(log_filename, mode='a', encoding='utf-8')
file_handler.setLevel(logging.INFO)

# 设置日志格式
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# 将处理器添加到日志器
logger.addHandler(file_handler)

# 同时也可以输出到控制台（可选）
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# ==================== 1. 配置 ====================
# 您的下载器信息
dl = Downloader("HKU", "u303637086@connect.hku.hk")

# 定义新的Dow Jones 30成分股列表
# 移除：WBA (Walgreens), XOM (Exxon Mobil)
# 添加：AMZN (Amazon), CRM (Salesforce)
DOGS_OF_30 = [
    "MMM",  # 3M Company
    "AXP",  # American Express Company
    "AMGN", # Amgen Inc.
    "AAPL", # Apple Inc.
    "AMZN", # Amazon.com Inc. (新增)
    "BA",   # Boeing Co
    "CAT",  # Caterpillar Inc.
    "CVX",  # Chevron Corporation
    "CSCO", # Cisco Systems, Inc.
    "KO",   # The Coca-Cola Company
    "CRM",  # Salesforce Inc. (新增)
    "DOW",  # Dow Inc.
    "GS",   # Goldman Sachs Group Inc
    "LTX",  # Linde plc (原Praxair)
    "HD",   # The Home Depot, Inc.
    "HON",  # Honeywell International Inc.
    "INTC", # Intel Corporation
    "IBM",  # International Business Machines Corporation
    "JNJ",  # Johnson & Johnson
    "JPM",  # JP Morgan Chase & Co
    "MCD",  # McDonald's Corporation
    "MRK",  # Merck & Co., Inc.
    "MSFT", # Microsoft Corporation
    "NKE",  # Nike, Inc.
    "PG",   # Procter & Gamble Company
    "TRV",  # Travelers Companies Inc
    "UNH",  # UnitedHealth Group Incorporated
    "VZ",   # Verizon Communications Inc.
    "V",    # Visa Inc.
    "WMT",  # Walmart Inc.
    "DIS"   # The Walt Disney Company
]

# 输出目录
base_output_dir = "../data/dogs_of_30_mdna"
os.makedirs(base_output_dir, exist_ok=True)
print(f"主输出目录已创建: {base_output_dir}")

# ==================== 2. 命名函数 (核心) ====================
def generate_filename(metadata, company_ticker: str, suffix: str = "mdna") -> str:
    """
    根据 FilingMetadata 生成标准化文件名。
    格式: {TICKER}_{YEAR}_{PERIOD}_{REPORT_DATE}_{SUFFIX}.md
    例如: MSFT_2024_Annual_20240630_mdna.md 或 AAPL_2024_Q1_20240331_mdna.md
    """
    report_date = datetime.strptime(metadata.report_date, "%Y-%m-%d")
    year = report_date.year
    
    # 格式化 report_date 为 YYYYMMDD
    report_date_str = report_date.strftime("%Y%m%d")
    
    # 判断报告类型 (年报 or 季报)
    if metadata.form_type == "10-K":
        period = "Annual"
    elif metadata.form_type == "10-Q":
        month = report_date.month
        if month == 3 or month == 1 or month == 2:
            period = "Q1"
        elif month == 6 or month == 4 or month == 5:
            period = "Q2"
        elif month == 9 or month == 7 or month == 8:
            period = "Q3"
        elif month == 12 or month == 10 or month == 11:
            period = "Q4"
        else:
            period = "Unknown"
    else:
        period = "Other"
    
    # 生成最终文件名
    filename = f"{company_ticker}_{year}_{period}_{report_date_str}_{suffix}.md"
    return filename

# ==================== 3. 主处理函数 ====================
def download_and_save_mdna(ticker: str, form_type: str, limit: int):
    """
    下载指定公司、指定类型、指定数量的财报，并提取MD&A保存为Markdown。
    """
    print(f"\n--- 开始处理 {ticker} 的 {form_type} 文件 ---")
    
    try:
        # 获取元数据
        metadatas = dl.get_filing_metadatas(
            RequestedFilings(ticker_or_cik=ticker, form_type=form_type, limit=limit)
        )
        print(f"  找到 {len(metadatas)} 份 {form_type} 文件。")
        
        # 为每家公司创建子目录
        ticker_dir = os.path.join(base_output_dir, ticker)
        os.makedirs(ticker_dir, exist_ok=True)
        
        for i, metadata in enumerate(metadatas, start=1):
            try:
                print(f"    [{i}/{len(metadatas)}] 正在处理 {metadata.report_date} ({metadata.form_type})...")
                
                # 下载HTML
                html = dl.download_filing(url=metadata.primary_doc_url).decode('utf-8', errors='ignore')
                
                # 解析HTML并提取MD&A
                elements: List = sp.Edgar10QParser().parse(html)
                top_level_sections = [
                    item for part in sp.TreeBuilder().build(elements) for item in part.children
                ]
                
                # 筛选MD&A部分 - 使用基于章节标题模式的判定
                mdna_patterns = [
                    "management's discussion and analysis",
                    "management discussion and analysis", 
                    "md&a",
                    "management discussion",
                    "financial condition and results of operations",
                    "management's discussion",
                    "discussion and analysis"
                ]
                
                mdna_sections = [
                    k for k in top_level_sections 
                    if any(pattern in k.semantic_element.text.lower() for pattern in mdna_patterns)
                ]
                
                if not mdna_sections:
                    print(f"      警告: 未在 {metadata.report_date} 的文件中找到MD&A部分。")
                    continue
                    
                assert len(mdna_sections) == 1, f"找到多个MD&A部分: {len(mdna_sections)}"
                mdna_section = mdna_sections[0]
                
                # 转换为Markdown
                levels = sorted({
                    k.semantic_element.level 
                    for k in mdna_section.get_descendants() 
                    if isinstance(k.semantic_element, sp.TitleElement)
                })
                level_to_markdown = {level: "#" * (i + 2) for i, level in enumerate(levels)}
                
                markdown = f"# {mdna_section.semantic_element.text}\n\n"
                for node in mdna_section.get_descendants():
                    element = node.semantic_element
                    if isinstance(element, sp.TextElement):
                        markdown += f"{element.text}\n\n"
                    elif isinstance(element, sp.TitleElement):
                        markdown += f"{level_to_markdown[element.level]} {element.text}\n\n"
                    elif isinstance(element, sp.TableElement):
                        markdown += f"[表格: {element.get_summary()}]\n\n"
                
                # 生成文件名
                filename = generate_filename(metadata, ticker, suffix="mdna")
                file_path = os.path.join(ticker_dir, filename)
                
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
                continue
                
    except Exception as e:
        print(f"  ❌ 获取 {ticker} 的 {form_type} 元数据时出错: {str(e)}")

# ==================== 4. 执行下载 ====================
if __name__ == "__main__":
    # 只下载新增的股票：AMZN和CRM
    new_stocks = ["AMZN", "CRM"]
    
    for ticker in new_stocks:
        print(f"\n🚀 开始下载 {ticker} 的MD&A数据...")
        
        # 下载10-Q季报
        download_and_save_mdna(ticker, "10-Q", limit=15)
        
        # 下载10-K年报
        download_and_save_mdna(ticker, "10-K", limit=3)
    
    print("\n\n✅ 新股票下载任务已完成！")
    print(f"AMZN和CRM的MD&A数据已保存在: {base_output_dir}")
    print("文件结构示例:")
    print("  dogs_of_30_mdna/")
    print("  ├── AMZN/")
    print("  │   ├── AMZN_2024_Annual_20240630_mdna.md")
    print("  │   ├── AMZN_2024_Q3_20240930_mdna.md")
    print("  │   └── ...")
    print("  └── CRM/")
    print("      ├── CRM_2024_Annual_20240630_mdna.md")
    print("      ├── CRM_2024_Q3_20240930_mdna.md")
    print("      └── ...")