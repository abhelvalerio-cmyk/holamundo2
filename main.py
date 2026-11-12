"""
VRA Analytics - Natalidad en Jujuy en el contexto nacional (2010-2024, proyeccion 2025-2027)
Proyecto Integrador (Programacion II + Ciencia de Datos)
Autores: Gutierres Victoria, Suares Romina, Valerio Abel

Ejecutar:   python app.py               (abre en el navegador)
            python app.py --escritorio  (ventana de escritorio)
Requisitos: pip install -r requirements.txt     (flet, flet-charts, pandas)
Datos:      carpeta datos/ (se genera con: python preparar_datos.py)

Los graficos son nativos de Flet (flet-charts). El asistente funciona sin internet:
responde con reglas sobre los mismos datos que muestra el tablero.
"""
import os
import unicodedata

import flet as ft
import flet_charts as fc
import pandas as pd

# ------------------------------------------------------------------ datos
AQUI = os.path.dirname(os.path.abspath(__file__))
CARPETAS = [os.path.join(AQUI, "datos"), os.path.join(AQUI, "..", "DATOS", "PROCESADOS")]


def cargar(nombre):
    """Busca el archivo primero en SCRIP-WEB/datos y despues en DATOS/PROCESADOS."""
    for carpeta in CARPETAS:
        ruta = os.path.join(carpeta, nombre)
        if os.path.exists(ruta):
            return pd.read_csv(ruta)
    raise FileNotFoundError(f"No se encontro {nombre}. Ejecuta: python preparar_datos.py")


try:
    IND = cargar("indicadores.csv")
    DIST = cargar("distribucion_edad.csv")
    PROY = cargar("proyecciones.csv")
    MOD = cargar("modelos.csv")
    DATOS_OK, ERROR_DATOS = True, ""
except FileNotFoundError as error:
    DATOS_OK, ERROR_DATOS = False, str(error)

PROVINCIAS = ["Jujuy", "Misiones", "Mendoza", "Buenos Aires", "Neuquén"]
REGION = {"Jujuy": "NOA", "Misiones": "NEA", "Mendoza": "Cuyo", "Buenos Aires": "Pampeana", "Neuquén": "Patagonia"}
COLOR = {"Jujuy": "#1F4E79", "Misiones": "#E69F00", "Mendoza": "#009E73", "Buenos Aires": "#CC79A7", "Neuquén": "#56B4E9"}
AZUL, ROJO, VERDE, GRIS = "#1F4E79", "#C0392B", "#2E8B57", "#6B7280"
GRUPOS = ["Menor de 20", "20-24", "25-29", "30-34", "35 o mas"]


def sin_tildes(texto):
    return "".join(c for c in unicodedata.normalize("NFD", str(texto).lower()) if unicodedata.category(c) != "Mn")


def f0(n):
    return f"{n:,.0f}".replace(",", ".")


def f1(n):
    return f"{n:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")


def valor(prov, anio, col):
    return float(IND[(IND.PROVINCIA == prov) & (IND.ANIO == anio)][col].iloc[0])


def proyeccion(prov, anio):
    fila = PROY[(PROY.PROVINCIA == prov) & (PROY.ANIO == anio)].iloc[0]
    return fila


# ------------------------------------------------------------------ graficos nativos
def ticks(minimo, maximo, n=5):
    paso = (maximo - minimo) / (n - 1)
    return [minimo + i * paso for i in range(n)]


def eje_x(anios, cada=2):
    return fc.ChartAxis(
        label_size=28,
        labels=[fc.ChartAxisLabel(value=a, label=ft.Text(str(a), size=10, color=GRIS)) for a in anios if (a - anios[0]) % cada == 0],
    )


def eje_y(minimo, maximo, formato):
    return fc.ChartAxis(
        label_size=52,
        labels=[fc.ChartAxisLabel(value=v, label=ft.Text(formato(v), size=10, color=GRIS)) for v in ticks(minimo, maximo)],
    )


def linea(puntos, color, grosor=2, punteada=False, curva=False, puntos_visibles=False):
    return fc.LineChartData(
        points=[fc.LineChartDataPoint(x, y) for x, y in puntos],
        color=color, stroke_width=grosor, curved=curva,
        dash_pattern=[6, 5] if punteada else None,
        point=puntos_visibles,
    )


