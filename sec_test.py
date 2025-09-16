from sec_downloader import Downloader
import sec_parser as sp
from sec_downloader.types import RequestedFilings
import os

output_dir = "mdna_markdowns"
os.makedirs(output_dir, exist_ok=True)

# Initialize the downloader with your company name and email
dl = Downloader("HKU", "u303637086@connect.hku.hk")

# Download the latest 10-Q filing for Apple
#html = dl.get_filing_html(ticker="AAPL", form="10-Q")
#print(html)

# Download the latest 2 10-Q filing for Microsoft
metadatas = dl.get_filing_metadatas(
    RequestedFilings(ticker_or_cik="AAPL", form_type="10-Q", limit=3)
)
print(len(metadatas))

all_html = []
# return 2, represent the latest 2 10-Q filing for Microsoft
for metadata in metadatas:
    # print(metadata)
    html = dl.download_filing(url=metadata.primary_doc_url).decode()
    all_html.append(html)
    #print(html[:50])

num = len(all_html)

for idx, html in enumerate(all_html, start=1):
    print("=" * 80)
    print(f"[{idx}/{num}] Parsing 10-Q...")

    elements: list = sp.Edgar10QParser().parse(html)
    top_level_sections = [
        item for part in sp.TreeBuilder().build(elements) for item in part.children
    ]
    # demo_output: str = sp.render(elements)
    # print(demo_output)

    # Filter MD&A section
    mdna_top_level_sections = [
        k for k in top_level_sections if "management" in k.semantic_element.text.lower()
    ]
    assert len(mdna_top_level_sections) == 1
    mdna_top_level_section = mdna_top_level_sections[0]

    # Convert to markdown (Step 1: Get levels)
    levels = sorted(
        {
            k.semantic_element.level
            for k in mdna_top_level_section.get_descendants()
            if isinstance(k.semantic_element, sp.TitleElement)
        }
    )
    level_to_markdown = {level: "#" * (i + 2) for i, level in enumerate(levels)}
    level_to_markdown



    # Convert to markdown (Step 2: Extract text)
    markdown = ""
    markdown += f"# {mdna_top_level_section.semantic_element.text}\n"
    for node in mdna_top_level_section.get_descendants():
        element = node.semantic_element
        if isinstance(element, sp.TextElement):
            markdown += f"{element.text}\n"
        elif isinstance(element, sp.TitleElement):
            markdown += f"{level_to_markdown[element.level]} {element.text}\n"
        elif isinstance(element, sp.TableElement):
            markdown += f"[{element.get_summary()}]\n"



    def get_lines(text, start=None, end=None, max_line_length=80):
        lines = text.split("\n")[start:end]
        return "\n".join(
            line if len(line) <= max_line_length else line[:max_line_length] + "..."
            for line in lines
        )


    print(get_lines(markdown, end=13))
    print("...")
    print(get_lines(markdown, start=-13))

    filename = os.path.join(output_dir, f"mdna_{idx}.md")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"MD&A markdown saved to: {filename}")
