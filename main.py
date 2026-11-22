"""
VRA Analytics - Natalidad en Jujuy en el contexto nacional (2010-2024, proyeccion 2025-2027)
Proyecto Integrador (Programacion II + Ciencia de Datos)
Autores: Victoria, Romina y Abel

Como ejecutarla:
    pip install -r requirements.txt
    python app.py                 -> se abre en el navegador
    python app.py --escritorio    -> ventana de escritorio

Los datos salen del notebook y estan incrustados en datos_embebidos.py (ver preparar_datos.py),
asi la misma app funciona en el navegador y se puede publicar en GitHub Pages.
"""
import math
import sys
import unicodedata
from urllib.parse import quote

import flet as ft
import flet_charts as fc

from datos_embebidos import CLASIFICACION, ENTRENAMIENTO, IMPORTANCIA, INDICADORES, PROYECCIONES, REGRESION

# =====================================================================================
# PASO 1 - Datos, colores y funciones para consultarlos
# Se arman diccionarios para buscar rapido un valor por (provincia, año).
# =====================================================================================
PROVINCIAS = ["Jujuy", "Misiones", "Mendoza", "Buenos Aires", "Neuquén"]
REGION = {"Jujuy": "NOA", "Misiones": "NEA", "Mendoza": "Cuyo", "Buenos Aires": "Pampeana", "Neuquén": "Patagonia"}
# Colores fuertes y bien distintos entre si (Jujuy en rojo para que resalte)
COLOR = {"Jujuy": "#E31A1C", "Misiones": "#1F78B4", "Mendoza": "#2CA02C", "Buenos Aires": "#7B2CBF", "Neuquén": "#F2A900"}
AZUL, AZUL2, CELESTE = "#0B2A4A", "#1F4E79", "#7FB3E6"      # colores de la marca
TEXTO, GRIS, GRIS_CLARO = "#111827", "#4B5563", "#9CA3AF"    # texto principal, texto secundario (oscuro) y barras neutras
ANIOS = list(range(2010, 2025))
IND = {(r["PROVINCIA"], r["ANIO"]): r for r in INDICADORES}
PRO = {(r["PROVINCIA"], r["ANIO"]): r for r in PROYECCIONES}

# Opciones que eligen los interruptores y la provincia (las leen todas las pestañas)
ESTADO = {"prov": "Jujuy", "solo": False, "ext": False}
REFRESCAR = {"f": None}

# Correos para derivar consultas al equipo (los usa el asistente y el panel "Contactá a un analista").
# OJO: son direcciones de ejemplo con el dominio reservado ".example", que no existe de verdad: reemplazarlas por los correos reales
# del grupo antes de entregar. Si se deja "" en alguno, ese integrante se muestra sin boton de correo.
CONTACTOS = {"Victoria": "victoria@vra-analytics.example", "Romina": "romina@vra-analytics.example", "Abel": "abel@vra-analytics.example"}


def dato(prov, anio, col):
    return IND[(prov, anio)][col]


def cambio(prov):
    """Variacion porcentual de los nacimientos 2010 -> 2024."""
    return (dato(prov, 2024, "NACIMIENTOS") / dato(prov, 2010, "NACIMIENTOS") - 1) * 100


def error_lineal(prov):
    """Error anual (%) de la regresion lineal en la prueba 2022-2024."""
    return next(r["MAPE total anual (%)"] for r in REGRESION if r["Alcance"] == prov and r["Modelo"] == "Regresión lineal")


def f0(n):
    return f"{n:,.0f}".replace(",", ".").replace("-", "−")


def f1(n):
    return f"{n:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".").replace("-", "−")


def unir(lista):
    return lista[0] if len(lista) == 1 else ", ".join(lista[:-1]) + " y " + lista[-1]


def visibles(prov):
    """Provincias que se dibujan (todas, o solo Jujuy y la elegida si el interruptor esta activo). La elegida y Jujuy van al final."""
    resto = [q for q in PROVINCIAS if q not in ("Jujuy", prov)]
    todas = resto + ["Jujuy"] + ([prov] if prov != "Jujuy" else [])
    return [q for q in todas if not ESTADO["solo"] or q in ("Jujuy", prov)]


def grosor(q, prov):
    return 5 if q in ("Jujuy", prov) else 2.5


def cambiar(clave, valor):
    ESTADO[clave] = valor
    REFRESCAR["f"]()


# =====================================================================================
# PASO 2 - Piezas reutilizables: graficos nativos de Flet, leyenda y tarjetas
# Todos los graficos pasan por estas funciones, asi tienen ejes con titulo, numeros redondos y textos al pasar el cursor.
# =====================================================================================
def escala(valores):
    """Elige un eje con numeros redondos (por ejemplo 40, 60, 80...) que contenga todos los valores."""
    lo, hi = min(valores), max(valores)
    pasos = (0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000)   # hasta Buenos Aires (cientos de miles)
    paso = next((s for s in pasos if (hi - lo) / s <= 6), pasos[-1])                                                  # si ninguno sirve, usa el mas grande (no se rompe)
    return math.floor(lo / paso) * paso, math.ceil(hi / paso) * paso, paso


def marcas_numericas(lo, hi, paso):
    valores = [lo + i * paso for i in range(round((hi - lo) / paso) + 1)]
    return [fc.ChartAxisLabel(value=v, label=ft.Text(f1(v) if paso < 1 else f0(v), size=12, color=GRIS)) for v in valores]


def marcas_anios(desde, hasta):
    return [fc.ChartAxisLabel(value=a, label=ft.Text(str(a), size=12, color=GRIS)) for a in range(desde, hasta + 1, 2)]


def eje(titulo, etiquetas, tam, paso=None):
    extra = {"label_spacing": paso} if paso else {}
    return fc.ChartAxis(title=ft.Text(titulo, size=13, color=GRIS), title_size=28, label_size=tam, labels=etiquetas, **extra)


def texto_hover(texto):
    """Texto del cuadro que aparece al pasar el cursor: oscuro, grande y en negrita (se lee sobre fondo blanco con cualquier color)."""
    return fc.LineChartDataPointTooltip(text=texto, text_style=ft.TextStyle(size=15, weight=ft.FontWeight.W_700, color=AZUL))


def texto_hover_barra(texto):
    return fc.BarChartRodTooltip(text=texto, text_style=ft.TextStyle(size=15, weight=ft.FontWeight.W_700, color=AZUL))


def cuadro_hover():
    """Cuadro blanco con borde azul y esquinas redondeadas (antes era gris con letras de color)."""
    return fc.LineChartTooltip(bgcolor="white", border_radius=10, padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                               border_side=ft.BorderSide(2, AZUL2), fit_inside_horizontally=True, fit_inside_vertically=True)


def lineas(series, titulo_y, fmt, marca_x=None, nota=None, alto=380):
    """Grafico de lineas. series = lista de (puntos, color, grosor, punteada, nombre).
    El nombre aparece al pasar el cursor ("Jujuy · 2020: 68"); sin nombre, la linea no muestra texto."""
    lo, hi, paso = escala([y for s in series for _, y in s[0]])
    xs = [x for s in series for x, _ in s[0]]
    datos = []
    for pts, c, g, d, nombre in series:
        puntos = [fc.LineChartDataPoint(x, y, tooltip=texto_hover(f"{nombre} · {int(x)}: {fmt(y)}"), show_tooltip=True) if nombre
                  else fc.LineChartDataPoint(x, y, show_tooltip=False) for x, y in pts]
        datos.append(fc.LineChartData(points=puntos, color=c, stroke_width=g, dash_pattern=[8, 6] if d else None))
    if marca_x:   # linea vertical punteada (por ejemplo el ultimo año con datos)
        datos.append(fc.LineChartData(points=[fc.LineChartDataPoint(marca_x, v, tooltip=texto_hover(nota) if nota else None, show_tooltip=bool(nota)) for v in (lo, hi)],
                                      color=GRIS_CLARO, stroke_width=2, dash_pattern=[4, 4]))
    return fc.LineChart(data_series=datos, min_x=min(xs), max_x=max(xs), min_y=lo, max_y=hi, height=alto, expand=True, tooltip=cuadro_hover(),
                        left_axis=eje(titulo_y, marcas_numericas(lo, hi, paso), 56, paso),
                        bottom_axis=eje("Año", marcas_anios(int(min(xs)), int(max(xs))), 32, 2),
                        horizontal_grid_lines=fc.ChartGridLines(interval=paso, color="#E5E7EB", width=1))


