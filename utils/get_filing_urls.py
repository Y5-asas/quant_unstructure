from sec_downloader import Downloader
from sec_downloader.types import RequestedFilings
import os
from datetime import datetime

# ==================== 1. 配置 ====================
# 您的下载器信息
dl = Downloader("HKU", "u303637086@connect.hku.hk")

# 需要获取财报网址的公司列表
TARGET_TICKERS = ["CVX", "IBM", "JPM", "MSFT", "INTC", "MMM"]

# 输出文件
output_file = "filing_urls.txt"

# ==================== 2. 获取财报网址函数 ====================
def get_filing_urls(ticker: str, form_type: str, limit: int):
    """
    获取指定公司、指定类型、指定数量的财报网址
    """
    print(f"正在获取 {ticker} 的 {form_type} 文件网址...")
    
    try:
        # 获取元数据
        metadatas = dl.get_filing_metadatas(
            RequestedFilings(ticker_or_cik=ticker, form_type=form_type, limit=limit)
        )
        
        print(f"  找到 {len(metadatas)} 份 {form_type} 文件")
        
        urls = []
        for i, metadata in enumerate(metadatas, start=1):
            url_info = {
                'ticker': ticker,
                'form_type': form_type,
                'report_date': metadata.report_date,
                'filing_date': metadata.filing_date,
                'url': metadata.primary_doc_url,
                'index': i
            }
            urls.append(url_info)
            print(f"    [{i:2d}] {metadata.report_date} -> {metadata.primary_doc_url}")
        
        return urls
        
    except Exception as e:
        print(f"  ❌ 获取 {ticker} 的 {form_type} 元数据时出错: {str(e)}")
        return []

# ==================== 3. 保存到文件 ====================
def save_urls_to_file(all_urls):
    """
    将所有财报网址保存到txt文件
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 100 + "\n")
        f.write("CVX, IBM, JPM, MSFT 公司财报网址列表\n")
        f.write("=" * 100 + "\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"总计: {len(all_urls)} 个文件\n\n")
        
        # 按公司分组
        current_ticker = None
        for url_info in all_urls:
            if url_info['ticker'] != current_ticker:
                current_ticker = url_info['ticker']
                f.write(f"\n{'='*80}\n")
                f.write(f"公司: {current_ticker}\n")
                f.write(f"{'='*80}\n\n")
            
            f.write(f"{url_info['form_type']} - {url_info['report_date']}\n")
            f.write(f"网址: {url_info['url']}\n")
            f.write(f"文件日期: {url_info['filing_date']}\n")
            f.write("-" * 80 + "\n\n")
        
        # 添加统计信息
        f.write("\n" + "=" * 100 + "\n")
        f.write("统计信息\n")
        f.write("=" * 100 + "\n")
        
        for ticker in TARGET_TICKERS:
            ticker_urls = [u for u in all_urls if u['ticker'] == ticker]
            q10_count = len([u for u in ticker_urls if u['form_type'] == '10-Q'])
            k10_count = len([u for u in ticker_urls if u['form_type'] == '10-K'])
            f.write(f"{ticker}: 10-Q: {q10_count}份, 10-K: {k10_count}份\n")
        
        f.write(f"\n总计: {len(all_urls)} 个文件\n")
        f.write(f"10-Q: {len([u for u in all_urls if u['form_type'] == '10-Q'])} 份\n")
        f.write(f"10-K: {len([u for u in all_urls if u['form_type'] == '10-K'])} 份\n")

# ==================== 4. 主执行函数 ====================
def main():
    print("开始获取CVX, IBM, JPM, MSFT公司的财报网址...")
    print("=" * 80)
    
    all_urls = []
    
    for ticker in TARGET_TICKERS:
        print(f"\n处理公司: {ticker}")
        print("-" * 40)
        
        # 获取10-Q季报 (15份)
        print(f"获取10-Q季报 (目标: 15份)...")
        q10_urls = get_filing_urls(ticker, "10-Q", limit=15)
        all_urls.extend(q10_urls)
        
        # 获取10-K年报 (3份)
        print(f"获取10-K年报 (目标: 3份)...")
        k10_urls = get_filing_urls(ticker, "10-K", limit=3)
        all_urls.extend(k10_urls)
        
        print(f"{ticker} 完成: 10-Q: {len(q10_urls)}份, 10-K: {len(k10_urls)}份")
    
    # 保存到文件
    print(f"\n正在保存网址到文件: {output_file}")
    save_urls_to_file(all_urls)
    
    print(f"\n✅ 完成！")
    print(f"所有财报网址已保存到: {output_file}")
    print(f"总计获取: {len(all_urls)} 个文件")
    
    # 显示统计信息
    print(f"\n统计信息:")
    for ticker in TARGET_TICKERS:
        ticker_urls = [u for u in all_urls if u['ticker'] == ticker]
        q10_count = len([u for u in ticker_urls if u['form_type'] == '10-Q'])
        k10_count = len([u for u in ticker_urls if u['form_type'] == '10-K'])
        print(f"  {ticker}: 10-Q: {q10_count}份, 10-K: {k10_count}份")

if __name__ == "__main__":
    main()
