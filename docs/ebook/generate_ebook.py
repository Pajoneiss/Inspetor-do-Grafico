
import os
import re

# Config
BASE_DIR = r"C:\Temp\Inspetor-do-Grafico\docs\ebook\pt"
OUTPUT_FILE = r"C:\Temp\Inspetor-do-Grafico\docs\ebook\O_INSPETOR_DO_GRAFICO_LIVRO_FINAL.html"
COVER_IMAGE = "capa_oficial.jpg"

# Ordem final dos arquivos
FILES = [
    "00_GUIA_DE_ESTUDO.md",
    "00_PREFACIO_A_VERDADE.md",
    "00_QUEM_NAO_DEVE_LER.md",
    "00_FUNDAMENTOS_ABSOLUTOS.md",
    "01_FUNDAMENTOS_CLASSICOS.md",
    "02_PRICE_ACTION_AVANCADO.md",
    "03_SMART_MONEY_CONCEPTS.md",
    "04_FERRAMENTAS_MATEMATICAS.md",
    "05_GESTAO_RISCO_PSICOLOGIA.md",
    "05_ILUSAO_DE_CONTROLE.md",
    "06_LIFESTYLE_SAUDE.md",
    "07_A_REVOLUCAO_INSPETOR.md",
    "08_MODALIDADES_ESTILOS.md",
    "09_ECOSSISTEMA_CRIPTO_SEGURANCA.md",
    "10_ANALISE_FUNDAMENTALISTA_MACRO.md",
    "11_HISTORIA_CRASHES.md",
    "12_MAPA_FINAL.md",
    "13_MERCADO_NAO_E_SUA_VIDA.md",
    "14_ENCERRAMENTO_FINAL.md"
]

# Mapping images to chapters
CHAPTER_IMAGES = {
    "00_FUNDAMENTOS": "images/ch00_basics_chart_axis.png",
    "01": "images/ch01_foundations.png",
    "02": "images/ch02_price_action.png",
    "03": "images/ch03_smart_money.png",
    "05_GESTAO": "images/ch05_psychology.png",
    "06": "images/ch06_lifestyle.png",
    "07": "images/ch07_ai.png",
    "09": "images/ch09_blockchain.png",
    "10": "images/ch10_macro.png",
    "11": "images/market_cycle.png",
    "12": "images/final_map.png",
    "13": "images/ch13_life_balance.png"
}

# Respiros Editoriais
RESPIRO_APOS_PREFACIO = '<div class="respiro"><p>"Se isso te incomodou, é porque funcionou."</p></div>'
RESPIRO_APOS_PSICOLOGIA = '<div class="respiro"><p>"A dor do stop é menor que a dor da falência."</p></div>'
RESPIRO_MEIO_DO_LIVRO = '<div class="respiro"><p>"Faça uma pausa. Respire. Volte amanhã."</p></div>'
RESPIRO_FINAL = '<div class="respiro"><p>"Você leu. Agora execute."</p></div>'


