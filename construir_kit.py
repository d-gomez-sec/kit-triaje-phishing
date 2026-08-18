# -*- coding: utf-8 -*-
"""Funde las 4 herramientas en un solo HTML (sin iframes).
   CSS: cada regla se limita a #appN. JS: cada script en una IIFE con
   un 'document' acotado a su contenedor. No se toca el codigo original."""
import re, os, io

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "herramientas")
APPS = [
    ("analizador-cabeceras.html",   "Analizador de Cabeceras",  "\u2709\ufe0f",
     "\u00bfQui\u00e9n envi\u00f3 de verdad este correo? Lee SPF, DKIM y DMARC y el viaje del mensaje.",
     "correo sospechoso \u2192"),
    ("expansor-acortados.html",     "Expansor de Enlaces",      "\U0001F517",
     "\u00bfA d\u00f3nde lleva de verdad un enlace corto? Sigue los saltos hasta el destino real.",
     "\u2192 enlace del correo \u2192"),
    ("detector-homografos-v4.html", "Detector de Hom\u00f3grafos", "\U0001F3AD",
     "\u00bfEl dominio imita a una marca con letras falsas? Caza suplantaciones en URLs.",
     "\u2192 URL de destino \u2192"),
    ("verificador-archivos.html",   "Verificador de Archivos",  "\U0001F4C4",
     "\u00bfEl adjunto es lo que dice ser? Magic bytes, doble extensi\u00f3n y contenido activo.",
     "\u2192 adjunto del correo"),
]

def trocear(txt):
    style = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", txt, re.S))
    script = "\n".join(re.findall(r"<script[^>]*>(.*?)</script>", txt, re.S))
    m = re.search(r"<body[^>]*>(.*?)</body>", txt, re.S)
    body = m.group(1) if m else ""
    body = re.sub(r"<script[^>]*>.*?</script>", "", body, flags=re.S)
    return style, body, script

def ambito_selector(sel, amb):
    # Un comentario pegado al selector impedia reconocerlo: se extrae y se repone.
    comentarios = "".join(re.findall(r"/\*.*?\*/", sel, re.S))
    sel = re.sub(r"/\*.*?\*/", "", sel, flags=re.S)
    fuera = []
    for p in [x.strip() for x in sel.split(",")]:
        if not p:
            continue
        if p in (":root", "html", "body"):
            fuera.append(amb)
        elif p == "*":
            fuera.append(amb + ", " + amb + " *")
        elif p.startswith("body"):
            fuera.append(amb + p[4:])
        elif p.startswith("html"):
            fuera.append(amb + p[4:])
        else:
            fuera.append(amb + " " + p)
    return comentarios + "\n" + ", ".join(fuera)

def ambito_css(css, amb):
    salida, i, n = [], 0, len(css)
    corte = re.compile(r"[{};]")
    while i < n:
        if css.startswith("/*", i):
            j = css.find("*/", i + 2)
            j = n if j == -1 else j + 2
            salida.append(css[i:j]); i = j; continue
        m = corte.search(css, i)
        if not m:
            salida.append(css[i:]); break
        if m.group() == "{":
            sel = css[i:m.start()]
            ini = m.end()
            prof, j = 1, ini
            while j < n and prof > 0:
                if css[j] == "{": prof += 1
                elif css[j] == "}": prof -= 1
                j += 1
            cuerpo = css[ini:j-1]
            limpio = sel.strip()
            if limpio.startswith("@"):
                arroba = limpio.split()[0].lower()
                if arroba in ("@media", "@supports", "@layer", "@document"):
                    salida.append(sel + "{" + ambito_css(cuerpo, amb) + "}")
                else:
                    salida.append(sel + "{" + cuerpo + "}")
            else:
                salida.append(ambito_selector(sel, amb) + "{" + cuerpo + "}")
            i = j
        else:
            salida.append(css[i:m.end()]); i = m.end()
    return "".join(salida)