def barras(items, titulo_x, titulo_y, alto=320, resaltar=None, abajo=False, tooltip_extra=""):
    """Grafico de barras. items = lista de (nombre, texto_del_valor, valor, color).
    El nombre y el valor van bajo cada barra; 'resaltar' pone ese nombre en rojo y negrita (Jujuy).
    Con abajo=True las barras cuelgan de la linea del 0 (valores negativos, para mostrar caidas): los nombres van arriba y los valores abajo."""
    lo, hi, paso = escala([0] + [v for _, _, v, _ in items])
    grupos = [fc.BarChartGroup(x=i, rods=[fc.BarChartRod(from_y=0, to_y=v, width=38, color=c, border_radius=4,
                                                         tooltip=texto_hover_barra(f"{n}: {t}{tooltip_extra}"))])
              for i, (n, t, v, c) in enumerate(items)]
    nombre_txt = lambda n: ft.Text(n, size=13 if n == resaltar else 12, weight=ft.FontWeight.W_700, color=COLOR["Jujuy"] if n == resaltar else TEXTO)
    centrado = ft.CrossAxisAlignment.CENTER
    marcas_y = marcas_numericas(lo, hi, paso)
    comun = dict(groups=grupos, min_y=lo, max_y=hi, height=alto, expand=True, tooltip=fc.BarChartTooltip(
        bgcolor="white", border_radius=10, padding=ft.Padding.symmetric(horizontal=12, vertical=8), border_side=ft.BorderSide(2, AZUL2)),
        horizontal_grid_lines=fc.ChartGridLines(interval=paso, color="#E5E7EB", width=1))
    if abajo:
        nombres = [fc.ChartAxisLabel(value=i, label=ft.Column([nombre_txt(n)], spacing=0, horizontal_alignment=centrado)) for i, (n, _, _, _) in enumerate(items)]
        valores = [fc.ChartAxisLabel(value=i, label=ft.Text(t, size=13, weight=ft.FontWeight.W_700, color=GRIS)) for i, (_, t, _, _) in enumerate(items)]
        return fc.BarChart(**comun, left_axis=eje(titulo_y, marcas_y, 56, paso), top_axis=eje(titulo_x, nombres, 30),
                           bottom_axis=fc.ChartAxis(labels=valores, label_size=30))
    etiquetas = [fc.ChartAxisLabel(value=i, label=ft.Column([nombre_txt(n), ft.Text(t, size=12, color=GRIS)], spacing=0, horizontal_alignment=centrado))
                 for i, (n, t, _, _) in enumerate(items)]
    return fc.BarChart(**comun, left_axis=eje(titulo_y, marcas_y, 56, paso), bottom_axis=eje(titulo_x, etiquetas, 56))


def barras_horizontales(items):
    """Barras con el nombre a la izquierda (para nombres largos que no entran bajo una barra vertical)."""
    filas = []
    for nombre, texto, valor, color in items:
        largo = max(1, round(valor))
        filas.append(ft.Row([ft.Text(nombre, size=13, weight=ft.FontWeight.W_600, color=TEXTO, width=150),
                             ft.Row([ft.Container(expand=largo, height=22, bgcolor=color, border_radius=4), ft.Container(expand=max(1, 100 - largo))],
                                    expand=True, spacing=0),
                             ft.Text(texto, size=13, color=GRIS, width=56, text_align=ft.TextAlign.END)], spacing=10))
    return ft.Column(filas, spacing=8)


def marca(color, forma):
    if isinstance(color, list):                      # varios colores: puntitos juntos
        return ft.Row([ft.Container(width=9, height=9, bgcolor=c, border_radius=5) for c in color], spacing=2, tight=True)
    if forma == "vertical":
        return ft.Container(width=3, height=15, bgcolor=color, border_radius=2)
    if forma == "horizontal":
        return ft.Container(width=18, height=3, bgcolor=color, border_radius=2)
    return ft.Container(width=14, height=14, bgcolor=color, border_radius=7)


def leyenda(items):
    """items = lista de (texto, color) o (texto, color, forma). Cada item ocupa solo su ancho para que queden en una fila."""
    return ft.Row([ft.Row([marca(i[1], i[2] if len(i) > 2 else "punto"), ft.Text(i[0], size=13, weight=ft.FontWeight.W_600, color=TEXTO)],
                          spacing=6, tight=True) for i in items], wrap=True, spacing=14, run_spacing=6)


def tarjeta(titulo, cuerpo, ayuda=None, col=None):
    hijos = [ft.Text(titulo, size=17, weight=ft.FontWeight.W_700, color=TEXTO)]
    if ayuda:
        hijos.append(ft.Text(ayuda, size=14, color=GRIS))
    return ft.Container(ft.Column(hijos + cuerpo, spacing=10), padding=20, bgcolor="white", border_radius=14,
                        border=ft.Border.all(1, "#E5E7EB"), col=col or {"xs": 12, "lg": 6})


def mensaje(hijos, color=AZUL2):
    """Recuadro celeste con la conclusion principal de cada pestaña, escrita en palabras simples."""
    return ft.Container(ft.Column(hijos, spacing=8), padding=18, border_radius=12, bgcolor=ft.Colors.with_opacity(0.07, color),
                        border=ft.Border.all(1, ft.Colors.with_opacity(0.35, color)), col={"xs": 12})


def dato_grande(titulo, valor):
    return ft.Column([ft.Text(titulo, size=13, color=GRIS), ft.Text(valor, size=22, weight=ft.FontWeight.W_800, color=TEXTO)], spacing=0)


def interruptor(texto, clave):
    return ft.Container(ft.Switch(label=texto, value=ESTADO[clave], active_color=AZUL2, on_change=lambda e: cambiar(clave, e.control.value)), col={"xs": 12})


def kpi(titulo, valor, detalle, color):
    return ft.Container(ft.Row([ft.Container(width=5, height=60, bgcolor=color, border_radius=3),
                                ft.Column([ft.Text(titulo, size=13, color=GRIS), ft.Text(valor, size=25, weight=ft.FontWeight.BOLD, color=TEXTO),
                                           ft.Text(detalle, size=13, weight=ft.FontWeight.W_600, color=color)], spacing=1)], spacing=12),
                        padding=16, bgcolor="white", border_radius=14, border=ft.Border.all(1, "#E5E7EB"), col={"xs": 12, "sm": 6, "lg": 3})


# =====================================================================================
# PASO 3 - Pestañas (una funcion por pestaña; todas reciben la provincia elegida p)
# =====================================================================================
def vista_resumen(p):
    """Nacimientos (indice 2010 = 100) y tasa de natalidad de las 5 provincias."""
    vis = visibles(p)
    indice, tasa = [], []
    for q in vis:
        base = dato(q, 2010, "NACIMIENTOS")
        indice.append(([(a, dato(q, a, "NACIMIENTOS") / base * 100) for a in ANIOS], COLOR[q], grosor(q, p), False, q))
        tasa.append(([(a, dato(q, a, "TASA")) for a in ANIOS], COLOR[q], grosor(q, p), False, q))
    indice.append(([(2010, 100), (2024, 100)], GRIS_CLARO, 2, True, None))      # referencia: nivel de 2010
    orden_leyenda = [q for q in PROVINCIAS if q in vis]
    # Leyendas autoexplicativas: cada una dice que numero es y de que año
    ley_i = leyenda([(f"{q}: en 2024 quedó en {100 + cambio(q):.0f}", COLOR[q]) for q in orden_leyenda] + [("Punto de partida: 2010 = 100", GRIS_CLARO, "horizontal")])
    ley_t = leyenda([(f"{q}: {f1(dato(q, 2024, 'TASA'))} en 2024", COLOR[q]) for q in orden_leyenda] + [("2022: cambio de base de población (Censo 2022)", GRIS_CLARO, "vertical")])
    nota = ft.Text("Desde 2022 el INDEC usa la población del Censo 2022: es un cambio de serie, no una variación real.", size=13, color=GRIS)
    return ft.ResponsiveRow([
        interruptor("Mostrar solo Jujuy y la provincia elegida", "solo"),
        tarjeta("¿Cuánto bajaron los nacimientos desde 2010?",
                [ley_i, lineas(indice, "Nacimientos (2010 = 100)", lambda v: f"{v:.0f} (2010 = 100)")],
                "Si en 2010 hubo 100 nacimientos, ¿cuántos hubo cada año? Por ejemplo, 47 significa que en 2024 nació menos de la mitad que en 2010."),
        tarjeta("Tasa de natalidad", [ley_t, lineas(tasa, "Nacimientos por 1.000 habitantes (‰)", lambda v: f"{f1(v)} ‰", marca_x=2022, nota="2022: el INDEC cambia la base de población"), nota],
                "Cuántos bebés nacen por cada 1.000 habitantes en un año. Sirve para comparar provincias de distinto tamaño."),
    ], spacing=14, run_spacing=14)


