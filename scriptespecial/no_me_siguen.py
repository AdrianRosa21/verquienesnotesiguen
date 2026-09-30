#!/usr/bin/env python3
"""
no_me_siguen.py

Muestra las cuentas de Instagram que TÚ sigues pero que NO te siguen de vuelta.

Usa los archivos oficiales de "Descargar tu información" de Instagram
(followers_1.json / following.json, o su versión HTML). No pide contraseña
ni se conecta a Instagram.

Uso:
    python no_me_siguen.py                 # lee la carpeta ./datos
    python no_me_siguen.py RUTA            # carpeta descomprimida o archivo .zip
    python no_me_siguen.py --excepciones otro.txt
"""

import argparse
import csv
import json
import re
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from html import escape
from html.parser import HTMLParser
from pathlib import Path

CARPETA_SCRIPT = Path(__file__).resolve().parent

RE_SEGUIDORES = re.compile(r"^followers(_\d+)?\.(json|html)$", re.IGNORECASE)
RE_SEGUIDOS = re.compile(r"^following\.(json|html)$", re.IGNORECASE)
# Acepta https://www.instagram.com/usuario y https://www.instagram.com/_u/usuario
RE_PERFIL = re.compile(r"instagram\.com/(?:_u/)?([A-Za-z0-9._]+)/?(?:\?.*)?$")


# ---------------------------------------------------------------------------
# Lectura de los archivos de Instagram
# ---------------------------------------------------------------------------

def usuario_desde_url(url):
    coincidencia = RE_PERFIL.search(url or "")
    return coincidencia.group(1) if coincidencia else None


def items_con_usuarios(datos):
    """Recorre el JSON y devuelve cada bloque que trae 'string_list_data'."""
    if isinstance(datos, dict):
        if "string_list_data" in datos:
            yield datos
        else:
            for valor in datos.values():
                yield from items_con_usuarios(valor)
    elif isinstance(datos, list):
        for elemento in datos:
            yield from items_con_usuarios(elemento)


def usuarios_de_json(ruta):
    with open(ruta, encoding="utf-8") as archivo:
        datos = json.load(archivo)

    for item in items_con_usuarios(datos):
        entradas = item.get("string_list_data") or []
        primera = entradas[0] if entradas else {}
        # Según la versión del export, el nombre viene en 'value', en 'title'
        # o solo dentro del enlace.
        nombre = (
            primera.get("value")
            or item.get("title")
            or usuario_desde_url(primera.get("href", ""))
        )
        if nombre:
            yield nombre, primera.get("timestamp")


class _BuscadorDeEnlaces(HTMLParser):
    def __init__(self):
        super().__init__()
        self.usuarios = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            nombre = usuario_desde_url(dict(attrs).get("href"))
            if nombre:
                self.usuarios.append((nombre, None))


def usuarios_de_html(ruta):
    buscador = _BuscadorDeEnlaces()
    buscador.feed(Path(ruta).read_text(encoding="utf-8", errors="replace"))
    return buscador.usuarios


def leer_usuarios(archivos):
    """Devuelve {usuario_en_minusculas: timestamp o None}."""
    # Si hay JSON y HTML de lo mismo, con el JSON basta.
    solo_json = [a for a in archivos if a.suffix.lower() == ".json"]
    archivos = solo_json or archivos

    usuarios = {}
    for ruta in archivos:
        lector = usuarios_de_json if ruta.suffix.lower() == ".json" else usuarios_de_html
        for nombre, marca_de_tiempo in lector(ruta):
            # Instagram no distingue mayúsculas en los usuarios.
            usuarios.setdefault(nombre.lower(), marca_de_tiempo)
    return usuarios


def buscar_archivos(carpeta):
    seguidores, seguidos = [], []
    for ruta in sorted(carpeta.rglob("*")):
        if not ruta.is_file():
            continue
        if RE_SEGUIDORES.match(ruta.name):
            seguidores.append(ruta)
        elif RE_SEGUIDOS.match(ruta.name):
            seguidos.append(ruta)
    return seguidores, seguidos