CABECERA_JS = """(function(){
  /* 'document' falso: solo ve dentro de #%(amb)s, asi los IDs repetidos
     entre herramientas no se pisan y el codigo original no cambia. */
  var __raiz = window.document.getElementById("%(amb)s");
  var document = {
    getElementById   : function(id){ return __raiz.querySelector("#" + id); },
    querySelector    : function(s){ return __raiz.querySelector(s); },
    querySelectorAll : function(s){ return __raiz.querySelectorAll(s); },
    createElement    : function(t){ return window.document.createElement(t); },
    createTextNode   : function(t){ return window.document.createTextNode(t); },
    execCommand      : function(){ return window.document.execCommand.apply(window.document, arguments); },
    addEventListener : function(){ return window.document.addEventListener.apply(window.document, arguments); },
    documentElement  : window.document.documentElement,
    get body(){ return __raiz; }
  };
  /* ---- codigo original de la herramienta, sin tocar ---- */
"""
PIE_JS = "\n})();\n"

estilos, cuerpos, guiones, tarjetas = [], [], [], []
for idx, (arch, nombre, ic, desc, flujo) in enumerate(APPS):
    amb = "app%d" % idx
    with io.open(os.path.join(DIR, arch), encoding="utf-8") as f:
        txt = f.read()
    st, bd, sc = trocear(txt)
    estilos.append("/* ===== %s ===== */\n%s" % (nombre, ambito_css(st, "#" + amb)))
    cuerpos.append('<section class="pane" id="%s">\n%s\n</section>' % (amb, bd.strip()))
    guiones.append((CABECERA_JS % {"amb": amb}) + sc + PIE_JS)
    tarjetas.append(
        '      <button class="tarjeta" data-ir="%s">\n'
        '        <span class="ic">%s</span>\n'
        '        <span class="nom">%s</span>\n'
        '        <span class="desc">%s</span>\n'
        '        <span class="flujo">%s</span>\n'
        '      </button>' % (amb, ic, nombre, desc, flujo))

CSS_LANZADOR = """
  :root{
    --k-fondo:#0d1117; --k-tinta:#c9d1d9; --k-panel:#161b22; --k-linea:#2a313c;
    --k-verde:#3fb950; --k-tenue:#8b949e;
    --k-mono:'Courier New',ui-monospace,monospace;
    --k-sans:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
  }
  html,body{margin:0;padding:0;background:var(--k-fondo);color:var(--k-tinta);
            font-family:var(--k-sans);min-height:100%}
  #menu{max-width:720px;margin:0 auto;padding:2rem 1rem 4rem}
  #menu header{text-align:center;margin-bottom:2rem}
  #menu h1{font-size:1.7rem;color:#e6edf3;letter-spacing:-.01em;margin:0}
  #menu h1::before{content:"> ";color:var(--k-verde);font-family:var(--k-mono)}
  #menu header p{color:var(--k-tenue);font-size:.95rem;margin:.5rem auto 0;line-height:1.5;max-width:520px}
  #rejilla{display:grid;grid-template-columns:1fr 1fr;gap:.9rem}
  @media (max-width:560px){ #rejilla{grid-template-columns:1fr} }
  .tarjeta{background:var(--k-panel);border:1px solid var(--k-linea);border-radius:14px;
           padding:1.2rem;cursor:pointer;text-align:left;font-family:var(--k-sans);
           transition:border-color .15s,transform .1s;
           box-shadow:0 1px 2px rgba(0,0,0,.3),0 6px 18px rgba(0,0,0,.2)}
  .tarjeta:hover{border-color:var(--k-verde);transform:translateY(-2px)}
  .tarjeta:focus-visible{outline:3px solid var(--k-verde);outline-offset:2px}
  .tarjeta .ic{font-size:1.8rem;display:block;margin-bottom:.6rem}
  .tarjeta .nom{font-weight:700;font-size:1.02rem;color:#e6edf3;display:block}
  .tarjeta .desc{font-size:.85rem;color:var(--k-tenue);margin-top:.35rem;line-height:1.4;display:block}
  .tarjeta .flujo{font-family:var(--k-mono);font-size:.7rem;color:var(--k-verde);
                  margin-top:.7rem;letter-spacing:.03em;display:block}
  #pie{margin-top:2rem;font-size:.78rem;color:var(--k-tenue);text-align:center;line-height:1.5}

  #barra{display:none;align-items:center;gap:.6rem;padding:.7rem 1rem;background:var(--k-panel);
         border-bottom:1px solid var(--k-linea);position:sticky;top:0;z-index:99}
  #barra.visible{display:flex}
  #volver{background:#21262d;color:var(--k-tinta);border:1px solid var(--k-linea);border-radius:8px;
          padding:.45rem .9rem;font-family:var(--k-sans);font-weight:600;font-size:.85rem;cursor:pointer}
  #volver:hover{border-color:var(--k-verde)}
  #volver:focus-visible{outline:3px solid var(--k-verde);outline-offset:2px}
  #tituloVista{font-weight:700;font-size:.95rem;color:#e6edf3;font-family:var(--k-mono)}
  .pane{display:none}
  .pane.activo{display:block}
"""