def vista_madres(p):
    """Madres menores de 20 años (2010 vs 2024, 5 provincias) y edad media de la madre."""
    grupos, etiquetas, bajas = [], [], {}
    for i, q in enumerate(PROVINCIAS):
        a, b = dato(q, 2010, "PCT_MENOR20"), dato(q, 2024, "PCT_MENOR20")
        bajas[q] = a - b
        varillas = [fc.BarChartRod(from_y=0, to_y=a, width=26, color=GRIS_CLARO, border_radius=4, tooltip=texto_hover_barra(f"{q} 2010: {f1(a)} % de madres menores de 20")),
                    fc.BarChartRod(from_y=0, to_y=b, width=26, color=COLOR[q], border_radius=4, tooltip=texto_hover_barra(f"{q} 2024: {f1(b)} % de madres menores de 20"))]
        grupos.append(fc.BarChartGroup(x=i, rods=varillas, spacing=4))
        es_j = q == "Jujuy"
        etiquetas.append(fc.ChartAxisLabel(value=i, label=ft.Column([
            ft.Text(q, size=13 if es_j else 12, weight=ft.FontWeight.W_700, color=COLOR["Jujuy"] if es_j else TEXTO),
            ft.Text(f"{f1(a)} → {f1(b)} %", size=12, color=GRIS),
            ft.Text(f"−{f1(a - b)} puntos", size=12, weight=ft.FontWeight.W_700, color=COLOR["Jujuy"] if es_j else GRIS)],
            spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER)))
    lo, hi, paso = escala([0] + [dato(q, 2010, "PCT_MENOR20") for q in PROVINCIAS])
    grafico_barras = fc.BarChart(groups=grupos, min_y=lo, max_y=hi, height=380, expand=True,
                                 tooltip=fc.BarChartTooltip(bgcolor="white", border_radius=10, padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                                                            border_side=ft.BorderSide(2, AZUL2)),
                                 left_axis=eje("Madres menores de 20 años (%)", marcas_numericas(lo, hi, paso), 56, paso),
                                 bottom_axis=eje("Provincia", etiquetas, 74),
                                 horizontal_grid_lines=fc.ChartGridLines(interval=paso, color="#E5E7EB", width=1))
    mayor = " Es la mayor baja de las cinco." if max(bajas, key=bajas.get) == "Jujuy" else ""
    vis = visibles(p)
    edad = [([(a, dato(q, a, "EDAD_MEDIA")) for a in ANIOS], COLOR[q], grosor(q, p), False, q) for q in vis]
    ley_e = leyenda([(f"{q}: {f1(dato(q, 2024, 'EDAD_MEDIA'))} años en 2024", COLOR[q]) for q in PROVINCIAS if q in vis])
    sube = max(PROVINCIAS, key=lambda q: dato(q, 2024, "EDAD_MEDIA") - dato(q, 2010, "EDAD_MEDIA"))
    return ft.ResponsiveRow([
        interruptor("Mostrar solo Jujuy y la provincia elegida", "solo"),
        tarjeta("Maternidad adolescente: 2010 vs 2024",
                [leyenda([("2010", GRIS_CLARO), ("2024 (color de cada provincia)", list(COLOR.values()))]), grafico_barras],
                f"Jujuy pasó de {f1(dato('Jujuy', 2010, 'PCT_MENOR20'))} % a {f1(dato('Jujuy', 2024, 'PCT_MENOR20'))} % de madres menores de 20 años.{mayor}"),
        tarjeta("Edad media de la madre", [ley_e, lineas(edad, "Edad media de la madre (años)", lambda v: f"{f1(v)} años")],
                f"Sube en todas las provincias. La mayor suba: {sube}, de {f1(dato(sube, 2010, 'EDAD_MEDIA'))} a {f1(dato(sube, 2024, 'EDAD_MEDIA'))} años."),
    ], spacing=14, run_spacing=14)


def vista_proyeccion(p):
    """Proyeccion 2025-2027 de la provincia elegida (la extension hasta 2030 es opcional y orientativa)."""
    hasta = 2030 if ESTADO["ext"] else 2027
    anios_p = range(2025, hasta + 1)
    obs = [(a, dato(p, a, "NACIMIENTOS")) for a in ANIOS]
    ultimo = obs[-1]

    def serie(col):
        return [ultimo] + [(a, PRO[(p, a)][col]) for a in anios_p]

    f27 = PRO[(p, 2027)]
    var = (f27["NACIMIENTOS_PROYECTADOS"] / ultimo[1] - 1) * 100
    resumen = mensaje([
        ft.Text(f"Si la tendencia actual continúa, {p} pasaría de {f0(ultimo[1])} nacimientos en 2024 a {f0(f27['NACIMIENTOS_PROYECTADOS'])} en 2027.",
                size=16, weight=ft.FontWeight.W_700, color=TEXTO),
        ft.Row([dato_grande("Cambio 2024 → 2027", f"{f1(var)} %"), dato_grande("Rango probable en 2027", f"{f0(f27['MINIMO'])} a {f0(f27['MAXIMO'])}"),
                dato_grande("Tasa estimada 2027", f"{f1(f27['TASA'])} ‰")], wrap=True, spacing=40, run_spacing=10),
        ft.Text(f"Confiabilidad: en la prueba con 2022-2024, este modelo se equivocó {f1(error_lineal(p))} % en el total anual.", size=14, color=GRIS)])
    grafico = lineas([(obs, COLOR[p], 5, False, "Observado"), (serie("NACIMIENTOS_PROYECTADOS"), TEXTO, 4, False, "Proyección central"),
                      (serie("MINIMO"), GRIS, 2.5, True, "Mínimo probable"), (serie("MAXIMO"), GRIS, 2.5, True, "Máximo probable")],
                     "Nacimientos por año", lambda v: f"{f0(v)} nacimientos", marca_x=2024, nota="Último dato real (2024)")
    filas = []
    for a in anios_p:
        f = PRO[(p, a)]
        est = {"italic": True, "color": GRIS} if a > 2027 else {}
        filas.append(ft.DataRow(cells=[
            ft.DataCell(ft.Text(f"{a}" + ("*" if a > 2027 else ""), **est)),
            ft.DataCell(ft.Text(f0(f["NACIMIENTOS_PROYECTADOS"]), weight=ft.FontWeight.W_700, **est)),
            ft.DataCell(ft.Text(f"{f0(f['MINIMO'])} a {f0(f['MAXIMO'])}", **est)),
            ft.DataCell(ft.Text(f"{f1((f['NACIMIENTOS_PROYECTADOS'] / ultimo[1] - 1) * 100)} %", **est)),
            ft.DataCell(ft.Text(f1(f["TASA"]), **est))]))
    tabla = ft.DataTable(columns=[ft.DataColumn(ft.Text(t, size=13)) for t in ("Año", "Nacimientos", "Rango probable", "vs 2024", "Tasa ‰")],
                         rows=filas, heading_row_height=38, data_row_min_height=36, data_row_max_height=38, column_spacing=18)
    pie_tabla = "Tasa = nacimientos por 1.000 habitantes (población proyectada por el INDEC)."
    if ESTADO["ext"]:
        pie_tabla = "* Extensión orientativa: la incertidumbre crece con el horizonte. " + pie_tabla
    # Variacion 2024 -> 2027 de cada provincia: una caida es un numero NEGATIVO (la barra cuelga hacia abajo)
    var27 = {q: (PRO[(q, 2027)]["NACIMIENTOS_PROYECTADOS"] / dato(q, 2024, "NACIMIENTOS") - 1) * 100 for q in PROVINCIAS}
    grupo = [q for q in PROVINCIAS if var27[q] <= min(var27.values()) + 1.5]
    menor = max(var27, key=var27.get)
    if len(grupo) == 1:
        conclusion = f"{grupo[0]} es la provincia donde más caerían los nacimientos ({f1(var27[grupo[0]])} %)."
    else:
        conclusion = f"{unir(grupo)} tienen las caídas más grandes y casi iguales (entre {f1(min(var27.values()))} % y {f1(max(var27[q] for q in grupo))} %)."
    conclusion += f" {menor} es la que menos cae ({f1(var27[menor])} %)."
    conclusion += " Cada barra hacia abajo es una caída respecto de 2024 (la línea del 0). Es lo que pasaría si la tendencia actual continúa."
    items = [(q, f"{f1(var27[q])} %", var27[q], COLOR[q]) for q in PROVINCIAS]
    return ft.ResponsiveRow([
        resumen,
        tarjeta(f"{p}: nacimientos observados y proyectados",
                [ft.Switch(label="Mostrar extensión 2028-2030 (orientativa)", value=ESTADO["ext"], active_color=AZUL2, on_change=lambda e: cambiar("ext", e.control.value)),
                 leyenda([("Observado", COLOR[p]), ("Proyección central", TEXTO), ("Rango probable (mínimo y máximo)", GRIS, "horizontal"),
                          ("Último dato real (2024)", GRIS_CLARO, "vertical")]), grafico],
                "El rango máximo incluye un escenario donde los nacimientos bajan más lento.", {"xs": 12, "lg": 7}),
        tarjeta("Valores proyectados", [tabla, ft.Text(pie_tabla, size=13, color=GRIS)],
                "Regresión lineal por perfil de madre, entrenada con 2014-2024.", {"xs": 12, "lg": 5}),
        tarjeta("¿Y las otras provincias? Cuánto cambiarían los nacimientos de 2024 a 2027",
                [barras(items, "Provincia (0 % = los nacimientos de 2024)", "Variación 2024 → 2027 (%)", 340, resaltar="Jujuy", abajo=True, tooltip_extra=" entre 2024 y 2027")],
                conclusion, {"xs": 12}),
    ], spacing=14, run_spacing=14)


VERDE_AZUL = "#3B82C4"


def titulo_chico(t):
    return ft.Text(t, size=14, weight=ft.FontWeight.W_700, color=TEXTO)


def texto_chico(t):
    return ft.Text(t, size=14, color=GRIS)


def linea_tiempo(desde, hasta, corte):
    """Un cuadradito por año: azul oscuro = años de entrenamiento, celeste = años de prueba."""
    return ft.Row([ft.Container(ft.Text(str(a), size=11, weight=ft.FontWeight.W_700, color="white" if a <= corte else AZUL), width=42, height=28,
                                border_radius=5, alignment=ft.Alignment(0, 0), bgcolor=AZUL2 if a <= corte else CELESTE)
                   for a in range(desde, hasta + 1)], spacing=3, wrap=True, run_spacing=3)