def grafico_lineas(series, anios, formato, titulo_y=None, altura=330):
    """series: lista de (puntos, color, grosor, punteada). Ejes calculados automaticamente."""
    ys = [y for s in series for _, y in s[0]]
    lo, hi = min(ys), max(ys)
    margen = (hi - lo) * 0.08 or 1
    lo, hi = lo - margen, hi + margen
    return fc.LineChart(
        data_series=[linea(p, c, g, d) for p, c, g, d in series],
        min_x=anios[0], max_x=anios[-1], min_y=lo, max_y=hi, height=altura, expand=True,
        left_axis=eje_y(lo, hi, formato), bottom_axis=eje_x(anios),
        horizontal_grid_lines=fc.ChartGridLines(color="#E5E7EB", width=1),
        tooltip=fc.LineChartTooltip(bgcolor="#111827"),
    )


def leyenda(items):
    return ft.Row(
        [ft.Row([ft.Container(width=12, height=12, bgcolor=c, border_radius=6), ft.Text(n, size=12, color=GRIS)], spacing=5)
         for n, c in items], wrap=True, spacing=14,
    )


def tarjeta(titulo, contenido, subtitulo=None, columnas=None):
    cuerpo = [ft.Text(titulo, size=15, weight=ft.FontWeight.W_600, color="#111827")]
    if subtitulo:
        cuerpo.append(ft.Text(subtitulo, size=12, color=GRIS))
    cuerpo.append(contenido)
    return ft.Container(
        content=ft.Column(cuerpo, spacing=8), padding=18, bgcolor="white", border_radius=14,
        border=ft.Border.all(1, "#E5E7EB"), col=columnas or {"xs": 12},
    )


def kpi(titulo, principal, detalle, color=AZUL, icono=ft.Icons.INSIGHTS):
    return ft.Container(
        content=ft.Row([
            ft.Container(ft.Icon(icono, color=color, size=22), width=42, height=42, border_radius=10,
                         bgcolor=ft.Colors.with_opacity(0.10, color), alignment=ft.Alignment(0, 0)),
            ft.Column([ft.Text(titulo, size=12, color=GRIS), ft.Text(principal, size=24, weight=ft.FontWeight.BOLD, color="#111827"),
                       ft.Text(detalle, size=11, color=color)], spacing=1, expand=True),
        ], spacing=12),
        padding=16, bgcolor="white", border_radius=14, border=ft.Border.all(1, "#E5E7EB"),
        col={"xs": 12, "sm": 6, "lg": 3},
    )