JS_LANZADOR = """
(function(){
  var menu = document.getElementById("menu"),
      barra = document.getElementById("barra"),
      titulo = document.getElementById("tituloVista");
  function abrir(amb, nombre){
    menu.style.display = "none";
    var todas = document.querySelectorAll(".pane");
    for (var i=0;i<todas.length;i++) todas[i].className = "pane";
    document.getElementById(amb).className = "pane activo";
    titulo.textContent = nombre;
    barra.className = "visible";
    window.scrollTo(0,0);
  }
  function volver(){
    var todas = document.querySelectorAll(".pane");
    for (var i=0;i<todas.length;i++) todas[i].className = "pane";
    barra.className = "";
    menu.style.display = "block";
    window.scrollTo(0,0);
  }
  var btns = document.querySelectorAll(".tarjeta");
  for (var i=0;i<btns.length;i++){
    (function(b){
      b.addEventListener("click", function(){
        abrir(b.getAttribute("data-ir"), b.querySelector(".nom").textContent);
      });
    })(btns[i]);
  }
  document.getElementById("volver").addEventListener("click", volver);
})();
"""

doc = u"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Kit de Triaje \u00b7 Ciberseguridad</title>
<style>
/* ================= LANZADOR ================= */
%(css_lanzador)s

/* ===== ESTILOS DE LAS HERRAMIENTAS (cada uno limitado a su #appN) ===== */
%(estilos)s
</style>
</head>
<body>

<div id="barra">
  <button id="volver">\u2190 Volver</button>
  <span id="tituloVista"></span>
</div>

<div id="menu">
  <header>
    <h1>Kit de Triaje</h1>
    <p>Cuatro herramientas para analizar correos, enlaces y archivos sospechosos.
       Todo el an\u00e1lisis ocurre en tu dispositivo.</p>
  </header>
  <div id="rejilla">
%(tarjetas)s
  </div>
  <div id="pie">Archivo \u00fanico y autocontenido \u00b7 sin iframes \u00b7 funciona sin conexi\u00f3n.</div>
</div>

%(cuerpos)s

<script>
%(js_lanzador)s
</script>

%(guiones)s

</body>
</html>
""" % {
    "css_lanzador": CSS_LANZADOR,
    "estilos": "\n\n".join(estilos),
    "tarjetas": "\n".join(tarjetas),
    "cuerpos": "\n\n".join(cuerpos),
    "js_lanzador": JS_LANZADOR,
    "guiones": "\n".join("<script>\n%s\n</script>" % g for g in guiones),
}

destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kit-ciberseguridad.html")
with io.open(destino, "w", encoding="utf-8") as f:
    f.write(doc)
print("Generado %s : %d bytes" % (destino, len(doc.encode("utf-8"))))