def tabla(columnas, filas, anchos, destacar=None):
    """Tabla propia: encabezado azul, filas alternadas y la fila destacada en celeste. Se desliza de costado si la pantalla es angosta."""
    def fila(textos, cabecera=False, fondo="white", fuerte=False):
        celdas = [ft.Container(ft.Text(t, size=13, weight=ft.FontWeight.W_700 if (cabecera or fuerte or i == 0) else ft.FontWeight.W_500,
                                        color="white" if cabecera else TEXTO), width=w, padding=ft.Padding.symmetric(horizontal=12, vertical=11))
                  for i, (t, w) in enumerate(zip(textos, anchos))]
        return ft.Container(ft.Row(celdas, spacing=0), bgcolor=fondo)
    cuerpo = [fila(columnas, cabecera=True, fondo=AZUL2)]
    for i, f in enumerate(filas):
        resaltada = destacar is not None and i == destacar
        cuerpo.append(fila(f, fondo="#DCEBFA" if resaltada else ("#F5F8FC" if i % 2 else "white"), fuerte=resaltada))
    return ft.Row([ft.Container(ft.Column(cuerpo, spacing=0), border_radius=10, border=ft.Border.all(1, "#D6E2F0"), clip_behavior=ft.ClipBehavior.HARD_EDGE)],
                  scroll=ft.ScrollMode.AUTO)


def referencia(termino, explicacion):
    return ft.Text(spans=[ft.TextSpan(termino + ": ", style=ft.TextStyle(weight=ft.FontWeight.W_700, color=TEXTO)), ft.TextSpan(explicacion)], size=13, color=GRIS)


def panel_tarea(color, tarea, que, probados, funciono, detalle):
    return ft.Container(ft.Column([
        ft.Text(tarea, size=13, weight=ft.FontWeight.W_800, color=color),
        ft.Text(que, size=16, weight=ft.FontWeight.W_700, color=TEXTO),
        ft.Text(probados, size=14, color=GRIS),
        ft.Container(ft.Text(funciono, size=14, weight=ft.FontWeight.W_700, color="white"), bgcolor=color, border_radius=8,
                     padding=ft.Padding.symmetric(horizontal=12, vertical=8)),
        ft.Text(detalle, size=13, color=GRIS)], spacing=8),
        padding=18, border_radius=12, bgcolor=ft.Colors.with_opacity(0.07, color), border=ft.Border.all(1, ft.Colors.with_opacity(0.35, color)),
        col={"xs": 12, "md": 6})


def tarjeta_resumen(p):
    """Que se entreno, con que fin y cuales modelos funcionaron (los demas se mencionan pero no se muestran)."""
    reg = [r for r in REGRESION if r["Alcance"] == p]
    otros = [r["MAPE total anual (%)"] for r in reg if r["Modelo"] != "Regresión lineal"]
    ga = {x["Modelo"]: x for x in CLASIFICACION if x["Alcance"].startswith("A")}
    arbol, rf, logi = ga["Árbol de decisión"], ga["Random Forest"], ga["Regresión logística"]
    veces = rf["Entrenamiento (ms)"] / arbol["Entrenamiento (ms)"]
    p1 = panel_tarea(AZUL2, "TAREA 1 · ESTIMAR NACIMIENTOS", "¿Cuántos bebés nacerán en un año?",
                     "Probamos 4 modelos: regresión lineal, regresión polinomial, Random Forest y Gradient Boosting.",
                     f"Funcionó: la regresión lineal (error de {f1(error_lineal(p))} % en {p})",
                     f"Los otros tres se equivocaron entre {f1(min(otros))} % y {f1(max(otros))} % en {p}, por eso no los usamos.")
    p2 = panel_tarea(VERDE_AZUL, "TAREA 2 · ENTENDER A LAS MADRES", "¿De qué edad es la madre?",
                     "Probamos 3 modelos: regresión logística, árbol de decisión y Random Forest.",
                     f"Funcionó: el árbol de decisión (acierta {f1(arbol['Accuracy'] * 100)} %)",
                     f"Random Forest acertó casi lo mismo ({f1(rf['Accuracy'] * 100)} %) pero tardó {veces:.0f} veces más en entrenar, y la regresión logística acertó menos "
                     f"({f1(logi['Accuracy'] * 100)} %).")
    return ft.Container(ft.Column([
        ft.Text("Probamos 7 modelos en 2 tareas y nos quedamos con los 2 que funcionaron", size=17, weight=ft.FontWeight.W_700, color=TEXTO),
        ft.Text("Un modelo es un programa que aprende de los datos de años anteriores. Probamos varios para cada tarea y elegimos el que mejor resultado dio; "
                "en esta pestaña mostramos solo esos dos.", size=14, color=GRIS),
        ft.ResponsiveRow([p1, p2], spacing=14, run_spacing=14)], spacing=12),
        padding=20, bgcolor="white", border_radius=14, border=ft.Border.all(1, "#E5E7EB"), col={"xs": 12})


def tarjeta_entrena_reg(p):
    e = ENTRENAMIENTO["regresion"][p]
    return tarjeta("Regresión lineal: cómo se entrenó", [
        leyenda([("Años de entrenamiento", AZUL2), ("Años de prueba (el modelo no los vio)", CELESTE)]),
        linea_tiempo(2014, 2024, 2021),
        titulo_chico("Qué predice"),
        texto_chico("Cuántos nacimientos habrá en cada año. Hay un modelo por provincia, porque cada una tiene su escala y su tendencia: si se mezclaran, "
                    "el modelo seguiría casi solo a Buenos Aires, que tiene muchos más nacimientos que Jujuy."),
        titulo_chico("Con qué datos"),
        texto_chico(f"El año, la edad de la madre, su nivel de instrucción y el tipo de parto. Cada año se divide en {ENTRENAMIENTO['perfiles']} perfiles de madre "
                    "(edad × instrucción × tipo de parto)."),
        titulo_chico("Cómo se entrenó y se probó"),
        texto_chico(f"Aprendió de 2014 a 2021 ({f0(e['train'])} nacimientos en {p}) y se probó con 2022 a 2024 ({f0(e['test'])}), años que no vio. "
                    "Se prueba con los años más recientes, y no al azar, porque lo que queremos es saber si sirve para el futuro."),
        titulo_chico("¿Por qué desde 2014 y no desde 2010?"),
        texto_chico("Porque 2014 fue el año con más nacimientos. Al probar distintos años de inicio vimos que arrancar en 2010 multiplicaba el error, y desde 2014 "
                    "el error baja a pocos puntos porcentuales en todas las provincias. El resto del análisis usa toda la serie 2010-2024; solo la ventana del modelo empieza en 2014."),
    ], "El modelo aprende del pasado y se evalúa con los años más recientes.", {"xs": 12, "lg": 6})


def tarjeta_entrena_arbol():
    c = ENTRENAMIENTO["clasificacion"]
    return tarjeta("Árbol de decisión: cómo se entrenó", [
        leyenda([("Años de entrenamiento", AZUL2), ("Años de prueba (el modelo no los vio)", CELESTE)]),
        linea_tiempo(2010, 2024, 2021),
        titulo_chico("Qué predice"),
        texto_chico("El grupo de edad de la madre: menor de 20, 20-24, 25-29, 30-34 o 35 o más."),
        titulo_chico("Con qué datos"),
        texto_chico("El año, la provincia, el nivel de instrucción, el tiempo de gestación, el peso al nacer, el tipo de parto y el sexo del bebé."),
        titulo_chico("Dos grupos de provincias"),
        texto_chico(f"Grupo A: Jujuy, Misiones, Mendoza y Neuquén juntas (entrenó con {f0(c['A']['train'])} nacimientos y se probó con {f0(c['A']['test'])}). "
                    f"Grupo B: Buenos Aires sola ({f0(c['B']['train'])} y {f0(c['B']['test'])}). Va aparte porque concentra el {f1(ENTRENAMIENTO['pct_ba'])} % "
                    "de los nacimientos y dominaría el resultado."),
        titulo_chico("Cómo se entrenó y se probó"),
        texto_chico("Aprendió de 2010 a 2021 (12 años) y se probó con 2022 a 2024 (3 años). Acá se usan todos los años disponibles: no hay que proyectar un total, "
                    "sino adivinar un grupo de edad, y así el árbol aprende con más datos."),
    ], "También se prueba con años que el modelo no vio.", {"xs": 12, "lg": 6})


def grafico_aciertos(a, b):
    """Dos pares de barras (uno por grupo de provincias): el arbol contra responder siempre el grupo mas frecuente."""
    grupos, etiquetas, valores = [], [], []
    for i, (g, quienes, x) in enumerate([("Grupo A", "Jujuy, Misiones, Mendoza y Neuquén", a), ("Grupo B", "Buenos Aires", b)]):
        ac, base = x["Accuracy"] * 100, x["Accuracy baseline"] * 100
        valores += [ac, base]
        grupos.append(fc.BarChartGroup(x=i, spacing=6, rods=[
            fc.BarChartRod(from_y=0, to_y=ac, width=70, color=AZUL2, border_radius=4, tooltip=texto_hover_barra(f"{g} · Árbol de decisión: acierta {f1(ac)} %")),
            fc.BarChartRod(from_y=0, to_y=base, width=70, color=GRIS_CLARO, border_radius=4,
                           tooltip=texto_hover_barra(f"{g} · Sin modelo (siempre 20-24 años): acierta {f1(base)} %"))]))
        etiquetas.append(fc.ChartAxisLabel(value=i, label=ft.Column([
            ft.Text(g, size=13, weight=ft.FontWeight.W_700, color=TEXTO), ft.Text(quienes, size=12, color=GRIS),
            ft.Text(f"Árbol {f1(ac)} % · Sin modelo {f1(base)} %", size=12, weight=ft.FontWeight.W_700, color=AZUL2)],
            spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER)))
    lo, hi, paso = escala([0] + valores)
    return fc.BarChart(groups=grupos, min_y=lo, max_y=hi, height=320, expand=True, group_spacing=40,
                       tooltip=fc.BarChartTooltip(bgcolor="white", border_radius=10, padding=ft.Padding.symmetric(horizontal=12, vertical=8), border_side=ft.BorderSide(2, AZUL2)),
                       left_axis=eje("Madres bien clasificadas (%)", marcas_numericas(lo, hi, paso), 56, paso), bottom_axis=eje("Grupo de provincias", etiquetas, 74),
                       horizontal_grid_lines=fc.ChartGridLines(interval=paso, color="#E5E7EB", width=1))


