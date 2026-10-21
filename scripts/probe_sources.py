"""Diagnóstico único de fontes públicas; respeito a robots.txt e bloqueios."""
from monitor import permitted,fetch,extract

TARGETS={
    "Sephora Brasil / ELF Lip Oil":"https://www.sephora.com.br/lip-oil-elf-cosmetics-glow-reviver-88992448-88992448.html",
    "Sephora Brasil / MAC Gloss":"https://www.sephora.com.br/gloss-mac-squirt-plumping-shimmer-88996457-821878.html",
    "OQVestir / BOSS Bomber":"https://www.oqvestir.com.br/jaqueta-masculina-bomber-h-coiner-bege-223231",
    "OQVestir / Vans Hylane":"https://www.oqvestir.com.br/tenis-unissex-ua-hylane-off-white-238290",
    "OQVestir / Vans Old Skool feminino":"https://www.oqvestir.com.br/tenis-feminino-old-skool-preto-235781",
    "OQVestir / Vans Old Skool masculino":"https://www.oqvestir.com.br/tenis-masculino-old-skool-preto-e-branco-260250",
    "Farfetch / Birkenstock":"https://www.farfetch.com/br/shopping/women/birkenstock-arizona-double-strap-sandals-item-16453016.aspx"
}
for name,url in TARGETS.items():
    allowed,reason=permitted(url)
    if not allowed:
        print(f"{name}: consulta omitida ({reason})")
        continue
    try:
        html=fetch(url)
        val=extract(html)
        print(f"{name}: HTML público acessível; preço BRL confirmado={val}" if val is not None else f"{name}: acessível, sem JSON-LD/metadados de preço BRL")
    except Exception as ex:
        print(f"{name}: HTTP indisponível ({type(ex).__name__}, status {getattr(ex,'code','?')})")