def md_to_html(text):
    # Escape HTML
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    # Headers
    text = re.sub(r'^# (.*?)$', r'<h1 class="chapter-title">\1</h1>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    
    # Bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Italic
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    
    # Blockquotes
    text = re.sub(r'^&gt; (.*?)$', r'<blockquote>\1</blockquote>', text, flags=re.MULTILINE)
    
    # Images
    text = re.sub(r'!\[(.*?)\]\((.*?)\)', r'<div class="img-container"><img src="\2" alt="\1"></div>', text)
    
    # Horizontal Rules
    text = re.sub(r'^---$', '<hr>', text, flags=re.MULTILINE)
    
    # Lists
    lines = text.split('\n')
    new_lines = []
    in_list = False
    
    for line in lines:
        if line.strip().startswith('* '):
            if not in_list:
                new_lines.append('<ul>')
                in_list = True
            content = line.strip()[2:]
            content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
            new_lines.append(f'<li>{content}</li>')
        else:
            if in_list:
                new_lines.append('</ul>')
                in_list = False
            new_lines.append(line)
            
    if in_list:
        new_lines.append('</ul>')
        
    text = '\n'.join(new_lines)
    
    # Paragraphs
    lines = text.split('\n')
    final_lines = []
    for line in lines:
        if line.strip() and not line.startswith('<') and not line.startswith('	'):
             final_lines.append(f'<p>{line}</p>')
        else:
             final_lines.append(line)
             
    return '\n'.join(final_lines)

CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Merriweather:ital,wght@0,300;0,400;0,700;0,900;1,300;1,400&family=Montserrat:wght@400;600;800&display=swap');

    @page {
        size: A4;
        margin: 2.5cm;
    }
    
    body {
        font-family: 'Merriweather', serif;
        font-size: 11pt;
        line-height: 1.7;
        color: #1a1a1a;
        background: white;
        max-width: 750px;
        margin: 0 auto;
        padding: 20px;
        text-align: justify;
    }
    
    h1, h2, h3, h4 {
        font-family: 'Montserrat', sans-serif;
        color: #000;
        margin-top: 2em;
        margin-bottom: 0.8em;
        text-align: left;
    }
    
    h1.chapter-title {
        font-size: 28pt;
        font-weight: 800;
        text-transform: uppercase;
        border-bottom: 3px solid #000;
        padding-bottom: 10px;
        margin-top: 0;
        text-align: left;
        page-break-before: always;
        color: #111;
    }
    
    h2 {
        font-size: 16pt;
        font-weight: 600;
        border-left: 4px solid #333;
        padding-left: 10px;
        margin-top: 2.5em; 
    }
    
    p {
        margin-bottom: 1em;
    }
    
    ul {
        margin-bottom: 1em;
        padding-left: 20px;
    }
    
    li {
        margin-bottom: 0.4em;
    }
    
    blockquote {
        font-style: italic;
        border-left: 3px solid #888;
        margin: 1.5em 1.5em;
        padding: 10px 15px;
        background: #f5f5f5;
        font-family: 'Montserrat', sans-serif;
        font-size: 10pt;
        color: #333;
    }
    
    .cover {
        width: 100%;
        height: 100vh;
        page-break-after: always;
        display: flex;
        justify-content: center;
        align-items: center;
        background: #000;
    }
    
    .cover img {
        max-width: 90%;
        max-height: 90%;
    }
    
    .page-break {
        page-break-after: always;
    }
    
    .legal {
        font-size: 9pt;
        color: #666;
        margin-top: 40vh;
        text-align: center;
    }
    
    .img-container {
        text-align: center;
        margin: 2em 0;
    }
    
    img {
        max-width: 100%;
        border: 1px solid #ccc;
        border-radius: 4px;
    }
    
    hr {
        border: none;
        border-top: 1px solid #ccc;
        margin: 2em 0;
    }
    
    .respiro {
        page-break-before: always;
        page-break-after: always;
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 60vh;
        text-align: center;
    }
    
    .respiro p {
        font-family: 'Montserrat', sans-serif;
        font-size: 14pt;
        font-style: italic;
        color: #555;
        max-width: 60%;
    }
</style>
"""

HTML_START = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>O Inspetor do Gráfico - Edição Definitiva</title>
    {CSS}
</head>
<body>

<!-- CAPA -->
<div class="cover">
    <img src="{COVER_IMAGE}" alt="Capa O Inspetor do Gráfico">
</div>

<!-- COPYRIGHT -->
<div class="page-break">
    <div class="legal">
        <p><strong>O Inspetor do Gráfico</strong></p>
        <p>Edição Definitiva - 2026</p>
        <p>Copyright © 2026 Ladder Labs & Inspetor Team.</p>
        <p>Todos os direitos reservados.</p>
        <br>
        <p><em>Disclaimer: Este material tem caráter estritamente educacional. O trading de ativos financeiros envolve risco substancial de perda e não é adequado para todos os investidores. O desempenho passado não é garantia de resultados futuros. O autor e a editora não se responsabilizam por quaisquer perdas financeiras decorrentes do uso das informações aqui contidas.</em></p>
    </div>
</div>
"""

HTML_END = """
</body>
</html>
"""

def generate():
    content_html = HTML_START
    
    for i, filename in enumerate(FILES):
        path = os.path.join(BASE_DIR, filename)
        
        # Respiros estratégicos
        if filename == "01_FUNDAMENTOS_CLASSICOS.md":
            content_html += RESPIRO_APOS_PREFACIO
        if filename == "06_LIFESTYLE_SAUDE.md":
            content_html += RESPIRO_APOS_PSICOLOGIA
        if filename == "10_ANALISE_FUNDAMENTALISTA_MACRO.md":
            content_html += RESPIRO_MEIO_DO_LIVRO
        if filename == "14_ENCERRAMENTO_FINAL.md":
            content_html += RESPIRO_FINAL
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                mk_content = f.read()
                content_html += md_to_html(mk_content)
        except FileNotFoundError:
            print(f"AVISO: Arquivo não encontrado: {filename}")
            continue
        
    content_html += HTML_END
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(content_html)
    
    print(f"Livro DEFINITIVO gerado em: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate()