# ------------------------------------------------------------------ asistente (reglas, sin internet)
def responder(pregunta, provincia):
    """Asistente offline: detecta la provincia y el tema en el texto y responde con los datos del tablero."""
    q = sin_tildes(pregunta)
    prov = next((p for p in PROVINCIAS if sin_tildes(p) in q), provincia)
    if "buenos aires" in q or "bs as" in q or "bsas" in q:
        prov = "Buenos Aires"
    anio = next((a for a in range(2010, 2031) if str(a) in q), None)

    def tiene(*claves):
        return any(c in q for c in claves)

    if tiene("hola", "buenas", "ayuda", "que podes", "que sabes", "como funciona"):
        return ("Soy el asistente de VRA Analytics. Respondo sobre natalidad en Jujuy, Misiones, Mendoza, Buenos Aires y Neuquen "
                "(2010-2024) y las proyecciones 2025-2027. Probá con: 'cuantos nacimientos hubo en Jujuy en 2024', "
                "'tasa de natalidad', 'maternidad adolescente', 'proyeccion 2027', 'ranking' o 'que modelo funciona mejor'.")
    if tiene("proyec", "predic", "futuro", "2025", "2026", "2027", "2028", "2029", "2030"):
        a = anio if anio and anio >= 2025 else 2027
        f = proyeccion(prov, a)
        extra = " (extension orientativa: la incertidumbre es mayor)" if a > 2027 else ""
        return (f"{prov}, {a}{extra}: se proyectan {f0(f.NACIMIENTOS_PROYECTADOS)} nacimientos (rango {f0(f.MINIMO)} a {f0(f.MAXIMO)}), "
                f"o sea una tasa de {f1(f.TASA)} por mil habitantes (rango {f1(f.TASA_MIN)} a {f1(f.TASA_MAX)}). "
                f"En un escenario conservador serian {f0(f.ESCENARIO_CONSERVADOR)}.")
    if tiene("adolesc", "menor de 20", "menores de 20", "jovenes", "madres jovenes"):
        a, b = valor(prov, 2010, "PCT_MENOR20"), valor(prov, 2024, "PCT_MENOR20")
        return (f"En {prov}, las madres menores de 20 años pasaron de {f1(a)} % de los nacimientos en 2010 a {f1(b)} % en 2024 "
                f"({f1(b - a)} puntos porcentuales).")
    if tiene("edad media", "edad promedio", "edad de la madre", "edad"):
        a, b = valor(prov, 2010, "EDAD_MEDIA"), valor(prov, 2024, "EDAD_MEDIA")
        return f"La edad media de las madres en {prov} subio de {f1(a)} años (2010) a {f1(b)} años (2024): la maternidad se esta postergando."
    if tiene("instruccion", "educacion", "secundaria", "estudio"):
        a, b = valor(prov, 2010, "PCT_SECUNDARIA_COMPLETA"), valor(prov, 2024, "PCT_SECUNDARIA_COMPLETA")
        return (f"En {prov}, las madres con secundaria completa o mas pasaron de {f1(a)} % (2010) a {f1(b)} % (2024). "
                "En el modelo de clasificacion, el nivel de instruccion es la variable que mas pesa para predecir el grupo de edad (cerca del 76 %).")
    if tiene("tasa"):
        a = anio if anio and anio <= 2024 else 2024
        return (f"La tasa de natalidad de {prov} en {a} fue {f1(valor(prov, a, 'TASA'))} por mil habitantes "
                f"(en 2010 era {f1(valor(prov, 2010, 'TASA'))}).")
    if tiene("ranking", "comparar", "comparacion", "mayor caida", "mas cayo", "cual cayo"):
        v = {p: (valor(p, 2024, "NACIMIENTOS") / valor(p, 2010, "NACIMIENTOS") - 1) * 100 for p in PROVINCIAS}
        orden = sorted(v.items(), key=lambda kv: kv[1])
        lista = "; ".join(f"{p} {f1(x)} %" for p, x in orden)
        return f"Variacion de nacimientos 2010-2024 (de mayor a menor caida): {lista}. Jujuy es la provincia donde mas cayeron."
    if tiene("modelo", "algoritmo", "error", "mape", "precision", "accuracy", "mejor"):
        r = MOD[(MOD.Tarea == "Regresión: nacimientos") & (MOD.Alcance == prov) & (MOD.Modelo == "Regresión lineal")]
        txt = ""
        if len(r):
            txt = f"Para {prov}, la regresion lineal erra {f1(r['MAPE total anual (%)'].iloc[0])} % en el total anual (prueba 2022-2024). "
        return (txt + "La regresion lineal gano en nacimientos anuales porque los modelos de arbol no extrapolan tendencias. "
                "En clasificacion de edad el acierto es de 27-29 %, apenas sobre el 23 % del modelo base.")
    if tiene("pearson", "correlacion"):
        return ("En Jujuy, la correlacion de Pearson entre año y nacimientos es -0,94 (caida muy marcada), entre año y % de madres menores de 20 es -0,93, "
                "y entre año y edad media es +0,93. Pearson mide asociacion lineal; no prueba causalidad.")
    if tiene("2022", "serie", "indec", "censo"):
        return ("En 2022 el INDEC cambio de base poblacional (Censo 2010 a Censo 2022). Por eso la poblacion tiene un salto ese año "
                "(Jujuy +2,07 %). Es un cambio de serie, no una variacion real: solo se explica, no se corrige.")
    if tiene("nacimiento", "nacieron", "nacidos", "cuantos", "natalidad"):
        a = anio if anio and anio <= 2024 else 2024
        n = valor(prov, a, "NACIMIENTOS")
        return f"En {prov} hubo {f0(n)} nacimientos en {a} (en 2010 fueron {f0(valor(prov, 2010, 'NACIMIENTOS'))})."
    return ("No entendi bien la consulta. Puedo responder sobre nacimientos, tasa de natalidad, maternidad adolescente, edad media, "
            "instruccion, proyecciones 2025-2027, ranking entre provincias y modelos. Mencioná una provincia si queres otra distinta a la elegida.")


