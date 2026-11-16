"""
VRA Analytics - Natalidad en Jujuy en el contexto nacional (2010-2024, proyeccion 2025-2027)
Proyecto Integrador (Programacion II + Ciencia de Datos)
Autores: Gutierres, Suares, Valerio

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

import flet as ft
import flet_charts as fc

from datos_embebidos import CLASIFICACION, IMPORTANCIA, INDICADORES, PROYECCIONES, REGRESION

# =====================================================================================
# PASO 1 - Datos, colores y funciones para consultarlos
# Se arman diccionarios para buscar rapido un valor por (provincia, año).
# =====================================================================================
PROVINCIAS = ["Jujuy", "Misiones", "Mendoza", "Buenos Aires", "Neuquén"]
REGION = {"Jujuy": "NOA", "Misiones": "NEA", "Mendoza": "Cuyo", "Buenos Aires": "Pampeana", "Neuquén": "Patagonia"}
# Colores fuertes y bien distintos entre si (Jujuy en rojo para que resalte)
COLOR = {"Jujuy": "#E31A1C", "Misiones": "#1F78B4", "Mendoza": "#2CA02C", "Buenos Aires": "#7B2CBF", "Neuquén": "#F2A900"}
GRIS, TEXTO, AZUL = "#6B7280", "#111827", "#0B2A4A"
ANIOS = list(range(2010, 2025))
IND = {(r["PROVINCIA"], r["ANIO"]): r for r in INDICADORES}
PRO = {(r["PROVINCIA"], r["ANIO"]): r for r in PROYECCIONES}


def dato(prov, anio, col):
    return IND[(prov, anio)][col]


def cambio(prov):
    """Variacion porcentual de los nacimientos 2010 -> 2024."""
    return (dato(prov, 2024, "NACIMIENTOS") / dato(prov, 2010, "NACIMIENTOS") - 1) * 100


def error_lineal(prov):
    """Error anual (%) de la regresion lineal en la prueba 2022-2024."""
    return next(r["MAPE total anual (%)"] for r in REGRESION if r["Alcance"] == prov and r["Modelo"] == "Regresión lineal")


def f0(n):
    return f"{n:,.0f}".replace(",", ".")


def f1(n):
    return f"{n:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")


def orden(prov):
    """Orden de dibujo: la provincia elegida y Jujuy van al final para que queden por encima."""
    resto = [q for q in PROVINCIAS if q not in ("Jujuy", prov)]
    return resto + ["Jujuy"] + ([prov] if prov != "Jujuy" else [])


def grosor(q, prov):
    return 7 if q == prov else (5 if q == "Jujuy" else 3)


# =====================================================================================
# PASO 2 - Piezas reutilizables: graficos nativos de Flet, leyenda y tarjetas
# Todos los graficos pasan por estas funciones, asi tienen ejes con titulo y numeros redondos.
# =====================================================================================
def escala(valores):
    """Elige un eje con numeros redondos (por ejemplo 40, 60, 80...) que contenga todos los valores."""
    lo, hi = min(valores), max(valores)
    paso = next(s for s in (0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000) if (hi - lo) / s <= 6)
    return math.floor(lo / paso) * paso, math.ceil(hi / paso) * paso, paso


def marcas_numericas(lo, hi, paso):
    valores = [lo + i * paso for i in range(round((hi - lo) / paso) + 1)]
    return [fc.ChartAxisLabel(value=v, label=ft.Text(f1(v) if paso < 1 else f0(v), size=11, color=GRIS)) for v in valores]


def marcas_anios(desde, hasta):
    return [fc.ChartAxisLabel(value=a, label=ft.Text(str(a), size=11, color=GRIS)) for a in range(desde, hasta + 1, 2)]


def eje(titulo, etiquetas, tam):
    return fc.ChartAxis(title=ft.Text(titulo, size=12, color=GRIS), title_size=26, label_size=tam, labels=etiquetas)


def lineas(series, titulo_y, marca_x=None, alto=360):
    """Grafico de lineas. series = lista de (puntos, color, grosor, punteada). marca_x = linea vertical opcional."""
    lo, hi, paso = escala([y for s in series for _, y in s[0]])
    xs = [x for s in series for x, _ in s[0]]
    datos = [fc.LineChartData(points=[fc.LineChartDataPoint(x, y) for x, y in pts], color=c, stroke_width=g,
                              dash_pattern=[8, 6] if d else None) for pts, c, g, d in series]
    if marca_x:
        datos.append(fc.LineChartData(points=[fc.LineChartDataPoint(marca_x, lo), fc.LineChartDataPoint(marca_x, hi)],
                                      color="#9CA3AF", stroke_width=2, dash_pattern=[4, 4]))
    return fc.LineChart(
        data_series=datos, min_x=min(xs), max_x=max(xs), min_y=lo, max_y=hi, height=alto, expand=True,
        left_axis=eje(titulo_y, marcas_numericas(lo, hi, paso), 52),
        bottom_axis=eje("Año", marcas_anios(int(min(xs)), int(max(xs))), 30),
        horizontal_grid_lines=fc.ChartGridLines(interval=paso, color="#E5E7EB", width=1))


def barras(items, titulo_x, titulo_y, alto=320):
    """Grafico de barras. items = lista de (nombre, texto_del_valor, valor, color); nombre y valor van bajo cada barra."""
    lo, hi, paso = escala([0] + [v for _, _, v, _ in items])
    grupos = [fc.BarChartGroup(x=i, rods=[fc.BarChartRod(from_y=0, to_y=v, width=38, color=c, border_radius=4, tooltip=t)])
              for i, (_, t, v, c) in enumerate(items)]
    etiquetas = [fc.ChartAxisLabel(value=i, label=ft.Column(
        [ft.Text(n, size=12, weight=ft.FontWeight.W_700, color=TEXTO), ft.Text(t, size=12, color=GRIS)],
        spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER)) for i, (n, t, _, _) in enumerate(items)]
    return fc.BarChart(groups=grupos, min_y=lo, max_y=hi, height=alto, expand=True,
                       left_axis=eje(titulo_y, marcas_numericas(lo, hi, paso), 52), bottom_axis=eje(titulo_x, etiquetas, 52),
                       horizontal_grid_lines=fc.ChartGridLines(interval=paso, color="#E5E7EB", width=1))


def leyenda(items):
    """items = lista de (texto, color). Cada item ocupa solo su ancho (tight) para que queden en una fila."""
    return ft.Row([ft.Row([ft.Container(width=14, height=14, bgcolor=c, border_radius=7),
                           ft.Text(t, size=13, weight=ft.FontWeight.W_600, color=TEXTO)], spacing=6, tight=True)
                   for t, c in items], wrap=True, spacing=18, run_spacing=6)


def tarjeta(titulo, cuerpo, ayuda=None, col=None):
    hijos = [ft.Text(titulo, size=17, weight=ft.FontWeight.W_700, color=TEXTO)]
    if ayuda:
        hijos.append(ft.Text(ayuda, size=13, color=GRIS))
    return ft.Container(ft.Column(hijos + cuerpo, spacing=10), padding=20, bgcolor="white", border_radius=14,
                        border=ft.Border.all(1, "#E5E7EB"), col=col or {"xs": 12, "lg": 6})


def mensaje(texto, color):
    """Recuadro de color con la conclusion principal de cada pestaña, escrita en palabras simples."""
    return ft.Container(ft.Text(texto, size=15, weight=ft.FontWeight.W_600, color=TEXTO), padding=16, border_radius=12,
                        bgcolor=ft.Colors.with_opacity(0.10, color), border=ft.Border.all(1, color), col={"xs": 12})


def kpi(titulo, valor, detalle, color):
    return ft.Container(ft.Row([ft.Container(width=5, height=58, bgcolor=color, border_radius=3),
                                ft.Column([ft.Text(titulo, size=12, color=GRIS),
                                           ft.Text(valor, size=24, weight=ft.FontWeight.BOLD, color=TEXTO),
                                           ft.Text(detalle, size=12, color=color)], spacing=1)], spacing=12),
                        padding=16, bgcolor="white", border_radius=14, border=ft.Border.all(1, "#E5E7EB"),
                        col={"xs": 12, "sm": 6, "lg": 3})


# =====================================================================================
# PASO 3 - Pestañas (una funcion por pestaña; todas reciben la provincia elegida p)
# =====================================================================================
def vista_resumen(p):
    """Nacimientos (indice 2010 = 100) y tasa de natalidad de las 5 provincias."""
    indice, tasa = [], []
    for q in orden(p):
        base = dato(q, 2010, "NACIMIENTOS")
        indice.append(([(a, dato(q, a, "NACIMIENTOS") / base * 100) for a in ANIOS], COLOR[q], grosor(q, p), False))
        tasa.append(([(a, dato(q, a, "TASA")) for a in ANIOS], COLOR[q], grosor(q, p), False))
    indice.append(([(2010, 100), (2024, 100)], "#9CA3AF", 2, True))   # referencia: nivel de 2010
    ley_i = leyenda([(f"{q} ({100 + cambio(q):.0f})", COLOR[q]) for q in PROVINCIAS])
    ley_t = leyenda([(f"{q} ({f1(dato(q, 2024, 'TASA'))} ‰)", COLOR[q]) for q in PROVINCIAS])
    return ft.ResponsiveRow([
        tarjeta("¿Cuánto bajaron los nacimientos desde 2010?",
                [ley_i, lineas(indice, "Nacimientos (2010 = 100)")],
                "Cada línea parte de 100 en 2010. Entre paréntesis, el valor de 2024. Línea gris: nivel de 2010."),
        tarjeta("Tasa de natalidad", [ley_t, lineas(tasa, "Nacimientos por 1.000 habitantes (‰)", marca_x=2022)],
                "Línea punteada vertical: en 2022 el INDEC cambia la base de población (Censo 2022); es un cambio de serie, no una variación real."),
    ], spacing=14, run_spacing=14)


def vista_madres(p):
    """Madres menores de 20 años (2010 vs 2024, 5 provincias) y edad media de la madre."""
    grupos, etiquetas = [], []
    for i, q in enumerate(PROVINCIAS):
        a, b = dato(q, 2010, "PCT_MENOR20"), dato(q, 2024, "PCT_MENOR20")
        varillas = [fc.BarChartRod(from_y=0, to_y=a, width=26, color="#9CA3AF", border_radius=4, tooltip=f"{q} 2010: {f1(a)} %"),
                    fc.BarChartRod(from_y=0, to_y=b, width=26, color=COLOR[q], border_radius=4, tooltip=f"{q} 2024: {f1(b)} %")]
        grupos.append(fc.BarChartGroup(x=i, rods=varillas, spacing=4))
        etiquetas.append(fc.ChartAxisLabel(value=i, label=ft.Column([
            ft.Text(q, size=12, weight=ft.FontWeight.W_700, color=TEXTO),
            ft.Text(f"{f1(a)} → {f1(b)} %", size=11, color=GRIS)], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER)))
    lo, hi, paso = escala([0] + [dato(q, 2010, "PCT_MENOR20") for q in PROVINCIAS])
    barras_edad = fc.BarChart(groups=grupos, min_y=lo, max_y=hi, height=360, expand=True,
                              left_axis=eje("Madres menores de 20 años (%)", marcas_numericas(lo, hi, paso), 52),
                              bottom_axis=eje("Provincia", etiquetas, 52),
                              horizontal_grid_lines=fc.ChartGridLines(interval=paso, color="#E5E7EB", width=1))
    edad = [([(a, dato(q, a, "EDAD_MEDIA")) for a in ANIOS], COLOR[q], grosor(q, p), False) for q in orden(p)]
    ley_e = leyenda([(f"{q} ({f1(dato(q, 2024, 'EDAD_MEDIA'))})", COLOR[q]) for q in PROVINCIAS])
    return ft.ResponsiveRow([
        tarjeta("Maternidad adolescente: 2010 vs 2024",
                [leyenda([("2010 (gris)", "#9CA3AF"), ("2024 (color de cada provincia)", TEXTO)]), barras_edad],
                f"Jujuy pasó de {f1(dato('Jujuy', 2010, 'PCT_MENOR20'))} % a {f1(dato('Jujuy', 2024, 'PCT_MENOR20'))} % de madres menores de 20 años. "
                "Debajo de cada barra: valor 2010 → 2024."),
        tarjeta("Edad media de la madre", [ley_e, lineas(edad, "Edad media de la madre (años)")],
                "Sube en todas las provincias: se posterga la maternidad. Estimada con el punto medio de cada rango de edad. Entre paréntesis, 2024."),
    ], spacing=14, run_spacing=14)


def vista_proyeccion(p):
    """Proyeccion 2025-2027 (y extension orientativa a 2030) de la provincia elegida."""
    obs = [(a, dato(p, a, "NACIMIENTOS")) for a in ANIOS]
    ultimo = obs[-1]

    def serie(col):
        return [ultimo] + [(a, PRO[(p, a)][col]) for a in range(2025, 2031)]

    f27 = PRO[(p, 2027)]
    var = (f27["NACIMIENTOS_PROYECTADOS"] / ultimo[1] - 1) * 100
    resumen = mensaje(f"Se proyecta que {p} pase de {f0(ultimo[1])} nacimientos en 2024 a {f0(f27['NACIMIENTOS_PROYECTADOS'])} en 2027 "
                      f"({f1(var)} %), con un rango probable de {f0(f27['MINIMO'])} a {f0(f27['MAXIMO'])}. "
                      f"Tasa estimada 2027: {f1(f27['TASA'])} por mil habitantes. "
                      f"Confiabilidad: en la prueba con 2022-2024 este modelo se equivocó {f1(error_lineal(p))} % en el total anual.", AZUL)
    grafico = lineas([(obs, COLOR[p], 6, False), (serie("NACIMIENTOS_PROYECTADOS"), TEXTO, 5, False),
                      (serie("MINIMO"), GRIS, 3, True), (serie("MAXIMO"), GRIS, 3, True)], "Nacimientos por año", marca_x=2024)
    filas = [ft.DataRow(cells=[
        ft.DataCell(ft.Text(f"{a}" + ("*" if a > 2027 else ""))),
        ft.DataCell(ft.Text(f0(PRO[(p, a)]["NACIMIENTOS_PROYECTADOS"]), weight=ft.FontWeight.W_700)),
        ft.DataCell(ft.Text(f"{f0(PRO[(p, a)]['MINIMO'])} a {f0(PRO[(p, a)]['MAXIMO'])}")),
        ft.DataCell(ft.Text(f"{f1((PRO[(p, a)]['NACIMIENTOS_PROYECTADOS'] / ultimo[1] - 1) * 100)} %")),
        ft.DataCell(ft.Text(f1(PRO[(p, a)]["TASA"])))]) for a in range(2025, 2031)]
    tabla = ft.DataTable(columns=[ft.DataColumn(ft.Text(t, size=12)) for t in ("Año", "Nacimientos", "Rango probable", "vs 2024", "Tasa ‰")],
                         rows=filas, heading_row_height=36, data_row_min_height=34, data_row_max_height=36, column_spacing=18)
    variaciones = [(q, f"{f1((PRO[(q, 2027)]['NACIMIENTOS_PROYECTADOS'] / dato(q, 2024, 'NACIMIENTOS') - 1) * 100)} %",
                    (PRO[(q, 2027)]["NACIMIENTOS_PROYECTADOS"] / dato(q, 2024, "NACIMIENTOS") - 1) * 100, COLOR[q]) for q in PROVINCIAS]
    return ft.ResponsiveRow([
        resumen,
        tarjeta(f"{p}: nacimientos observados y proyectados",
                [leyenda([("Observado", COLOR[p]), ("Proyección central", TEXTO), ("Rango probable (mínimo y máximo)", GRIS)]), grafico],
                "Línea vertical: último año con datos (2024). El rango máximo incluye un escenario conservador de caída más lenta. "
                "2028-2030 es solo orientativo.", {"xs": 12, "lg": 7}),
        tarjeta("Valores proyectados", [tabla, ft.Text("* Extensión orientativa: la incertidumbre crece con el horizonte. "
                                                       "Tasa = nacimientos por 1.000 habitantes (población proyectada por el INDEC).", size=12, color=GRIS)],
                "Modelo: regresión lineal por perfil de madre, reentrenada con 2014-2024.", {"xs": 12, "lg": 5}),
        tarjeta("¿Y las otras provincias? Cambio proyectado 2024 → 2027", [barras(variaciones, "Provincia", "Cambio de los nacimientos (%)", 280)],
                "Permite ver si Jujuy sigue siendo la provincia donde más bajan los nacimientos.", {"xs": 12}),
    ], spacing=14, run_spacing=14)


def vista_modelos(p):
    """Resultados de los modelos explicados en lenguaje simple; los datos tecnicos quedan plegados al final."""
    corto = {"Regresión lineal": "Lineal", "Regresión polinomial (g=2)": "Polinomial", "Random Forest": "Random Forest", "Gradient Boosting": "Gradient Boosting"}
    reg = [r for r in REGRESION if r["Alcance"] == p]
    err = lambda r: r["MAPE total anual (%)"]
    mejor = min(reg, key=err)
    cumple = err(mejor) <= 10
    por_modelo = [(corto[r["Modelo"]], f"{f1(err(r))} %", err(r), "#2E8B57" if err(r) <= 10 else "#C0392B") for r in reg]
    por_prov = [(q, f"{f1(error_lineal(q))} %", error_lineal(q), COLOR[q]) for q in PROVINCIAS]
    mejor_prov = min(PROVINCIAS, key=error_lineal)

    cla = {c["Alcance"]: c for c in CLASIFICACION if c["Modelo"] == "Árbol de decisión"}
    a, b = cla["A: 4 provincias"], cla["B: Buenos Aires"]
    acierto = [("Modelo A", f"{f1(a['Accuracy'] * 100)} %", a["Accuracy"] * 100, AZUL), ("Azar A", f"{f1(a['Accuracy baseline'] * 100)} %", a["Accuracy baseline"] * 100, "#9CA3AF"),
               ("Modelo B", f"{f1(b['Accuracy'] * 100)} %", b["Accuracy"] * 100, AZUL), ("Azar B", f"{f1(b['Accuracy baseline'] * 100)} %", b["Accuracy baseline"] * 100, "#9CA3AF")]
    importancia = [(n, f"{f1(v)} %", v, AZUL if v > 50 else "#9CA3AF") for n, v in IMPORTANCIA.items()]

    # Detalle tecnico (plegado): tablas con R2, tiempo de entrenamiento y memoria
    t_reg = ft.DataTable(columns=[ft.DataColumn(ft.Text(t, size=12)) for t in ("Modelo", "Error anual", "R²", "Entrenamiento (ms)", "Memoria (MB)")],
                         rows=[ft.DataRow(cells=[ft.DataCell(ft.Text(r["Modelo"], size=12)), ft.DataCell(ft.Text(f"{f1(err(r))} %")),
                                                 ft.DataCell(ft.Text(f"{r['R2']:.2f}".replace(".", ","))), ft.DataCell(ft.Text(f1(r["Entrenamiento (ms)"]))),
                                                 ft.DataCell(ft.Text(f1(r["RAM máx (MB)"])))]) for r in reg], column_spacing=18)
    t_cla = ft.DataTable(columns=[ft.DataColumn(ft.Text(t, size=12)) for t in ("Alcance", "Algoritmo", "Acierto", "F1", "Base")],
                         rows=[ft.DataRow(cells=[ft.DataCell(ft.Text(c["Alcance"], size=12)), ft.DataCell(ft.Text(c["Modelo"], size=12)),
                                                 ft.DataCell(ft.Text(f"{f1(c['Accuracy'] * 100)} %")), ft.DataCell(ft.Text(f"{f1(c['F1 ponderado'] * 100)} %")),
                                                 ft.DataCell(ft.Text(f"{f1(c['Accuracy baseline'] * 100)} %"))]) for c in CLASIFICACION], column_spacing=18)
    glosario = ("R²: cuánto de la variación explica el modelo en cada combinación de categorías (no equivale al error anual). "
                "Entrenamiento y memoria: lo que tarda y consume cada modelo. F1: acierto balanceado entre grupos de edad. "
                "Base: acierto de un modelo que elige siempre el grupo más frecuente.")
    detalle = ft.ExpansionTile(title=ft.Text("Ver tablas con R², tiempos y memoria", size=14),
                               controls=[ft.Text(glosario, size=12, color=GRIS), ft.Row([t_reg], scroll=ft.ScrollMode.AUTO), ft.Row([t_cla], scroll=ft.ScrollMode.AUTO)])
    return ft.ResponsiveRow([
        mensaje(f"Para {p}, el mejor modelo ({mejor['Modelo'].lower()}) se equivoca solo {f1(err(mejor))} % al estimar los nacimientos de un año completo. "
                f"La meta del proyecto era menos de 10 %: {'se cumple.' if cumple else 'no se cumple.'}", "#2E8B57" if cumple else "#C0392B"),
        tarjeta(f"Error de cada modelo en {p}", [barras(por_modelo, "Modelo", "Error anual (%)")],
                "Cuanto más baja la barra, mejor. Verde: cumple la meta (menos de 10 %). Se probó con 2022-2024, años que los modelos no habían visto."),
        tarjeta("Error de la regresión lineal por provincia", [barras(por_prov, "Provincia", "Error anual (%)")],
                f"El modelo funciona mejor en {mejor_prov}. Esta comparación no depende de la provincia elegida."),
        tarjeta("¿Se puede adivinar la edad de la madre?", [barras(acierto, "Modelo", "Casos acertados (%)")],
                f"Es difícil: el modelo acierta cerca de {round(a['Accuracy'] * 10)} de cada 10 casos, contra {round(a['Accuracy baseline'] * 10)} de cada 10 de un modelo que "
                "elige siempre el grupo más frecuente. A: 4 provincias juntas. B: solo Buenos Aires (muy grande, por eso va aparte)."),
        tarjeta("¿Qué variable pesa más?", [barras(importancia, "Variable", "Importancia (%)")],
                "El nivel de instrucción concentra la mayor parte: una madre muy joven rara vez tiene estudios secundarios completos. Eso no significa que la instrucción cause la edad."),
        tarjeta("Detalle técnico (opcional)", [detalle], col={"xs": 12}),
    ], spacing=14, run_spacing=14)


# =====================================================================================
# PASO 4 - Asistente: responde con reglas (palabras clave), como ELIZA, usando los datos del tablero.
# No genera texto libre: solo plantillas con cifras reales, y si no entiende, pregunta.
# =====================================================================================
SUGERENCIAS = ["¿Cuántos nacimientos hubo en 2024?", "Maternidad adolescente", "Proyección 2027", "Comparar Jujuy con Mendoza",
               "Ranking de provincias", "¿Qué modelo funciona mejor?"]
ALIAS = {"Jujuy": ["jujuy"], "Misiones": ["misiones"], "Mendoza": ["mendoza"], "Buenos Aires": ["buenos aires", "bs as", "bsas"], "Neuquén": ["neuquen"]}


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


def responder(texto, elegida):
    """Devuelve (respuesta, opciones). Si la pregunta es ambigua o desconocida, devuelve opciones para elegir."""
    q = " " + sin_tildes(texto) + " "
    provs = provincias_en(q)
    prov = provs[0] if provs else elegida
    quien = prov if provs else f"{prov} (la provincia elegida)"
    anio = next((a for a in range(2010, 2031) if str(a) in q), None)
    tiene = lambda *claves: any(c in q for c in claves)

    if tiene(" hola", "buenas", "ayuda", "que podes", "que sabes"):
        return ("Soy el asistente de VRA Analytics. Respondo sobre natalidad en Jujuy, Misiones, Mendoza, Buenos Aires y Neuquén (2010-2024) "
                "y las proyecciones 2025-2027. Elegí una pregunta o escribí la tuya.", SUGERENCIAS)
    if tiene("compar", "versus", " vs ", "diferencia", "contra"):
        if len(provs) >= 2:
            return comparar(provs[0], provs[1]), []
        if len(provs) == 1 and provs[0] != "Jujuy":
            return comparar(provs[0], "Jujuy"), []
        return "¿Qué provincias querés comparar?", [f"Jujuy vs {o}" for o in PROVINCIAS[1:]]
    if tiene("modelo", "algoritmo", "error", "mape", "acierto", "precision"):
        r = error_lineal(prov)
        return (f"Para {quien}, la regresión lineal se equivoca {f1(r)} % en el total anual (prueba con 2022-2024). Gana porque los modelos de árbol no "
                "extrapolan tendencias. Adivinar la edad de la madre es más difícil: se acierta cerca de 3 de cada 10 casos, contra 2 de cada 10 de un modelo base."), []
    if tiene("mayor tasa", "menor tasa", "tasa mas alta", "tasa mas baja"):
        orden_t = sorted(PROVINCIAS, key=lambda x: -dato(x, 2024, "TASA"))
        return "Tasa de natalidad 2024 (de mayor a menor): " + "; ".join(f"{x} {f1(dato(x, 2024, 'TASA'))} ‰" for x in orden_t) + ".", []
    if tiene("ranking", "mayor caida", "mas cayo", "cayeron", "mayor baja"):
        orden_c = sorted(PROVINCIAS, key=cambio)
        return ("Cambio de los nacimientos 2010-2024 (de mayor a menor caída): " + "; ".join(f"{x} {f1(cambio(x))} %" for x in orden_c) +
                f". {orden_c[0]} es donde más cayeron."), []
    if tiene("mejor", "peor"):
        return "¿Mejor en qué sentido? Elegí una opción:", ["Mayor caída de nacimientos", "Mayor tasa de natalidad", "¿Qué modelo funciona mejor?"]
    if tiene("proyec", "predic", "futuro", "2025", "2026", "2027", "2028", "2029", "2030"):
        a = anio if anio and anio >= 2025 else 2027
        f = PRO[(prov, a)]
        nota = " (extensión orientativa: más incertidumbre)" if a > 2027 else ""
        return (f"{quien}, {a}{nota}: se proyectan {f0(f['NACIMIENTOS_PROYECTADOS'])} nacimientos (rango {f0(f['MINIMO'])} a {f0(f['MAXIMO'])}), "
                f"con una tasa de {f1(f['TASA'])} por mil habitantes."), []
    if tiene("adolesc", "menor de 20", "menores de 20", "madres jovenes"):
        return (f"En {quien}, las madres menores de 20 años pasaron de {f1(dato(prov, 2010, 'PCT_MENOR20'))} % de los nacimientos en 2010 "
                f"a {f1(dato(prov, 2024, 'PCT_MENOR20'))} % en 2024."), []
    if tiene("edad"):
        return (f"La edad media de las madres en {quien} subió de {f1(dato(prov, 2010, 'EDAD_MEDIA'))} años (2010) a "
                f"{f1(dato(prov, 2024, 'EDAD_MEDIA'))} años (2024): se posterga la maternidad."), []
    if tiene("instruccion", "educacion", "secundaria", "estudio"):
        return ("En el modelo que predice el grupo de edad de la madre, el nivel de instrucción es la variable que más pesa "
                f"(cerca del {f0(IMPORTANCIA['Nivel de instrucción'])} %): una madre muy joven rara vez tiene secundaria completa."), []
    if tiene("pearson", "correlacion"):
        return ("En Jujuy, la correlación de Pearson entre el año y los nacimientos es -0,94 (caída muy marcada); con el porcentaje de madres menores de 20 "
                "es -0,93 y con la edad media +0,93. Pearson mide asociación lineal, no prueba causalidad."), []
    if tiene("2022", "serie", "indec", "censo"):
        return ("En 2022 el INDEC cambió la base de población (de Censo 2010 a Censo 2022), por eso la población tiene un salto ese año. "
                "Es un cambio de serie, no una variación real: solo se explica, no se corrige."), []
    if tiene("tasa"):
        a = anio if anio and anio <= 2024 else 2024
        return f"La tasa de natalidad de {quien} en {a} fue {f1(dato(prov, a, 'TASA'))} por mil habitantes (en 2010: {f1(dato(prov, 2010, 'TASA'))}).", []
    if tiene("nacimiento", "nacieron", "nacidos", "cuantos", "natalidad"):
        a = anio if anio and anio <= 2024 else 2024
        return f"En {quien} hubo {f0(dato(prov, a, 'NACIMIENTOS'))} nacimientos en {a} (en 2010: {f0(dato(prov, 2010, 'NACIMIENTOS'))}).", []
    return ("No encontré eso en los datos. Solo puedo hablar de natalidad en Jujuy, Misiones, Mendoza, Buenos Aires y Neuquén (2010-2024) "
            "y de las proyecciones 2025-2027. Probá con alguna de estas preguntas:"), SUGERENCIAS


def crear_asistente(page, provincia_actual):
    """Arma la tarjeta del chat. provincia_actual() devuelve la provincia elegida en la lista."""
    mensajes = ft.ListView(spacing=10, height=380, auto_scroll=True)
    entrada = ft.TextField(hint_text="Escribí tu pregunta…", expand=True, border_radius=10, border_color="#9CA3AF", dense=True)

    def burbuja(texto, mio):
        return ft.Row([ft.Container(ft.Text(texto, size=14, color="white" if mio else TEXTO, selectable=True),
                                    padding=ft.Padding.symmetric(horizontal=14, vertical=10), bgcolor=AZUL if mio else "#EEF2F7",
                                    border_radius=14, max_width=640)],
                      alignment=ft.MainAxisAlignment.END if mio else ft.MainAxisAlignment.START)

    def botones(opciones):
        return ft.Row([ft.OutlinedButton(content=ft.Text(o), on_click=lambda e, o=o: enviar(o)) for o in opciones], wrap=True, spacing=8, run_spacing=6)

    def enviar(texto=None):
        texto = (texto or entrada.value or "").strip()
        if not texto:
            return
        respuesta, opciones = responder(texto, provincia_actual())
        mensajes.controls.append(burbuja(texto, True))
        mensajes.controls.append(burbuja(respuesta, False))
        if opciones:
            mensajes.controls.append(botones(opciones))
        entrada.value = ""
        page.update()

    def borrar(e):
        del mensajes.controls[1:]
        page.update()

    mensajes.controls.append(burbuja("Hola, soy el asistente de VRA Analytics. Preguntame sobre nacimientos, tasa, maternidad adolescente, "
                                     "proyecciones, comparaciones entre provincias o modelos.", False))
    entrada.on_submit = lambda e: enviar()
    cuerpo = [botones(SUGERENCIAS), mensajes,
              ft.Row([entrada, ft.IconButton(ft.Icons.SEND, icon_color=AZUL, tooltip="Enviar", on_click=lambda e: enviar()),
                      ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=GRIS, tooltip="Borrar conversación", on_click=borrar)])]
    return ft.ResponsiveRow([tarjeta("Asistente VRA", cuerpo, "Responde con cifras reales de este tablero. Si no entiende la pregunta, te ofrece opciones.", {"xs": 12})])


# =====================================================================================
# PASO 5 - Pantalla principal: encabezado, selector de provincia, tarjetas y pestañas
# Al cambiar la provincia o la pestaña se vuelve a dibujar solo lo que corresponde.
# =====================================================================================
def main(page: ft.Page):
    page.title = "VRA Analytics | Natalidad en Jujuy"
    page.bgcolor = "#F3F4F6"
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO
    estado = {"prov": "Jujuy"}

    # Encabezado: logo con las iniciales del grupo, nombre, apellidos y selector de provincia
    logo = ft.Container(ft.Row([ft.Text("V", size=20, weight=ft.FontWeight.W_900, color="white"),
                                ft.Text("R", size=20, weight=ft.FontWeight.W_900, color="#7FB3E6"),
                                ft.Text("A", size=20, weight=ft.FontWeight.W_900, color="white")], spacing=0, tight=True),
                        width=58, height=58, border_radius=12, alignment=ft.Alignment(0, 0), border=ft.Border.all(2, "#7FB3E6"),
                        gradient=ft.LinearGradient(begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1), colors=["#0B2A4A", "#1F4E79"]))
    subtitulo = ft.Text("Jujuy · NOA", size=13, weight=ft.FontWeight.W_600, color="#BFD7F0")
    selector = ft.Dropdown(value="Jujuy", label="Provincia", width=260, options=[ft.DropdownOption(key=p, text=p) for p in PROVINCIAS],
                           filled=True, fill_color="white", color=AZUL, text_size=16, border_color="#7FB3E6", border_width=2,
                           label_style=ft.TextStyle(color=AZUL, weight=ft.FontWeight.W_700), on_select=lambda e: cambiar_provincia())
    encabezado = ft.Container(ft.ResponsiveRow([
        ft.Container(ft.Row([logo, ft.Column([ft.Text("VRA Analytics", size=26, weight=ft.FontWeight.W_800, color="white"),
                                              ft.Text("Natalidad en Jujuy en el contexto nacional · 2010-2024", size=13, color="#BFD7F0"),
                                              ft.Text("Gutierres · Suares · Valerio", size=11, color="#9FC3E8")], spacing=0)], spacing=14),
                     col={"xs": 12, "md": 8}),
        ft.Container(ft.Column([ft.Text("Elegí una provincia ▼", size=12, color="#BFD7F0"),
                                ft.Container(selector, bgcolor="white", border_radius=10), subtitulo],
                               horizontal_alignment=ft.CrossAxisAlignment.END, spacing=4), col={"xs": 12, "md": 4}, alignment=ft.Alignment(1, 0)),
    ], run_spacing=10), padding=ft.Padding.symmetric(horizontal=26, vertical=18),
        gradient=ft.LinearGradient(begin=ft.Alignment(-1, 0), end=ft.Alignment(1, 0), colors=["#0B2A4A", "#1F4E79"]))

    kpis = ft.ResponsiveRow(spacing=14, run_spacing=14)
    cuerpo = ft.Container(padding=ft.Padding.only(top=14))
    asistente = crear_asistente(page, lambda: estado["prov"])
    VISTAS = [vista_resumen, vista_madres, vista_proyeccion, vista_modelos, lambda p: asistente]
    tabs = ft.Tabs(length=5, selected_index=0, on_change=lambda e: dibujar(),
                   content=ft.TabBar(tabs=[ft.Tab(label=n) for n in ("Resumen", "Madres", "Proyección", "Modelos", "Asistente")]))

    def dibujar():
        """Redibuja las tarjetas de arriba y la pestaña activa para la provincia elegida."""
        p = estado["prov"]
        var = cambio(p)
        f27 = PRO[(p, 2027)]
        kpis.controls = [
            kpi("Nacimientos 2024", f0(dato(p, 2024, "NACIMIENTOS")), f"{f1(var)} % vs 2010 ({f0(dato(p, 2010, 'NACIMIENTOS'))})", "#C0392B"),
            kpi("Tasa de natalidad 2024", f"{f1(dato(p, 2024, 'TASA'))} ‰", f"2010: {f1(dato(p, 2010, 'TASA'))} ‰", COLOR[p]),
            kpi("Madres menores de 20", f"{f1(dato(p, 2024, 'PCT_MENOR20'))} %", f"2010: {f1(dato(p, 2010, 'PCT_MENOR20'))} %", "#2E8B57"),
            kpi("Proyección 2027", f0(f27["NACIMIENTOS_PROYECTADOS"]), f"Rango {f0(f27['MINIMO'])} a {f0(f27['MAXIMO'])}", "#7C3AED"),
        ]
        subtitulo.value = f"{p} · {REGION[p]}" + ("" if p == "Jujuy" else "  (se compara con Jujuy)")
        cuerpo.content = VISTAS[tabs.selected_index](p)
        page.update()

    def cambiar_provincia():
        estado["prov"] = selector.value
        dibujar()

    pie = ft.Container(ft.Text("VRA Analytics · Gutierres · Suares · Valerio · Fuentes: DEIS (nacidos vivos) e INDEC (proyecciones de población)",
                               size=11, color=GRIS, text_align=ft.TextAlign.CENTER), padding=14, alignment=ft.Alignment(0, 0))
    page.add(encabezado, ft.Container(ft.Column([kpis, tabs, cuerpo], spacing=14), padding=ft.Padding.symmetric(horizontal=26, vertical=18)), pie)
    dibujar()


# Se ejecuta al abrir el archivo. En GitHub Pages (navegador, "emscripten") y en escritorio se abre tal cual;
# en tu computadora, por defecto, se abre en el navegador.
if sys.platform == "emscripten" or "--escritorio" in sys.argv:
    ft.run(main)
else:
    ft.run(main, view=ft.AppView.WEB_BROWSER)