def arbol_ilustrativo():
    """Dibujo de ejemplo de como decide un arbol de decisión (cajas y flechas). No es el arbol real ni sus cifras."""
    centro = ft.CrossAxisAlignment.CENTER

    def pregunta(t):
        return ft.Container(ft.Text(t, size=13, weight=ft.FontWeight.W_700, color="white", text_align=ft.TextAlign.CENTER), bgcolor=AZUL2, border_radius=10,
                            padding=ft.Padding.symmetric(horizontal=14, vertical=10), alignment=ft.Alignment(0, 0))

    def hoja(t):
        return ft.Container(ft.Text(t, size=13, weight=ft.FontWeight.W_700, color=AZUL, text_align=ft.TextAlign.CENTER), bgcolor="#E3EDF8", border_radius=10,
                            border=ft.Border.all(1, CELESTE), padding=ft.Padding.symmetric(horizontal=14, vertical=10), alignment=ft.Alignment(0, 0), width=150)

    def rama(si_no):
        return ft.Column([ft.Container(ft.Text(si_no, size=12, weight=ft.FontWeight.W_800, color="white"), bgcolor="#3B82C4" if si_no == "Sí" else "#6B7280", border_radius=10,
                                       padding=ft.Padding.symmetric(horizontal=10, vertical=2)), ft.Text("↓", size=16, color=GRIS)], spacing=0, horizontal_alignment=centro)

    izquierda = ft.Column([rama("No"), hoja("Más probable: menor de 20 años")], horizontal_alignment=centro, spacing=2)
    derecha = ft.Column([rama("Sí"), pregunta("¿Tiene estudios superiores?"),
                         ft.Row([ft.Column([rama("No"), hoja("Más probable: 20-24 años")], horizontal_alignment=centro, spacing=2),
                                 ft.Column([rama("Sí"), hoja("Más probable: 30-34 años")], horizontal_alignment=centro, spacing=2)],
                                alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.START, spacing=16, wrap=True)],
                        horizontal_alignment=centro, spacing=2)
    esquema = ft.Column([pregunta("¿La madre terminó la secundaria?"),
                         ft.Row([izquierda, derecha], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.START, spacing=28, wrap=True, run_spacing=10)],
                        horizontal_alignment=centro, spacing=6)
    aviso = ft.Container(ft.Text("EJEMPLO ILUSTRATIVO: muestra cómo decide un árbol de decisión. No es el árbol real ni sus cifras (el real hace hasta 10 preguntas seguidas).",
                                 size=12, weight=ft.FontWeight.W_700, color="#92400E"), bgcolor="#FFF6E0", border=ft.Border.all(1, "#F2A900"), border_radius=8,
                         padding=ft.Padding.symmetric(horizontal=12, vertical=8))
    conclusion = ft.Container(ft.Text(f"En nuestros datos, el árbol usó el nivel de instrucción como la pregunta más importante ({f1(IMPORTANCIA['Nivel de instrucción'])} %). "
                                      "Las madres con menos estudios tienden a ser más jóvenes. Es una asociación, no una causa.", size=14, weight=ft.FontWeight.W_600, color=TEXTO),
                              bgcolor=ft.Colors.with_opacity(0.07, AZUL2), border=ft.Border.all(1, ft.Colors.with_opacity(0.35, AZUL2)), border_radius=10, padding=14)
    return tarjeta("¿Cómo decide el árbol?", [aviso, ft.Container(esquema, padding=ft.Padding.symmetric(vertical=8), alignment=ft.Alignment(0, 0)), conclusion],
                   "Un árbol de decisión hace preguntas de sí o no, una tras otra, hasta llegar a una respuesta.", {"xs": 12, "lg": 6})


def seccion(titulo, color):
    return ft.Container(ft.Row([ft.Container(width=6, height=26, bgcolor=color, border_radius=3), ft.Text(titulo, size=20, weight=ft.FontWeight.W_800, color=AZUL)], spacing=10),
                        col={"xs": 12}, padding=ft.Padding.only(top=10))


def vista_modelos(p):
    """Resultados de los dos modelos que funcionaron, explicados en lenguaje simple; las tablas tecnicas quedan al final."""
    err = lambda r: r["MAPE total anual (%)"]
    lineal = {r["Alcance"]: r for r in REGRESION if r["Modelo"] == "Regresión lineal"}
    por_prov = [(q, f"{f1(error_lineal(q))} %", error_lineal(q), COLOR[q]) for q in PROVINCIAS]
    cla = {(x["Alcance"][0], x["Modelo"]): x for x in CLASIFICACION}
    a, b = cla[("A", "Árbol de decisión")], cla[("B", "Árbol de decisión")]
    importancia = [(n, f"{f1(v)} %", v, AZUL2 if v > 50 else GRIS_CLARO) for n, v in IMPORTANCIA.items()]
    ejemplo = round(6000 * err(lineal[p]) / 100, -1)

    # Detalle tecnico: solo los modelos que funcionaron
    t_reg = tabla(["Provincia", "Error anual", "R²", "Entrenamiento (ms)", "Memoria (MB)"],
                  [[q, f"{f1(err(lineal[q]))} %", f"{lineal[q]['R2']:.2f}".replace(".", ","), f1(lineal[q]["Entrenamiento (ms)"]), f1(lineal[q]["RAM máx (MB)"])] for q in PROVINCIAS],
                  [170, 130, 90, 190, 150], destacar=PROVINCIAS.index(p))
    t_cla = tabla(["Grupo", "Provincias", "Acierto del árbol", "Acierto sin modelo", "F1", "Entrenamiento (ms)"],
                  [[g, quienes, f"{f1(x['Accuracy'] * 100)} %", f"{f1(x['Accuracy baseline'] * 100)} %", f"{f1(x['F1 ponderado'] * 100)} %", f1(x["Entrenamiento (ms)"])]
                   for g, quienes, x in (("Grupo A", "Jujuy, Misiones, Mendoza y Neuquén", a), ("Grupo B", "Buenos Aires", b))],
                  [110, 290, 160, 170, 90, 170])
    detalle = ft.ExpansionTile(title=ft.Text("Ver tablas con error, aciertos, tiempos y memoria", size=14, weight=ft.FontWeight.W_600), expanded=True, controls=[
        ft.Container(ft.Column([
            titulo_chico("Regresión lineal: estimar nacimientos (prueba 2022-2024, en la provincia elegida se resalta la fila)"), t_reg,
            titulo_chico("Árbol de decisión: adivinar el grupo de edad de la madre (prueba 2022-2024)"), t_cla,
            titulo_chico("Cómo leer las columnas"),
            referencia("Error anual", "cuánto se equivoca el modelo, en %, al estimar el total de nacimientos de un año. Cuanto menor, mejor."),
            referencia("R²", "de 0 a 1, qué parte de las diferencias entre perfiles de madres explica el modelo. No es lo mismo que el error anual: para proyectar importa el total del año."),
            referencia("Entrenamiento (ms) y Memoria (MB)", "lo que tardó en aprender, en milisegundos, y la memoria máxima que usó."),
            referencia("Acierto del árbol", "de cada 100 madres, a cuántas les adivinó bien el grupo de edad."),
            referencia("Acierto sin modelo", "lo que se acierta si siempre se responde el grupo más frecuente (20-24 años). Es la vara para saber si el árbol aporta algo."),
            referencia("F1", "acierto balanceado entre los cinco grupos de edad (100 % sería perfecto)."),
            ft.Text("Los otros modelos (polinomial, Random Forest, Gradient Boosting y regresión logística) también se entrenaron y midieron; sus resultados completos están en el notebook.",
                    size=13, italic=True, color=GRIS)], spacing=10), padding=ft.Padding.symmetric(horizontal=4, vertical=6))])
    return ft.ResponsiveRow([
        mensaje([ft.Text(f"Para {p}, el mejor modelo (regresión lineal) se equivoca solo {f1(err(lineal[p]))} % al estimar los nacimientos de un año completo.",
                         size=16, weight=ft.FontWeight.W_700, color=TEXTO),
                 ft.Text(f"Por ejemplo: si en un año nacen 6.000 bebés, el modelo se equivoca en unos {f0(ejemplo)}.", size=14, color=GRIS)]),
        tarjeta_resumen(p),
        seccion("Tarea 1 · Regresión lineal: estimar los nacimientos", AZUL2),
        tarjeta("Error de la regresión lineal por provincia", [barras(por_prov, "Provincia", "Error anual (%)", resaltar="Jujuy")],
                f"El modelo se equivoca menos en {min(PROVINCIAS, key=error_lineal)}. Cuanto más baja la barra, mejor."),
        tarjeta_entrena_reg(p),
        seccion("Tarea 2 · Árbol de decisión: entender a las madres", VERDE_AZUL),
        tarjeta_entrena_arbol(),
        tarjeta("¿Se puede adivinar la edad de la madre?",
                [leyenda([("Árbol de decisión", AZUL2), ("Sin modelo: responder siempre 20-24 años", GRIS_CLARO)]), grafico_aciertos(a, b)],
                f"Es difícil: de cada 10 madres, el árbol acierta la edad de casi {round(a['Accuracy'] * 10)}; sin modelo se acierta {round(a['Accuracy baseline'] * 10)}. "
                "Mejora la respuesta obvia, pero adivinar la edad sigue siendo complicado."),
        arbol_ilustrativo(),
        tarjeta("¿Qué variable pesa más?", [barras_horizontales(importancia)],
                "Muestra en qué datos se apoyó el árbol para decidir la edad de la madre. El nivel de instrucción pesa más: una madre muy joven rara vez tiene secundaria completa. "
                "Sirve para entender qué datos importan; no significa que la instrucción cause la edad."),
        seccion("Detalle técnico", GRIS_CLARO),
        tarjeta("Tablas de los modelos que funcionaron", [detalle], col={"xs": 12}),
    ], spacing=14, run_spacing=14)


