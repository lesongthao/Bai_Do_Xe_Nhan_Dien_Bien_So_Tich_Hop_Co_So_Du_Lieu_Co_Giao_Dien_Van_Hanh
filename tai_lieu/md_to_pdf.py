"""
Script chuyển Markdown → PDF cho báo cáo đồ án
Hỗ trợ: bảng, heading, bold/italic, code blocks, danh sách
"""
import sys
import os
import markdown
from xhtml2pdf import pisa

def md_to_pdf(md_path, pdf_path):
    """Đọc file .md, chuyển sang HTML, rồi xuất PDF"""
    
    # Đọc file markdown
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Loại bỏ Mermaid code blocks (xhtml2pdf không render được)
    import re
    md_content = re.sub(r'```mermaid\n.*?```', 
                        '<p><em>[Sơ đồ Mermaid - xem file .md gốc]</em></p>', 
                        md_content, flags=re.DOTALL)
    
    # Loại bỏ carousel blocks  
    md_content = re.sub(r'````carousel\n.*?````',
                        '<p><em>[Carousel - xem file .md gốc]</em></p>',
                        md_content, flags=re.DOTALL)
    
    # Loại bỏ GitHub alerts syntax
    md_content = re.sub(r'> \[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\n', '', md_content)
    
    # Sửa đường dẫn ảnh: bỏ dấu / ở đầu (vd: /C:/... -> C:/...)
    md_content = re.sub(r'\(/([A-Za-z]:)', r'(\1', md_content)
    
    # Chuyển markdown → HTML
    html_body = markdown.markdown(
        md_content,
        extensions=['tables', 'fenced_code', 'nl2br', 'sane_lists']
    )
    
    # Template HTML với CSS đẹp
    html_full = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@page {{
    size: A4;
    margin: 2cm 2.5cm;
}}
body {{
    font-family: "Times New Roman", serif;
    font-size: 13pt;
    line-height: 1.6;
    color: #222;
}}
h1 {{
    font-size: 20pt;
    text-align: center;
    color: #1a237e;
    border-bottom: 2px solid #1a237e;
    padding-bottom: 8px;
    margin-top: 20px;
}}
h2 {{
    font-size: 16pt;
    color: #283593;
    border-bottom: 1px solid #ccc;
    padding-bottom: 4px;
    margin-top: 18px;
}}
h3 {{
    font-size: 14pt;
    color: #3949ab;
    margin-top: 14px;
}}
table {{
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0;
    font-size: 11pt;
}}
th {{
    background-color: #1a237e;
    color: white;
    padding: 6px 8px;
    text-align: left;
    border: 1px solid #333;
}}
td {{
    padding: 5px 8px;
    border: 1px solid #ccc;
}}
tr:nth-child(even) {{
    background-color: #f5f5f5;
}}
code {{
    background-color: #f0f0f0;
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 11pt;
    font-family: "Courier New", monospace;
}}
pre {{
    background-color: #f5f5f5;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 10pt;
    overflow-x: auto;
}}
blockquote {{
    border-left: 4px solid #1a237e;
    padding: 8px 12px;
    margin: 10px 0;
    background-color: #e8eaf6;
    font-style: italic;
}}
ul, ol {{
    margin: 8px 0;
    padding-left: 24px;
}}
li {{
    margin-bottom: 4px;
}}
strong {{
    color: #1a237e;
}}
hr {{
    border: none;
    border-top: 2px solid #1a237e;
    margin: 20px 0;
}}
img {{
    max-width: 100%;
    display: block;
    margin: 10px auto;
}}
</style>
</head>
<body>
{html_body}
</body>
</html>"""
    
    # Xuất PDF
    with open(pdf_path, 'wb') as pdf_file:
        status = pisa.CreatePDF(html_full, dest=pdf_file, encoding='utf-8')
    
    if status.err:
        print(f"Loi khi tao PDF: {status.err}")
        return False
    else:
        size_mb = os.path.getsize(pdf_path) / (1024*1024)
        print(f"Da tao PDF: {pdf_path}")
        print(f"Kich thuoc: {size_mb:.1f} MB")
        return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Cách dùng: python md_to_pdf.py <file.md> [output.pdf]")
        sys.exit(1)
    
    md_file = sys.argv[1]
    if len(sys.argv) >= 3:
        pdf_file = sys.argv[2]
    else:
        pdf_file = md_file.rsplit('.', 1)[0] + '.pdf'
    
    md_to_pdf(md_file, pdf_file)