def leer_excepciones(ruta):
    """Una cuenta por línea. Se ignoran líneas vacías, comentarios (#) y la @."""
    if not ruta.exists():
        return set()
    excepciones = set()
    for linea in ruta.read_text(encoding="utf-8-sig").splitlines():
        nombre = linea.split("#", 1)[0].strip().lstrip("@").lower()
        if nombre:
            excepciones.add(nombre)
    return excepciones


# ---------------------------------------------------------------------------
# Resultados
# ---------------------------------------------------------------------------

def formatear_fecha(marca_de_tiempo):
    if not marca_de_tiempo:
        return ""
    fecha = datetime.fromtimestamp(marca_de_tiempo, tz=timezone.utc)
    return fecha.strftime("%d/%m/%Y")


def guardar_txt(ruta, filas):
    ruta.write_text("\n".join(u for u, _ in filas) + "\n", encoding="utf-8")


def guardar_csv(ruta, filas):
    # utf-8-sig para que Excel abra bien el archivo.
    with open(ruta, "w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(["usuario", "enlace", "lo_sigues_desde"])
        for usuario, marca_de_tiempo in filas:
            escritor.writerow([
                usuario,
                f"https://www.instagram.com/{usuario}/",
                formatear_fecha(marca_de_tiempo),
            ])


PLANTILLA_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cuentas que no me siguen</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 720px; margin: 2rem auto; padding: 0 1rem; color: #222; }
  h1 { font-size: 1.4rem; }
  .resumen { color: #555; margin-bottom: 1rem; }
  table { width: 100%; border-collapse: collapse; }
  th, td { text-align: left; padding: .5rem; border-bottom: 1px solid #ddd; }
  tr.hecho a { text-decoration: line-through; color: #999; }
  tr.hecho td { color: #999; }
  a { color: #0645ad; }
</style>
</head>
<body>
<h1>Cuentas que sigo y no me siguen</h1>
<p class="resumen">Total: __TOTAL__ &middot; Pendientes: <strong id="pendientes">__TOTAL__</strong>.
Abre cada perfil, deja de seguirlo en Instagram y marca la casilla para llevar la cuenta.</p>
<table>
<thead><tr><th>#</th><th>Usuario</th><th>Lo sigues desde</th><th>Ya lo dejé</th></tr></thead>
<tbody>
__FILAS__
</tbody>
</table>
<script>
  var CLAVE = "scriptespecial_dejados";
  function cargar() {
    try { return JSON.parse(localStorage.getItem(CLAVE) || "[]"); } catch (e) { return []; }
  }
  function guardar(lista) {
    try { localStorage.setItem(CLAVE, JSON.stringify(lista)); } catch (e) {}
  }
  var dejados = cargar();
  var casillas = document.querySelectorAll("input[data-u]");
  function actualizar() {
    var pendientes = 0;
    casillas.forEach(function (c) {
      c.closest("tr").classList.toggle("hecho", c.checked);
      if (!c.checked) pendientes++;
    });
    document.getElementById("pendientes").textContent = pendientes;
  }
  casillas.forEach(function (c) {
    c.checked = dejados.indexOf(c.dataset.u) !== -1;
    c.addEventListener("change", function () {
      dejados = dejados.filter(function (u) { return u !== c.dataset.u; });
      if (c.checked) dejados.push(c.dataset.u);
      guardar(dejados);
      actualizar();
    });
  });
  actualizar();
</script>
</body>
</html>
"""


def guardar_html(ruta, filas):
    partes = []
    for numero, (usuario, marca_de_tiempo) in enumerate(filas, start=1):
        u = escape(usuario)
        partes.append(
            f'<tr><td>{numero}</td>'
            f'<td><a href="https://www.instagram.com/{u}/" target="_blank" rel="noopener">@{u}</a></td>'
            f'<td>{formatear_fecha(marca_de_tiempo)}</td>'
            f'<td><input type="checkbox" data-u="{u}"></td></tr>'
        )
    html = (
        PLANTILLA_HTML
        .replace("__TOTAL__", str(len(filas)))
        .replace("__FILAS__", "\n".join(partes))
    )
    ruta.write_text(html, encoding="utf-8")


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------

def analizar(carpeta, ruta_excepciones, carpeta_resultados):
    archivos_seguidores, archivos_seguidos = buscar_archivos(carpeta)

    if not archivos_seguidores or not archivos_seguidos:
        print("No encontré los archivos de Instagram en:", carpeta)
        print("Necesito followers_1.json y following.json (o sus versiones .html).")
        print("Mira el README.md para ver cómo descargarlos.")
        return 1

    seguidores = leer_usuarios(archivos_seguidores)
    seguidos = leer_usuarios(archivos_seguidos)

    if not seguidores or not seguidos:
        print("Los archivos se encontraron pero no pude leer usuarios de ellos.")
        print("Seguidores leídos:", len(seguidores), "| Seguidos leídos:", len(seguidos))
        return 1

    excepciones = leer_excepciones(ruta_excepciones)

    # Yo lo sigo (está en 'seguidos') y él a mí no (no está en 'seguidores').
    no_me_siguen = [
        (usuario, marca_de_tiempo)
        for usuario, marca_de_tiempo in seguidos.items()
        if usuario not in seguidores
    ]
    filas = [f for f in no_me_siguen if f[0] not in excepciones]
    omitidos = len(no_me_siguen) - len(filas)

    carpeta_resultados.mkdir(parents=True, exist_ok=True)
    guardar_txt(carpeta_resultados / "no_me_siguen.txt", filas)
    guardar_csv(carpeta_resultados / "no_me_siguen.csv", filas)
    guardar_html(carpeta_resultados / "no_me_siguen.html", filas)

    print(f"Te siguen:                {len(seguidores)}")
    print(f"Sigues:                   {len(seguidos)}")
    print(f"No te siguen de vuelta:   {len(filas)}", end="")
    print(f"  (más {omitidos} en excepciones)" if omitidos else "")
    print()
    for numero, (usuario, marca_de_tiempo) in enumerate(filas, start=1):
        fecha = formatear_fecha(marca_de_tiempo)
        print(f"{numero:>4}. @{usuario}" + (f"  (lo sigues desde {fecha})" if fecha else ""))
    print()
    print("Archivos generados en:", carpeta_resultados)
    print("  - no_me_siguen.html  (ábrelo en el navegador, tiene enlaces y casillas)")
    print("  - no_me_siguen.csv   (para Excel)")
    print("  - no_me_siguen.txt   (lista simple)")
    return 0


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Cuentas de Instagram que sigues y no te siguen de vuelta."
    )
    parser.add_argument(
        "ruta", nargs="?", default=str(CARPETA_SCRIPT / "datos"),
        help="carpeta con los archivos de Instagram, o el .zip descargado (por defecto: ./datos)",
    )
    parser.add_argument(
        "--excepciones", default=str(CARPETA_SCRIPT / "excepciones.txt"),
        help="archivo con cuentas que quieres seguir aunque no te sigan",
    )
    parser.add_argument(
        "--salida", default=str(CARPETA_SCRIPT / "resultados"),
        help="carpeta donde guardar los resultados (por defecto: ./resultados)",
    )
    args = parser.parse_args()

    ruta = Path(args.ruta).expanduser()
    if not ruta.exists():
        print("No existe la ruta:", ruta)
        return 1

    excepciones = Path(args.excepciones).expanduser()
    salida = Path(args.salida).expanduser()

    if ruta.is_file() and ruta.suffix.lower() == ".zip":
        with tempfile.TemporaryDirectory() as temporal:
            with zipfile.ZipFile(ruta) as zip_instagram:
                zip_instagram.extractall(temporal)
            return analizar(Path(temporal), excepciones, salida)

    if not ruta.is_dir():
        print("La ruta debe ser una carpeta o un archivo .zip:", ruta)
        return 1
    return analizar(ruta, excepciones, salida)


if __name__ == "__main__":
    sys.exit(main())
