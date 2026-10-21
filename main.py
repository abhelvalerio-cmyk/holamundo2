import flet as ft

def main(page: ft.Page):
    page.title = "Cotizador de Informática"
    page.window_width = 900
    page.window_height = 700

    txt_cliente = ft.TextField(label="Nombre del cliente")
    txt_presupuesto = ft.TextField(label="Presupuesto tope ($)", keyboard_type=ft.KeyboardType.NUMBER)

    dd_procesador = ft.Dropdown(
        label="Seleccione Procesador",
        options=[
            ft.dropdown.Option(key="p1", text="Intel Core i3 (65W) - $100000"),
            ft.dropdown.Option(key="p2", text="Intel Core i5 (65W) - $180000"),
            ft.dropdown.Option(key="p3", text="AMD Ryzen 7 (105W) - $280000"),
        ]
    )

    datos_procesadores = {
        "p1": {"precio": 100000, "watts": 65},
        "p2": {"precio": 180000, "watts": 65},
        "p3": {"precio": 280000, "watts": 105}
    }

    slider_ram = ft.Slider(min=8, max=64, divisions=7, value=8, label="{value} GB")

    chk_gpu = ft.Checkbox(label="Placa de video dedicada ($250000 - 180W)")
    chk_ssd = ft.Checkbox(label="Unidad SSD extra ($45000 - 10W)")
    chk_armado = ft.Checkbox(label="Servicio de armado ($15000 - 0W)")

    sw_envio = ft.Switch(label="Envío a domicilio ($5000)")

    rg_pago = ft.RadioGroup(content=ft.Column([
        ft.Radio(value="efectivo", label="Efectivo / Transferencia (10% descuento)"),
        ft.Radio(value="debito", label="Tarjeta de Débito (Precio de lista)"),
        ft.Radio(value="credito", label="Tarjeta de Crédito en 3 cuotas (15% recargo)")
    ]))

    txt_alerta = ft.Text(color="red")
    txt_subtotal = ft.Text("Subtotal: $0")
    txt_total = ft.Text("Total a pagar: $0")
    txt_cuotas = ft.Text("")
    txt_fuente = ft.Text("Fuente recomendada: -")
    txt_presupuesto_resultado = ft.Text("")

    def calcular_cotizacion(e):
        txt_alerta.value = ""
        
        if not dd_procesador.value:
            txt_alerta.value = "Error: Debe seleccionar un procesador."
            page.update()
            return
            
        if not rg_pago.value:
            txt_alerta.value = "Error: Debe seleccionar un medio de pago."
            page.update()
            return

        try:
            presupuesto = float(txt_presupuesto.value)
        except (ValueError, TypeError):
            txt_alerta.value = "Error: Ingrese un presupuesto numérico válido."
            page.update()
            return

        proc_info = datos_procesadores[dd_procesador.value]
        precio_cpu = proc_info["precio"]
        watts_cpu = proc_info["watts"]

        gb_ram = int(slider_ram.value)
        precio_ram = (gb_ram / 8) * 20000

        precio_adicionales = 0
        watts_adicionales = 0

        if chk_gpu.value:
            precio_adicionales += 250000
            watts_adicionales += 180
        if chk_ssd.value:
            precio_adicionales += 45000
            watts_adicionales += 10
        if chk_armado.value:
            precio_adicionales += 15000

        costo_envio = 5000 if sw_envio.value else 0

        subtotal = precio_cpu + precio_ram + precio_adicionales + costo_envio

        total = subtotal
        cuotas_texto = ""

        if rg_pago.value == "efectivo":
            total = subtotal * 0.90
        elif rg_pago.value == "debito":
            total = subtotal
        elif rg_pago.value == "credito":
            total = subtotal * 1.15
            valor_cuota = total / 3
            cuotas_texto = f"3 cuotas de: ${valor_cuota:.2f}"

        consumo_base = watts_cpu + watts_adicionales + 50
        consumo_estimado = consumo_base * 1.25

        if consumo_estimado > 450:
            fuente_recomendada = "Se recomienda una fuente de 650W o superior."
        else:
            fuente_recomendada = "Se sugiere una fuente convencional de 500W."

        if total <= presupuesto:
            diferencia = presupuesto - total
            resultado_presupuesto = f"Aprobado. Saldo a favor: ${diferencia:.2f}"
        else:
            diferencia = total - presupuesto
            resultado_presupuesto = f"Advertencia: Faltan ${diferencia:.2f} para cubrir la cotización."

        txt_subtotal.value = f"Subtotal: ${subtotal:.2f}"
        txt_total.value = f"Total a pagar: ${total:.2f}"
        txt_cuotas.value = cuotas_texto
        txt_fuente.value = f"Consumo estimado: {consumo_estimado:.1f}W. {fuente_recomendada}"
        txt_presupuesto_resultado.value = resultado_presupuesto
        
        page.update()

    BotonClase = getattr(ft, "FilledButton", getattr(ft, "Button", getattr(ft, "ElevatedButton", None)))
    btn_calcular = BotonClase("Calcular Cotización", on_click=calcular_cotizacion)

    formulario = ft.ListView(
        controls=[
            ft.Text("Datos del Cliente", weight="bold"),
            txt_cliente,
            txt_presupuesto,
            ft.Divider(),
            ft.Text("Hardware", weight="bold"),
            dd_procesador,
            ft.Text("Memoria RAM (GB):"),
            slider_ram,
            ft.Text("Adicionales Optativos:"),
            chk_gpu,
            chk_ssd,
            chk_armado,
            sw_envio,
            ft.Divider(),
            ft.Text("Medio de Pago", weight="bold"),
            rg_pago,
            ft.Container(content=btn_calcular, padding=10)
        ],
        expand=True,
        spacing=10
    )

    resultados = ft.ListView(
        controls=[
            ft.Text("Resultados de la Cotización", weight="bold"),
            txt_alerta,
            txt_subtotal,
            txt_total,
            txt_cuotas,
            txt_fuente,
            txt_presupuesto_resultado
        ],
        expand=True,
        spacing=10
    )

    page.add(
        ft.Row([
            ft.Container(content=formulario, expand=True),
            ft.VerticalDivider(),
            ft.Container(content=resultados, expand=True)
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
    )

if __name__ == "__main__":
    if hasattr(ft, "app"):
        ft.app(target=main)
    elif hasattr(ft, "run"):
        ft.run(main)