# =====================================================================================
# PASO 4 - Asistente: responde con reglas (palabras clave), como ELIZA, usando los datos del tablero.
# No genera texto libre: solo plantillas con cifras reales; si no entiende, pregunta o deriva al equipo.
# Tambien tiene un mensaje oculto que se activa con las palabras "estoicismo" o "victoria".
# =====================================================================================
DESCRIPCION = ("VRA Analytics es una consultora de análisis de datos con base en Abra Pampa, Jujuy, y más de 10 años de experiencia. "
               "Nuestro objetivo como analistas es convertir datos públicos en información clara para que gobiernos, instituciones y familias de la región tomen mejores decisiones.")
SERVICIOS = ["Análisis demográfico y de natalidad para organismos de salud y municipios",
             "Tableros interactivos de indicadores, como este",
             "Proyecciones de población y de demanda de servicios (maternidades, escuelas, centros de salud)",
             "Informes de diagnóstico para decisiones públicas",
             "Capacitación en lectura de datos para equipos técnicos y de gestión"]
PERFIL = (DESCRIPCION + "\n\nQué hacemos:\n" + "\n".join(f"• {x}" for x in SERVICIOS) +
          "\n\nNuestro equipo de analistas: Victoria, Romina y Abel. Si querés hablar con alguno, pedime un contacto.")
TEMAS = [("Los datos", "#1F78B4", "Nacimientos, tasa de natalidad, madres y edad promedio de cada provincia."),
         ("Las proyecciones", "#2CA02C", "Cuántos bebés nacerán hasta 2027 y con qué margen de error."),
         ("Lo que descubrimos", "#7B2CBF", "Los patrones más claros, los modelos usados y qué tan confiables son."),
         ("VRA Analytics", "#E31A1C", "Quiénes somos, qué hacemos y cómo contactarnos.")]
ALIAS = {"Jujuy": ["jujuy"], "Misiones": ["misiones"], "Mendoza": ["mendoza"], "Buenos Aires": ["buenos aires", "bs as", "bsas"], "Neuquén": ["neuquen"]}
MENSAJE_OCULTO = """Una pausa antes de seguir.

Mi compañera Victoria siempre dice que hay cosas que dependen de nosotros y otras que no. Y cuanto más pasa el tiempo, más razón le encuentro.

Hay cosas que no podemos controlar: la nota, el resultado, saber de antemano si vamos a aprobar. Pero hay algo que sí está en nuestras manos: cómo caminamos hasta ahí.

Cuántas veces nos exigimos de más. Cuántas veces nos olvidamos de que detrás de cada parcial hay una persona que también se cansa, que también duda, y que igual sigue.

Por eso quiero decirles esto: si hicieron lo que podían, con lo que tenían, ya hicieron mucho. Dejar fluir, respirar y estar en paz con uno mismo también es una forma de aprobar.

Mucha calma y mucha fuerza a todos.

Y si el camino se complica un poco… siempre queda el recuperatorio. 😄

De parte de VRA Analytics."""