# ------------------------------------------------------------------ app
def main(page: ft.Page):
    page.title = "VRA Analytics | Natalidad en Jujuy"
    page.bgcolor = "#F3F4F6"
    page.padding = 0
    page.theme = ft.Theme(color_scheme_seed=AZUL)
    page.scroll = ft.ScrollMode.AUTO

    logo = ft.Container(
        content=ft.Row([ft.Text("V", size=19, weight=ft.FontWeight.W_900, color="white"),
                        ft.Text("R", size=19, weight=ft.FontWeight.W_900, color="#7FB3E6"),
                        ft.Text("A", size=19, weight=ft.FontWeight.W_900, color="white")], spacing=0, tight=True),
        width=54, height=54, border_radius=12, alignment=ft.Alignment(0, 0),
        gradient=ft.LinearGradient(begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1), colors=["#0B2A4A", "#1F4E79"]),
        border=ft.Border.all(2, "#7FB3E6"),
    )

    if not DATOS_OK:
        page.add(ft.Container(ft.Column([logo, ft.Text("No se encontraron los datos", size=20, weight=ft.FontWeight.BOLD),
                                         ft.Text(ERROR_DATOS), ft.Text("Ejecutá primero el notebook y luego: python preparar_datos.py")]),
                              padding=30))
        return

    estado = {"prov": "Jujuy"}
    contenido = ft.Column(spacing=16)
    kpis = ft.ResponsiveRow(spacing=14, run_spacing=14)

    # ---------------- vistas ----------------
    def vista_resumen(p):
        anios = list(range(2010, 2025))
        indice = []
        tasas = []
        for q in PROVINCIAS:
            d = IND[IND.PROVINCIA == q].sort_values("ANIO")
            base = d.NACIMIENTOS.iloc[0]
            g = 3.6 if q == p else (2.8 if q == "Jujuy" else 1.4)
            indice.append(([(a, n / base * 100) for a, n in zip(d.ANIO, d.NACIMIENTOS)], COLOR[q], g, False))
            tasas.append(([(a, t) for a, t in zip(d.ANIO, d.TASA)], COLOR[q], g, False))
        ley = leyenda([(q, COLOR[q]) for q in PROVINCIAS])
        return ft.ResponsiveRow([
            tarjeta("Evolución de los nacimientos (índice 2010 = 100)", ft.Column([ley, grafico_lineas(indice, anios, lambda v: f"{v:.0f}")]),
                    "La provincia elegida y Jujuy se dibujan más gruesas.", {"xs": 12, "lg": 6}),
            tarjeta("Tasa de natalidad (por 1.000 habitantes)", ft.Column([ley, grafico_lineas(tasas, anios, lambda v: f"{v:.0f}")]),
                    "Nacimientos / población × 1.000. Desde 2022 la población usa la base del Censo 2022.", {"xs": 12, "lg": 6}),
        ], spacing=14, run_spacing=14)

    def vista_madres(p):
        anios = list(range(2010, 2025))
        series_edad = []
        for q in PROVINCIAS:
            d = IND[IND.PROVINCIA == q].sort_values("ANIO")
            g = 3.6 if q == p else (2.8 if q == "Jujuy" else 1.4)
            series_edad.append(([(a, e) for a, e in zip(d.ANIO, d.EDAD_MEDIA)], COLOR[q], g, False))

        # barras: % por grupo de edad, 2010 vs 2024, provincia elegida
        def barras(prov):
            grupos = []
            for i, g in enumerate(GRUPOS):
                rods = []
                for anio, col in ((2010, "#9CA3AF"), (2024, COLOR[prov])):
                    f = DIST[(DIST.PROVINCIA == prov) & (DIST.ANIO == anio) & (DIST.GRUPO == g)]
                    v = float(f.PCT.iloc[0]) if len(f) else 0
                    rods.append(fc.BarChartRod(from_y=0, to_y=v, width=22, color=col, border_radius=4,
                                               tooltip=f"{anio}: {v:.1f} %"))
                grupos.append(fc.BarChartGroup(x=i, rods=rods, spacing=4))
            return fc.BarChart(
                groups=grupos, height=330, expand=True, min_y=0, max_y=40,
                left_axis=fc.ChartAxis(label_size=44, labels=[fc.ChartAxisLabel(value=v, label=ft.Text(f"{v} %", size=10, color=GRIS)) for v in (0, 10, 20, 30, 40)]),
                bottom_axis=fc.ChartAxis(label_size=28, labels=[fc.ChartAxisLabel(value=i, label=ft.Text(g.replace("mas", "más"), size=10, color=GRIS)) for i, g in enumerate(GRUPOS)]),
                horizontal_grid_lines=fc.ChartGridLines(color="#E5E7EB", width=1),
            )
        a, b = valor(p, 2010, "PCT_MENOR20"), valor(p, 2024, "PCT_MENOR20")
        return ft.ResponsiveRow([
            tarjeta(f"{p}: edad de la madre, 2010 vs 2024", ft.Column([leyenda([("2010", "#9CA3AF"), ("2024", COLOR[p])]), barras(p)]),
                    f"Madres menores de 20 años: {f1(a)} % en 2010 → {f1(b)} % en 2024.", {"xs": 12, "lg": 6}),
            tarjeta("Edad media de la madre (años)", ft.Column([leyenda([(q, COLOR[q]) for q in PROVINCIAS]), grafico_lineas(series_edad, anios, lambda v: f"{v:.1f}")]),
                    "Estimada con el punto medio de cada rango de edad. Sube en todas las provincias.", {"xs": 12, "lg": 6}),
        ], spacing=14, run_spacing=14)

    def vista_proyeccion(p):
        d = IND[IND.PROVINCIA == p].sort_values("ANIO")
        pr = PROY[(PROY.PROVINCIA == p)].sort_values("ANIO")
        obs = [(a, n) for a, n in zip(d.ANIO, d.NACIMIENTOS)]
        ult = obs[-1]
        anios = list(range(2010, 2031))
        central = [ult] + [(a, n) for a, n in zip(pr.ANIO, pr.NACIMIENTOS_PROYECTADOS)]
        minimo = [ult] + [(a, n) for a, n in zip(pr.ANIO, pr.MINIMO)]
        maximo = [ult] + [(a, n) for a, n in zip(pr.ANIO, pr.MAXIMO)]
        cons = [ult] + [(a, n) for a, n in zip(pr.ANIO, pr.ESCENARIO_CONSERVADOR)]
        grafico = grafico_lineas([(obs, COLOR[p], 3.4, False), (central, ROJO, 3, False), (minimo, "#93C5FD", 1.6, True),
                                  (maximo, "#93C5FD", 1.6, True), (cons, "#D97706", 1.8, True)], anios, lambda v: f0(v))
        filas = []
        for _, f in pr.iterrows():
            orient = int(f.ANIO) > 2027
            filas.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(f"{int(f.ANIO)}" + ("*" if orient else ""))),
                ft.DataCell(ft.Text(f0(f.NACIMIENTOS_PROYECTADOS), weight=ft.FontWeight.W_600)),
                ft.DataCell(ft.Text(f"{f0(f.MINIMO)} - {f0(f.MAXIMO)}")),
                ft.DataCell(ft.Text(f0(f.ESCENARIO_CONSERVADOR))),
                ft.DataCell(ft.Text(f1(f.TASA))),
            ]))
        tabla = ft.DataTable(
            columns=[ft.DataColumn(ft.Text(t, size=12)) for t in ("Año", "Nacimientos", "Rango 95 %", "Conservador", "Tasa ‰")],
            rows=filas, heading_row_height=36, data_row_min_height=34, data_row_max_height=36, column_spacing=22,
        )
        return ft.ResponsiveRow([
            tarjeta(f"{p}: nacimientos observados y proyectados",
                    ft.Column([leyenda([("Observado", COLOR[p]), ("Proyección central", ROJO), ("Rango 95 %", "#93C5FD"), ("Escenario conservador", "#D97706")]), grafico]),
                    "Proyección principal 2025-2027. 2028-2030 es una extensión orientativa.", {"xs": 12, "lg": 7}),
            tarjeta("Valores proyectados", ft.Column([tabla, ft.Text("* Extensión orientativa: la incertidumbre crece con el horizonte.", size=11, color=GRIS)]),
                    "Modelo: regresión lineal por perfil de madre, reentrenada con 2014-2024.", {"xs": 12, "lg": 5}),
        ], spacing=14, run_spacing=14)

    def vista_modelos(p):
        reg = MOD[(MOD.Tarea == "Regresión: nacimientos") & (MOD.Alcance == p)]
        filas = [ft.DataRow(cells=[
            ft.DataCell(ft.Text(r.Modelo, size=12, weight=ft.FontWeight.W_600 if r["MAPE total anual (%)"] == reg["MAPE total anual (%)"].min() else None)),
            ft.DataCell(ft.Text(f1(r["MAPE total anual (%)"]) + " %")),
            ft.DataCell(ft.Text(f1(r.R2 * 100) if False else f"{r.R2:.2f}".replace(".", ","))),
            ft.DataCell(ft.Text(f1(r["Entrenamiento (ms)"]))),
            ft.DataCell(ft.Text(f1(r["RAM máx (MB)"]))),
        ]) for _, r in reg.iterrows()]
        tabla_reg = ft.DataTable(columns=[ft.DataColumn(ft.Text(t, size=12)) for t in ("Modelo", "Error anual", "R²", "Entren. ms", "RAM MB")],
                                 rows=filas, heading_row_height=36, data_row_min_height=34, data_row_max_height=38, column_spacing=18)
        cla = MOD[MOD.Tarea == "Clasificación: grupo etario"]
        filas_c = [ft.DataRow(cells=[
            ft.DataCell(ft.Text(r.Alcance, size=12)), ft.DataCell(ft.Text(r.Modelo, size=12)),
            ft.DataCell(ft.Text(f"{r.Accuracy * 100:.1f} %".replace(".", ","))),
            ft.DataCell(ft.Text(f"{r['F1 ponderado'] * 100:.1f} %".replace(".", ","))),
            ft.DataCell(ft.Text(f"{r['Accuracy baseline'] * 100:.0f} %")),
        ]) for _, r in cla.iterrows()]
        tabla_cla = ft.DataTable(columns=[ft.DataColumn(ft.Text(t, size=12)) for t in ("Modelo", "Algoritmo", "Accuracy", "F1", "Base")],
                                 rows=filas_c, heading_row_height=36, data_row_min_height=34, data_row_max_height=38, column_spacing=16)
        return ft.ResponsiveRow([
            tarjeta(f"Regresión de nacimientos: {p}", ft.Column([tabla_reg, ft.Text("Prueba con datos 2022-2024 que los modelos no vieron. Objetivo propuesto: error anual ≤ 10 %.", size=11, color=GRIS)]),
                    "Gana la regresión lineal: los árboles no extrapolan la tendencia.", {"xs": 12, "lg": 6}),
            tarjeta("Clasificación del grupo de edad de la madre", ft.Column([tabla_cla, ft.Text("Base = acertar siempre la clase más frecuente (≈ 22-23 %). El nivel de instrucción pesa ≈ 76 % en el modelo.", size=11, color=GRIS)]),
                    "Supera al modelo base, pero por poco: sirve más para interpretar que para predecir.", {"xs": 12, "lg": 6}),
        ], spacing=14, run_spacing=14)

    # ---------------- asistente ----------------
    mensajes = ft.ListView(spacing=8, height=330, auto_scroll=True)
    entrada = ft.TextField(hint_text="Escribí tu consulta…", expand=True, border_radius=10, dense=True)

    def burbuja(texto, mio):
        return ft.Row([ft.Container(ft.Text(texto, size=13, color="white" if mio else "#111827", selectable=True), padding=ft.Padding.symmetric(horizontal=14, vertical=9),
                                    bgcolor=AZUL if mio else "#EEF2F7", border_radius=14, width=None, expand=False)],
                      alignment=ft.MainAxisAlignment.END if mio else ft.MainAxisAlignment.START)

    def enviar(texto=None):
        texto = (texto or entrada.value or "").strip()
        if not texto:
            return
        mensajes.controls.append(burbuja(texto, True))
        mensajes.controls.append(burbuja(responder(texto, estado["prov"]), False))
        entrada.value = ""
        page.update()

    mensajes.controls.append(burbuja("Hola, soy el asistente de VRA Analytics. Preguntame por nacimientos, tasa, maternidad adolescente, proyecciones o modelos.", False))
    sugerencias = ft.Row([ft.OutlinedButton(t, on_click=lambda e, t=t: enviar(t)) for t in
                          ("¿Cuántos nacimientos hubo en 2024?", "Tasa de natalidad", "Maternidad adolescente", "Proyección 2027", "Ranking de provincias", "¿Qué modelo funciona mejor?")],
                         wrap=True, spacing=8, run_spacing=6)
    entrada.on_submit = lambda e: enviar()
    vista_chat = ft.ResponsiveRow([tarjeta("Asistente VRA", ft.Column([sugerencias, mensajes, ft.Row([entrada, ft.IconButton(ft.Icons.SEND, icon_color=AZUL, on_click=lambda e: enviar())])]),
                                           "Funciona sin internet: responde con reglas sobre los datos del tablero.", {"xs": 12, "lg": 9})])

    # ---------------- armado ----------------
    VISTAS = [("Resumen", vista_resumen), ("Madres", vista_madres), ("Proyección", vista_proyeccion), ("Modelos", vista_modelos)]
    paneles = [ft.Container(padding=ft.Padding.only(top=14)) for _ in VISTAS]
    panel_chat = ft.Container(vista_chat, padding=ft.Padding.only(top=14))

    def actualizar(_=None):
        p = estado["prov"]
        a24, a10 = valor(p, 2024, "NACIMIENTOS"), valor(p, 2010, "NACIMIENTOS")
        var = (a24 / a10 - 1) * 100
        f27 = proyeccion(p, 2027)
        kpis.controls = [
            kpi("Nacimientos 2024", f0(a24), f"{f1(var)} % vs 2010 ({f0(a10)})", ROJO if var < 0 else VERDE, ft.Icons.CHILD_CARE),
            kpi("Tasa de natalidad 2024", f"{f1(valor(p, 2024, 'TASA'))} ‰", f"2010: {f1(valor(p, 2010, 'TASA'))} ‰", AZUL, ft.Icons.SHOW_CHART),
            kpi("Madres menores de 20", f"{f1(valor(p, 2024, 'PCT_MENOR20'))} %", f"2010: {f1(valor(p, 2010, 'PCT_MENOR20'))} %", VERDE, ft.Icons.TRENDING_DOWN),
            kpi("Proyección 2027", f0(f27.NACIMIENTOS_PROYECTADOS), f"Rango {f0(f27.MINIMO)} - {f0(f27.MAXIMO)}", "#7C3AED", ft.Icons.TIMELINE),
        ]
        for panel, (_, fn) in zip(paneles, VISTAS):
            panel.content = fn(p)
        titulo_prov.value = f"{p} · {REGION[p]}" + ("" if p == "Jujuy" else "  (comparada con Jujuy)")
        page.update()

    def cambiar_provincia(e):
        estado["prov"] = selector.value
        actualizar()

    selector = ft.Dropdown(value="Jujuy", label="Provincia", width=190, options=[ft.DropdownOption(key=p, text=p) for p in PROVINCIAS],
                           on_select=cambiar_provincia, dense=True, bgcolor="white", border_radius=10, color="#111827")
    titulo_prov = ft.Text("Jujuy · NOA", size=13, color="#BFD7F0")

    encabezado = ft.Container(
        content=ft.Row([
            ft.Row([logo, ft.Column([ft.Text("VRA Analytics", size=24, weight=ft.FontWeight.W_800, color="white"),
                                     ft.Text("Natalidad en Jujuy en el contexto nacional · 2010-2024", size=12, color="#BFD7F0")], spacing=0)], spacing=14),
            ft.Column([selector, titulo_prov], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=4),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True, run_spacing=10),
        padding=ft.Padding.symmetric(horizontal=26, vertical=18),
        gradient=ft.LinearGradient(begin=ft.Alignment(-1, 0), end=ft.Alignment(1, 0), colors=["#0B2A4A", "#1F4E79"]),
    )

    nombres = [n for n, _ in VISTAS] + ["Asistente"]
    tabs = ft.Tabs(
        length=len(nombres), selected_index=0,
        content=ft.Column([
            ft.TabBar(tabs=[ft.Tab(label=n) for n in nombres]),
            ft.TabBarView(controls=paneles + [panel_chat], height=720),
        ], spacing=0),
    )

    pie = ft.Container(ft.Text("VRA Analytics · Gutierres Victoria · Suares Romina · Valerio Abel · Fuentes: DEIS (nacidos vivos) e INDEC (proyecciones de población)",
                               size=11, color=GRIS, text_align=ft.TextAlign.CENTER), padding=14, alignment=ft.Alignment(0, 0))

    page.add(encabezado, ft.Container(ft.Column([kpis, tabs], spacing=14), padding=ft.Padding.symmetric(horizontal=26, vertical=18)), pie)
    actualizar()


if __name__ == "__main__":
    import sys
    if "--escritorio" in sys.argv:
        ft.run(main)                                        # ventana de escritorio
    else:
        ft.run(main, view=ft.AppView.WEB_BROWSER)           # se abre en el navegador (por defecto)
