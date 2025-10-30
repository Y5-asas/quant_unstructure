from sec_downloader import Downloader
import sec_parser as sp
from sec_downloader.types import RequestedFilings
from typing import List

# ==================== 1. 配置 ====================
dl = Downloader("HKU", "u303637086@connect.hku.hk")

# ==================== 2. 测试改进后的MD&A识别逻辑 ====================
def test_improved_mdna_detection():
    """
    测试改进后的MD&A识别逻辑
    """
    print("测试改进后的MD&A识别逻辑...")
    print("=" * 60)
    
    try:
        # 获取CVX的最新10-Q
        metadatas = dl.get_filing_metadatas(
            RequestedFilings(ticker_or_cik="CVX", form_type="10-Q", limit=1)
        )
        
        if not metadatas:
            print("未找到CVX的10-Q文件")
            return
        
        metadata = metadatas[0]
        print(f"测试文件: {metadata.report_date} ({metadata.form_type})")
        
        # 下载HTML
        html = dl.download_filing(url=metadata.primary_doc_url).decode('utf-8', errors='ignore')
        
        # 解析HTML
        elements: List = sp.Edgar10QParser().parse(html)
        top_level_sections = [
            item for part in sp.TreeBuilder().build(elements) for item in part.children
        ]
        
        print(f"找到 {len(top_level_sections)} 个顶级章节")
        
        # 使用改进后的识别逻辑
        mdna_sections = []
        
        # 策略1: 直接模式匹配
        mdna_patterns = [
            "management's discussion and analysis",
            "management discussion and analysis", 
            "md&a",
            "management discussion",
            "financial condition and results of operations",
            "management's discussion",
            "discussion and analysis",
            "management's discussion and analysis of financial condition and results of operations",
            "management discussion and analysis of financial condition and results of operations",
            "item 2. management's discussion and analysis of financial condition and results of operations",
            "item 2. management discussion and analysis of financial condition and results of operations",
            "management's discussion and analysis of",
            "management discussion and analysis of",
            "discussion and analysis of financial condition",
            "discussion and analysis of results of operations"
        ]
        
        print(f"\n--- 策略1: 直接模式匹配 ---")
        direct_matches = [
            k for k in top_level_sections 
            if any(pattern in k.semantic_element.text.lower() for pattern in mdna_patterns)
        ]
        mdna_sections.extend(direct_matches)
        
        if direct_matches:
            print(f"✅ 策略1成功: 找到 {len(direct_matches)} 个MD&A部分")
            for section in direct_matches:
                print(f"  - {section.semantic_element.text}")
        else:
            print(f"❌ 策略1失败: 直接模式匹配未找到结果")
        
        # 策略2: 基于Item编号和子章节内容的智能匹配
        if not mdna_sections:
            print(f"\n--- 策略2: 基于Item编号的智能匹配 ---")
            
            for section in top_level_sections:
                section_title = section.semantic_element.text.strip()
                
                # 检查是否是Item 2（10-Q中通常是MD&A）
                if "Item 2" in section_title:
                    print(f"  找到Item 2，检查子章节内容...")
                    
                    # 检查子章节是否包含MD&A关键词
                    children = section.get_descendants()
                    title_children = [c for c in children if isinstance(c.semantic_element, sp.TitleElement)]
                    
                    has_mdna_content = False
                    for child in title_children:
                        child_title = child.semantic_element.text.lower()
                        if any(keyword in child_title for keyword in ["management", "discussion", "analysis"]):
                            print(f"    子章节包含MD&A关键词: {child.semantic_element.text}")
                            has_mdna_content = True
                            break
                    
                    if has_mdna_content:
                        print(f"  ✅ Item 2 被识别为MD&A部分")
                        mdna_sections.append(section)
                        break
        else:
            print(f"\n--- 策略2: 跳过（策略1已成功） ---")
        
        # 策略3: 搜索所有包含MD&A关键词的子章节
        if not mdna_sections:
            print(f"\n--- 策略3: 搜索所有子章节 ---")
            
            for section in top_level_sections:
                children = section.get_descendants()
                for child in children:
                    if isinstance(child.semantic_element, sp.TitleElement):
                        child_title = child.semantic_element.text.lower()
                        if any(keyword in child_title for keyword in ["management", "discussion", "analysis"]):
                            print(f"  找到包含MD&A关键词的子章节: {child.semantic_element.text}")
                            print(f"  位于章节: {section.semantic_element.text}")
                            mdna_sections.append(section)
                            break
                if mdna_sections:
                    break
        else:
            print(f"\n--- 策略3: 跳过（前面策略已成功） ---")
        
        # 最终结果
        print(f"\n{'='*60}")
        print("最终结果")
        print("="*60)
        
        if mdna_sections:
            print(f"✅ 成功找到 {len(mdna_sections)} 个MD&A部分:")
            for i, section in enumerate(mdna_sections):
                print(f"  {i+1}. 主章节: {section.semantic_element.text}")
                
                # 显示子章节信息
                children = section.get_descendants()
                title_children = [c for c in children if isinstance(c.semantic_element, sp.TitleElement)]
                if title_children:
                    print(f"     子章节数量: {len(title_children)}")
                    print(f"     前3个子章节:")
                    for j, child in enumerate(title_children[:3]):
                        print(f"       {j+1}. {child.semantic_element.text}")
        else:
            print(f"❌ 所有策略都失败了，未找到任何MD&A部分")
            
    except Exception as e:
        print(f"测试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_improved_mdna_detection()