def sin_tildes(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")


def provincias_en(q):
    """Provincias mencionadas en el texto, en el orden en que aparecen."""
    pos = {p: min(q.find(c) for c in claves if c in q) for p, claves in ALIAS.items() if any(c in q for c in claves)}
    return sorted(pos, key=pos.get)


def comparar(a, b):
    d = lambda p, c, n=2024: dato(p, n, c)
    return (f"{a} vs {b}\n"
            f"• Nacimientos 2024: {f0(d(a, 'NACIMIENTOS'))} vs {f0(d(b, 'NACIMIENTOS'))} (cambio desde 2010: {f1(cambio(a))} % vs {f1(cambio(b))} %)\n"
            f"• Tasa de natalidad 2024: {f1(d(a, 'TASA'))} ‰ vs {f1(d(b, 'TASA'))} ‰\n"
            f"• Madres menores de 20: {f1(d(a, 'PCT_MENOR20'))} % vs {f1(d(b, 'PCT_MENOR20'))} % (en 2010: {f1(d(a, 'PCT_MENOR20', 2010))} % vs {f1(d(b, 'PCT_MENOR20', 2010))} %)\n"
            f"• Edad media de la madre: {f1(d(a, 'EDAD_MEDIA'))} vs {f1(d(b, 'EDAD_MEDIA'))} años\n"
            f"• Proyección 2027: {f0(PRO[(a, 2027)]['NACIMIENTOS_PROYECTADOS'])} vs {f0(PRO[(b, 2027)]['NACIMIENTOS_PROYECTADOS'])} nacimientos")


def resumen_provincia(p):
    """Informacion general de una provincia, para cuando solo se la nombra o se pide "informacion"."""
    f27 = PRO[(p, 2027)]
    return (f"{p} ({REGION[p]}): resumen\n"
            f"• Nacimientos: {f0(dato(p, 2024, 'NACIMIENTOS'))} en 2024 ({f1(cambio(p))} % desde 2010)\n"
            f"• Tasa de natalidad: {f1(dato(p, 2024, 'TASA'))} ‰ (en 2010: {f1(dato(p, 2010, 'TASA'))} ‰)\n"
            f"• Madres menores de 20: {f1(dato(p, 2024, 'PCT_MENOR20'))} % (en 2010: {f1(dato(p, 2010, 'PCT_MENOR20'))} %)\n"
            f"• Edad media de la madre: {f1(dato(p, 2024, 'EDAD_MEDIA'))} años (en 2010: {f1(dato(p, 2010, 'EDAD_MEDIA'))})\n"
            f"• Proyección 2027: {f0(f27['NACIMIENTOS_PROYECTADOS'])} nacimientos (rango {f0(f27['MINIMO'])} a {f0(f27['MAXIMO'])})\n"
            f"• Confiabilidad del modelo: error de {f1(error_lineal(p))} % en el total anual")


def patrones(p, quien):
    """Los hallazgos principales, en palabras simples y con cifras reales de la provincia."""
    return (f"Lo más importante que encontramos en {quien}:\n"
            f"• Nacen cada vez menos bebés: {f0(dato(p, 2010, 'NACIMIENTOS'))} en 2010 y {f0(dato(p, 2024, 'NACIMIENTOS'))} en 2024 ({f1(cambio(p))} %).\n"
            f"• Hay menos madres adolescentes: las menores de 20 años pasaron de {f1(dato(p, 2010, 'PCT_MENOR20'))} % a {f1(dato(p, 2024, 'PCT_MENOR20'))} % de los nacimientos.\n"
            f"• Las madres son cada vez mayores: la edad media subió de {f1(dato(p, 2010, 'EDAD_MEDIA'))} a {f1(dato(p, 2024, 'EDAD_MEDIA'))} años.\n"
            "• La caída es constante: en Jujuy, la correlación de Pearson entre el año y los nacimientos es −0,94 (muy cerca de −1: bajan casi todos los años).\n"
            f"• La edad de la madre y los estudios van de la mano: el árbol de decisión encontró que el nivel de instrucción es lo que más se asocia con la edad "
            f"(pesa {f0(IMPORTANCIA['Nivel de instrucción'])} %). Las madres con menos estudios tienden a ser más jóvenes. Es una relación, no una causa.")


def responder(texto, elegida):
    """Devuelve (respuesta, opciones, tipo). tipo: "" normal, "derivar" (ofrece escribirle al equipo) u "oculto" (mensaje especial)."""
    q = " " + sin_tildes(texto) + " "
    provs = provincias_en(q)
    prov = provs[0] if provs else elegida
    quien = prov if provs else f"{prov} (la provincia elegida)"
    anio = next((a for a in range(2010, 2031) if str(a) in q), None)
    tiene = lambda *claves: any(c in q for c in claves)

    if tiene("estoic", "victoria"):
        return MENSAJE_OCULTO, [], "oculto"
    if tiene(" hola", "buenas", "ayuda", "que podes", "que sabes"):
        return ("Soy el asistente de VRA Analytics. Puedo hablarte de los datos de natalidad de Jujuy, Misiones, Mendoza, Buenos Aires y Neuquén (2010-2024), "
                "de las proyecciones hasta 2027, de lo que descubrimos y de quiénes somos. Escribí tu pregunta."), [], ""
    if tiene("quienes son", "quienes somos", "quien es vra", "vra analytics", "empresa", "consultora", "servicio", "a que se dedic", "que hacen", "experiencia", "objetivo"):
        return PERFIL, [], ""
    if tiene("patron", "hallazgo", "descubr", "encontraron", "conclusion", "que aprendieron"):
        return patrones(prov, quien), ["Maternidad adolescente", "Proyección 2027"], ""
    if tiene("analista", "contacto", "contactar", "hablar con", "humano", "una persona"):
        return "Con gusto. Podés escribirle a alguien del equipo:", [], "derivar"
    if tiene("compar", "versus", " vs ", "diferencia", "contra"):
        if len(provs) >= 2:
            return comparar(provs[0], provs[1]), [], ""
        if len(provs) == 1 and provs[0] != "Jujuy":
            return comparar(provs[0], "Jujuy"), [], ""
        return "¿Qué provincias querés comparar?", [f"Jujuy vs {o}" for o in PROVINCIAS[1:]], ""
    if tiene("modelo", "algoritmo", "error", "mape", "acierto", "precision"):
        return (f"Probamos 7 modelos y nos quedamos con 2. Para estimar nacimientos funcionó la regresión lineal: en {quien} se equivoca {f1(error_lineal(prov))} % en el total anual "
                "(prueba con 2022-2024); gana porque los modelos de árbol no extrapolan tendencias. Para adivinar la edad de la madre funcionó el árbol de decisión: "
                "acierta cerca de 3 de cada 10 casos, contra 2 de cada 10 si siempre se responde el grupo más frecuente."), [], ""
    if tiene("mayor tasa", "menor tasa", "tasa mas alta", "tasa mas baja"):
        orden_t = sorted(PROVINCIAS, key=lambda x: -dato(x, 2024, "TASA"))
        return "Tasa de natalidad 2024 (de mayor a menor): " + "; ".join(f"{x} {f1(dato(x, 2024, 'TASA'))} ‰" for x in orden_t) + ".", [], ""
    if tiene("ranking", "mayor caida", "mas cayo", "cayeron", "mayor baja"):
        orden_c = sorted(PROVINCIAS, key=cambio)
        return ("Cambio de los nacimientos 2010-2024 (de mayor a menor caída): " + "; ".join(f"{x} {f1(cambio(x))} %" for x in orden_c) +
                f". {orden_c[0]} es donde más cayeron."), [], ""
    if tiene("mejor", "peor"):
        return "¿Mejor en qué sentido? Elegí una opción:", ["Mayor caída de nacimientos", "Mayor tasa de natalidad", "¿Qué modelo funciona mejor?"], ""
    if tiene("proyec", "predic", "futuro", "2025", "2026", "2027", "2028", "2029", "2030"):
        a = anio if anio and anio >= 2025 else 2027
        f = PRO[(prov, a)]
        nota = " (extensión orientativa: más incertidumbre)" if a > 2027 else ""
        return (f"{quien}, {a}{nota}: se proyectan {f0(f['NACIMIENTOS_PROYECTADOS'])} nacimientos (rango {f0(f['MINIMO'])} a {f0(f['MAXIMO'])}), "
                f"con una tasa de {f1(f['TASA'])} por mil habitantes."), [], ""
    if tiene("adolesc", "menor de 20", "menores de 20", "madres jovenes"):
        return (f"En {quien}, las madres menores de 20 años pasaron de {f1(dato(prov, 2010, 'PCT_MENOR20'))} % de los nacimientos en 2010 "
                f"a {f1(dato(prov, 2024, 'PCT_MENOR20'))} % en 2024."), [], ""
    if tiene("edad"):
        return (f"La edad media de las madres en {quien} subió de {f1(dato(prov, 2010, 'EDAD_MEDIA'))} años (2010) a "
                f"{f1(dato(prov, 2024, 'EDAD_MEDIA'))} años (2024): se posterga la maternidad."), [], ""
    if tiene("instruccion", "educacion", "secundaria", "estudio"):
        return ("En el modelo que predice el grupo de edad de la madre, el nivel de instrucción es la variable que más pesa "
                f"(cerca del {f0(IMPORTANCIA['Nivel de instrucción'])} %): una madre muy joven rara vez tiene secundaria completa."), [], ""
    if tiene("pearson", "correlacion"):
        return ("En Jujuy, la correlación de Pearson entre el año y los nacimientos es −0,94 (caída muy marcada); con el porcentaje de madres menores de 20 "
                "es −0,93 y con la edad media +0,93. Pearson mide asociación lineal, no prueba causalidad."), [], ""
    if tiene("2022", "serie", "indec", "censo"):
        return ("En 2022 el INDEC cambió la base de población (de Censo 2010 a Censo 2022), por eso la población tiene un salto ese año. "
                "Es un cambio de serie, no una variación real: solo se explica, no se corrige."), [], ""
    if tiene("tasa"):
        a = anio if anio and anio <= 2024 else 2024
        return f"La tasa de natalidad de {quien} en {a} fue {f1(dato(prov, a, 'TASA'))} por mil habitantes (en 2010: {f1(dato(prov, 2010, 'TASA'))}).", [], ""
    if tiene("nacimiento", "nacieron", "nacidos", "cuantos", "natalidad"):
        a = anio if anio and anio <= 2024 else 2024
        return f"En {quien} hubo {f0(dato(prov, a, 'NACIMIENTOS'))} nacimientos en {a} (en 2010: {f0(dato(prov, 2010, 'NACIMIENTOS'))}).", [], ""
    if provs or tiene("informacion", "info ", "resumen", "datos", "contame", "hablame", "decime"):
        opciones = [f"Proyección 2027 de {prov}"] + ([f"Comparar {prov} con Jujuy"] if prov != "Jujuy" else [])
        return resumen_provincia(prov), opciones, ""
    return ("No encontré eso en los datos. Solo puedo hablar de natalidad en Jujuy, Misiones, Mendoza, Buenos Aires y Neuquén (2010-2024) y de las "
            "proyecciones 2025-2027. Probá con alguno de los temas de la bienvenida o escribile a alguien del equipo:"), [], "derivar"


def botones_contacto(pregunta=""):
    """Un boton por integrante que abre el correo con el asunto y la consulta ya escritos (si el correo esta cargado)."""
    botones = []
    for nombre, correo in CONTACTOS.items():
        if correo:
            cuerpo = f"Hola {nombre}, tengo una consulta sobre el tablero de VRA Analytics.\n\n{pregunta}"
            botones.append(ft.OutlinedButton(content=ft.Text(f"Escribirle a {nombre}"), icon=ft.Icons.MAIL_OUTLINE,
                                             url=f"mailto:{correo}?subject={quote('Consulta desde VRA Analytics')}&body={quote(cuerpo)}"))
        else:
            botones.append(ft.Text(f"{nombre} (correo sin cargar)", size=13, color=GRIS))
    return botones


def bienvenida():
    """Primer mensaje del chat: los temas que se pueden consultar, agrupados y con un color cada uno."""
    filas = [ft.Row([ft.Container(width=5, height=44, bgcolor=c, border_radius=3),
                     ft.Column([ft.Text(t, size=14, weight=ft.FontWeight.W_800, color=c), ft.Text(d, size=13, color=GRIS)], spacing=0, expand=True)], spacing=10)
             for t, c, d in TEMAS]
    return ft.Container(ft.Column([ft.Text("¡Hola! Soy el asistente de VRA Analytics. Puedo ayudarte con:", size=15, weight=ft.FontWeight.W_700, color=TEXTO)] + filas +
                                  [ft.Text("Escribí tu pregunta abajo. Por ejemplo: «¿Cuántos nacimientos hubo en Jujuy en 2024?» o «¿Quiénes son VRA Analytics?»",
                                           size=13, italic=True, color=GRIS)], spacing=10),
                        padding=16, bgcolor="white", border_radius=14, border=ft.Border.all(1, CELESTE), max_width=640)


def crear_asistente(page):
    """Arma el chat (izquierda) y el panel con el perfil de la empresa y el contacto (derecha)."""
    mensajes = ft.ListView(spacing=10, height=400, auto_scroll=True)
    entrada = ft.TextField(hint_text="Escribí tu pregunta…", expand=True, border_radius=10, border_color=CELESTE, bgcolor="white", dense=True)

    def burbuja(texto, mio, oculto=False):
        if oculto:      # mensaje especial: una sola burbuja con los parrafos separados adentro
            contenido = ft.Column([ft.Text(par, size=14, color=TEXTO, selectable=True) for par in texto.split("\n\n")], spacing=10)
        else:
            contenido = ft.Text(texto, size=14, color="white" if mio else TEXTO, selectable=True)
        fondo = AZUL2 if mio else ("#FFF6E0" if oculto else "white")
        borde = None if mio else ft.Border.all(1, "#F2A900" if oculto else CELESTE)
        return ft.Row([ft.Container(contenido, padding=ft.Padding.symmetric(horizontal=14, vertical=10), bgcolor=fondo, border=borde,
                                    border_radius=14, max_width=760 if oculto else 640)],
                      alignment=ft.MainAxisAlignment.END if mio else ft.MainAxisAlignment.START)

    def opciones_fila(opciones):
        return ft.Row([ft.OutlinedButton(content=ft.Text(o), on_click=lambda e, o=o: enviar(o)) for o in opciones], wrap=True, spacing=8, run_spacing=6)

    def enviar(texto=None):
        texto = (texto or entrada.value or "").strip()
        if not texto:
            return
        respuesta, opciones, tipo = responder(texto, ESTADO["prov"])
        mensajes.controls.append(burbuja(texto, True))
        mensajes.controls.append(burbuja(respuesta, False, tipo == "oculto"))
        if tipo == "derivar":
            mensajes.controls.append(ft.Row(botones_contacto(texto), wrap=True, spacing=8, run_spacing=6))
        if opciones:
            mensajes.controls.append(opciones_fila(opciones))
        entrada.value = ""
        page.update()

    def borrar(e):
        del mensajes.controls[1:]
        page.update()

    mensajes.controls.append(bienvenida())
    entrada.on_submit = lambda e: enviar()
    mini_logo = ft.Container(ft.Row([ft.Text("V", size=14, weight=ft.FontWeight.W_900, color="white"), ft.Text("R", size=14, weight=ft.FontWeight.W_900, color=CELESTE),
                                     ft.Text("A", size=14, weight=ft.FontWeight.W_900, color="white")], spacing=0, tight=True),
                             width=44, height=44, border_radius=10, alignment=ft.Alignment(0, 0), border=ft.Border.all(2, CELESTE))
    cabecera = ft.Container(ft.Row([mini_logo, ft.Column([ft.Text("Asistente VRA", size=18, weight=ft.FontWeight.W_800, color="white"),
                                                          ft.Text("Responde con cifras reales de este tablero", size=13, color="#BFD7F0")], spacing=0)], spacing=12),
                            padding=16, gradient=ft.LinearGradient(begin=ft.Alignment(-1, 0), end=ft.Alignment(1, 0), colors=[AZUL, AZUL2]))
    cuerpo = ft.Container(ft.Column([mensajes, ft.Row([entrada, ft.IconButton(ft.Icons.SEND, icon_color="white", bgcolor=AZUL2, tooltip="Enviar", on_click=lambda e: enviar()),
                                                       ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=GRIS, tooltip="Borrar conversación", on_click=borrar)])], spacing=12),
                          padding=16, bgcolor="#EAF2FB")
    chat = ft.Container(ft.Column([cabecera, cuerpo], spacing=0), border_radius=14, border=ft.Border.all(1, "#D6E2F0"), clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        col={"xs": 12, "md": 8})
    puntos = [ft.Row([ft.Container(width=8, height=8, bgcolor=c, border_radius=4, margin=ft.Margin.only(top=6)), ft.Text(x, size=14, color=GRIS, expand=True)], spacing=8,
                     vertical_alignment=ft.CrossAxisAlignment.START) for x, c in zip(SERVICIOS, ["#E31A1C", "#1F78B4", "#2CA02C", "#7B2CBF", "#F2A900"])]
    panel = ft.Column([
        tarjeta("Sobre VRA Analytics", [ft.Text(DESCRIPCION, size=14, color=GRIS), ft.Text("Qué hacemos", size=14, weight=ft.FontWeight.W_700, color=TEXTO)] + puntos, col={"xs": 12}),
        tarjeta("Contactá a un analista", [ft.Text("Si tu consulta no está entre los temas, escribile al equipo:", size=14, color=GRIS)] + botones_contacto(), col={"xs": 12}),
    ], spacing=14, col={"xs": 12, "md": 4})
    return ft.ResponsiveRow([chat, panel], spacing=14, run_spacing=14)


