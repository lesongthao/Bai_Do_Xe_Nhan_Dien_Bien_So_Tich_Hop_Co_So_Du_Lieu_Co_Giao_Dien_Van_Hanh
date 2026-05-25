"""
Render cac so do Mermaid thanh file PNG dep bang mermaid.ink API.
"""
import base64, os, re, urllib.request, zlib, sys

MD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'so_do_khoi_he_thong.md')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'so_do')
os.makedirs(OUT, exist_ok=True)

def read_mermaid_blocks(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Tim tat ca heading + mermaid block
    pattern = r'## (\d+)\.\s+(.+?)\n.*?```mermaid\n(.*?)```'
    blocks = re.findall(pattern, content, re.DOTALL)
    return [(num, title.strip(), code.strip()) for num, title, code in blocks]

def mermaid_to_png(code, output_path, title=""):
    """Dung mermaid.ink API de render thanh PNG."""
    # Encode mermaid code thanh base64 (cho URL)
    encoded = base64.urlsafe_b64encode(code.encode('utf-8')).decode('ascii')
    # URL API - dung SVG de chat luong cao hon
    url = f"https://mermaid.ink/img/{encoded}?type=png&bgColor=!white&theme=default&width=1920&height=1080"

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        with open(output_path, 'wb') as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"  [LOI] {e}")
        return False

if __name__ == '__main__':
    print(f"Doc file: {MD_FILE}")
    blocks = read_mermaid_blocks(MD_FILE)
    print(f"Tim thay {len(blocks)} so do Mermaid\n")

    ok = 0
    for num, title, code in blocks:
        fname = f"{num.zfill(2)}_{re.sub(r'[^a-zA-Z0-9]', '_', title.lower()).strip('_')[:50]}.png"
        out_path = os.path.join(OUT, fname)
        print(f"[{num}/{len(blocks)}] {title}")
        print(f"  -> {fname}")
        if mermaid_to_png(code, out_path, title):
            size_kb = os.path.getsize(out_path) / 1024
            print(f"  OK ({size_kb:.0f} KB)")
            ok += 1
        print()

    print(f"\nHoan tat: {ok}/{len(blocks)} so do da xuat vao {OUT}")
