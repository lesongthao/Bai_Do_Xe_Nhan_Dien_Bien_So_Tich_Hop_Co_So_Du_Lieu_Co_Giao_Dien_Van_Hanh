import os
import re
import subprocess
import fitz  # pymupdf

def main():
    tex_file = "bao_cao_do_an.tex"
    with open(tex_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Preambles for standalone tikz
    preamble = r"""\documentclass[tikz, border=2mm]{standalone}
\usepackage{fontspec}
\usepackage[vietnamese]{babel}
\setmainfont{Times New Roman}
\usepackage[dvipsnames,svgnames,x11names]{xcolor}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning, fit, backgrounds, calc}

\tikzstyle{block} = [rectangle, rounded corners, minimum width=2.5cm, minimum height=1cm, align=center, inner sep=2mm, draw=black, fill=blue!8, font=\small]
\tikzstyle{decision} = [diamond, aspect=2.5, minimum width=2cm, align=center, inner sep=1mm, draw=black, fill=yellow!15, font=\small]
\tikzstyle{arrow} = [thick, ->, >=Stealth]
\tikzstyle{darrow} = [thick, <->, >=Stealth]
\tikzstyle{process} = [rectangle, minimum width=2cm, minimum height=0.8cm, align=center, inner sep=2mm, draw=black, fill=green!8, font=\small]
\tikzstyle{reject} = [rectangle, rounded corners, minimum width=2cm, minimum height=0.8cm, align=center, inner sep=2mm, draw=red!70, fill=red!8, font=\small]
\tikzstyle{accept} = [rectangle, rounded corners, minimum width=2cm, minimum height=0.8cm, align=center, inner sep=2mm, draw=green!70!black, fill=green!12, font=\small]

\begin{document}
"""
    postamble = r"\end{document}"
    
    # Find all tikzpictures
    pattern = r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}"
    matches = list(re.finditer(pattern, content, re.DOTALL))
    
    if not os.path.exists("svg_exports"):
        os.makedirs("svg_exports")
        
    for i, match in enumerate(matches):
        tikz_code = match.group(0)
        
        # Try to find the caption for naming
        # Look ahead up to 200 chars for \caption{...}
        lookahead = content[match.end():match.end()+200]
        caption_match = re.search(r"\\caption\{([^}]+)\}", lookahead)
        
        if caption_match:
            # Clean up filename
            name = caption_match.group(1).replace(" ", "_").replace("/", "-")
            # Remove unicode
            import unicodedata
            name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
            name = re.sub(r'[^\w\-]', '', name)[:50]
        else:
            name = f"hinh_{i+1}"
            
        print(f"Exporting: {name}")
        
        temp_tex = f"svg_exports/{name}.tex"
        with open(temp_tex, "w", encoding="utf-8") as out:
            out.write(preamble + tikz_code + "\n" + postamble)
            
        # Compile to pdf
        subprocess.run(["xelatex", "-interaction=nonstopmode", f"{name}.tex"], cwd="svg_exports", capture_output=True, shell=True)
        
        pdf_file = f"svg_exports/{name}.pdf"
        svg_file = f"svg_exports/{name}.svg"
        if os.path.exists(pdf_file):
            # Convert PDF to SVG
            doc = fitz.open(pdf_file)
            page = doc[0]
            svg_content = page.get_svg_image()
            with open(svg_file, "w", encoding="utf-8") as svg_out:
                svg_out.write(svg_content)
            print(f"-> Created {svg_file}")
            
            # Cleanup
            doc.close()
            os.remove(pdf_file)
            os.remove(temp_tex)
            for ext in [".aux", ".log"]:
                if os.path.exists(f"svg_exports/{name}{ext}"):
                    os.remove(f"svg_exports/{name}{ext}")

if __name__ == '__main__':
    main()