# =====================================================================================
# PASO 5 - Pantalla principal: encabezado, selector de provincia, tarjetas y pestañas
# Al cambiar la provincia, un interruptor o la pestaña se vuelve a dibujar solo lo que corresponde.
# =====================================================================================
def nombres_equipo(tam=10, claro="white"):
    """VICTORIA · ROMINA · ABEL en mayusculas chicas, con la inicial resaltada (son las letras del logo)."""
    def uno(n):
        estilo = lambda color: ft.TextStyle(size=tam, weight=ft.FontWeight.W_700, color=color, letter_spacing=2)
        return ft.Row([ft.Text(n[0], style=estilo(CELESTE)), ft.Text(n[1:], style=estilo(claro))], spacing=0, tight=True)
    nombres = [uno(n) for n in ("VICTORIA", "ROMINA", "ABEL")]
    fila = [nombres[0], ft.Text("·", color=CELESTE), nombres[1], ft.Text("·", color=CELESTE), nombres[2]]
    return ft.Row(fila, spacing=8, tight=True, wrap=True)


def main(page: ft.Page):
    page.title = "VRA Analytics | Natalidad en Jujuy"
    page.bgcolor = "#F3F4F6"
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO

    # Encabezado: logo VRA con los nombres debajo | titulo centrado | selector de provincia
    logo = ft.Container(ft.Row([ft.Text("V", size=20, weight=ft.FontWeight.W_900, color="white"),
                                ft.Text("R", size=20, weight=ft.FontWeight.W_900, color=CELESTE),
                                ft.Text("A", size=20, weight=ft.FontWeight.W_900, color="white")], spacing=0, tight=True),
                        width=58, height=58, border_radius=12, alignment=ft.Alignment(0, 0), border=ft.Border.all(2, CELESTE),
                        gradient=ft.LinearGradient(begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1), colors=[AZUL, AZUL2]))
    izquierda = ft.Column([logo, ft.Container(height=1, width=190, bgcolor=ft.Colors.with_opacity(0.5, CELESTE)), nombres_equipo()],
                          horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=7)
    centro = ft.Column([ft.Text("VRA ANALYTICS", style=ft.TextStyle(size=12, weight=ft.FontWeight.W_700, color=CELESTE, letter_spacing=4)),
                        ft.Text("Natalidad en Jujuy en el contexto nacional", size=34, weight=ft.FontWeight.W_800, color="white", text_align=ft.TextAlign.CENTER),
                        ft.Text("2010-2024 · Nacimientos, tasa de natalidad y proyección", size=14, color="#BFD7F0", text_align=ft.TextAlign.CENTER)],
                       horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3)
    subtitulo = ft.Text("Jujuy · NOA", size=14, weight=ft.FontWeight.W_600, color="#BFD7F0")
    selector = ft.Dropdown(value="Jujuy", width=260, options=[ft.DropdownOption(key=q, text=q) for q in PROVINCIAS], filled=True, fill_color="white",
                           color=AZUL, text_size=16, border_color=CELESTE, border_width=2, on_select=lambda e: cambiar("prov", selector.value))
    derecha = ft.Column([ft.Text("Elegí una provincia ▼", size=13, color="#BFD7F0"), selector, subtitulo], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=4)
    encabezado = ft.Container(ft.ResponsiveRow([
        ft.Container(izquierda, col={"xs": 12, "md": 3}, alignment=ft.Alignment(0, 0)),
        ft.Container(centro, col={"xs": 12, "md": 6}, alignment=ft.Alignment(0, 0)),
        ft.Container(derecha, col={"xs": 12, "md": 3}, alignment=ft.Alignment(1, 0)),
    ], vertical_alignment=ft.CrossAxisAlignment.CENTER, run_spacing=14), padding=ft.Padding.symmetric(horizontal=26, vertical=20),
        gradient=ft.LinearGradient(begin=ft.Alignment(-1, 0), end=ft.Alignment(1, 0), colors=[AZUL, AZUL2]))

    kpis = ft.ResponsiveRow(spacing=14, run_spacing=14)
    cuerpo = ft.Container(padding=ft.Padding.only(top=14))
    asistente = crear_asistente(page)
    VISTAS = [vista_resumen, vista_madres, vista_proyeccion, vista_modelos, lambda p: asistente]
    tabs = ft.Tabs(length=5, selected_index=0, on_change=lambda e: dibujar(),
                   content=ft.TabBar(tabs=[ft.Tab(label=n) for n in ("Resumen", "Madres", "Proyección", "Modelos", "Asistente")]))

    def dibujar():
        """Redibuja las tarjetas de arriba y la pestaña activa para la provincia elegida."""
        p = ESTADO["prov"]
        f27 = PRO[(p, 2027)]
        kpis.controls = [
            kpi("Nacimientos 2024", f0(dato(p, 2024, "NACIMIENTOS")), f"{f1(cambio(p))} % vs 2010 ({f0(dato(p, 2010, 'NACIMIENTOS'))})", AZUL2),
            kpi("Tasa de natalidad 2024", f"{f1(dato(p, 2024, 'TASA'))} ‰", f"2010: {f1(dato(p, 2010, 'TASA'))} ‰", COLOR[p]),
            kpi("Madres menores de 20", f"{f1(dato(p, 2024, 'PCT_MENOR20'))} %", f"2010: {f1(dato(p, 2010, 'PCT_MENOR20'))} %", AZUL),
            kpi("Proyección 2027", f0(f27["NACIMIENTOS_PROYECTADOS"]), f"Rango {f0(f27['MINIMO'])} a {f0(f27['MAXIMO'])}", "#3B82C4"),
        ]
        subtitulo.value = f"{p} · {REGION[p]}" + ("" if p == "Jujuy" else "  (se compara con Jujuy)")
        cuerpo.content = VISTAS[tabs.selected_index](p)
        page.update()

    REFRESCAR["f"] = dibujar
    pie = ft.Container(ft.Column([nombres_equipo(10, "#374151"), ft.Text("VRA Analytics · Consultora de datos · Abra Pampa, Jujuy · Fuentes: DEIS (nacidos vivos) e INDEC (proyecciones de población)", size=12, color=GRIS)],
                                 horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6), padding=18, alignment=ft.Alignment(0, 0))
    page.add(encabezado, ft.Container(ft.Column([kpis, tabs, cuerpo], spacing=14), padding=ft.Padding.symmetric(horizontal=26, vertical=18)), pie)
    dibujar()


# Se ejecuta al abrir el archivo. En GitHub Pages (navegador, "emscripten") y en escritorio se abre tal cual;
# en tu computadora, por defecto, se abre en el navegador.
if sys.platform == "emscripten" or "--escritorio" in sys.argv:
    ft.run(main)
else:
    ft.run(main, view=ft.AppView.WEB_BROWSER)
