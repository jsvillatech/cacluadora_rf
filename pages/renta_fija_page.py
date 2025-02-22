import streamlit as st
from datetime import datetime
import pandas as pd
import numpy as np
from utils.data import generar_cashflows_df, cupon_corrido_calc
from utils.ui_helpers import display_errors


# validate form function
def validate_inputs(
    valor_nominal,
    fecha_emision,
    fecha_vencimiento,
    periodo_cupon,
    tasa_cupon,
    base_intereses,
    fecha_negociacion,
    tasa_mercado,
    valor_nominal_base,
):
    """Validates form inputs and returns a dictionary of errors."""
    errors = {}

    # Lista de campos obligatorios y sus mensajes de error
    required_fields = {
        "valor_nominal": "❌ El valor nominal no puede estar vacío.",
        "fecha_emision": "❌ La fecha de emisión no puede estar vacía.",
        "fecha_vencimiento": "❌ La fecha de vencimiento no puede estar vacía.",
        "periodo_cupon": "❌ El período del cupón no puede estar vacío.",
        "tasa_cupon": "❌ La tasa del cupón no puede estar vacía.",
        "base_intereses": "❌ La base de intereses no puede estar vacía.",
        "fecha_negociacion": "❌ La fecha de negociación no puede estar vacía.",
        "tasa_mercado": "❌ La tasa de mercado no puede estar vacía.",
        "valor_nominal_base": "❌ El valor nominal base no puede estar vacío.",
    }

    # Verificación automática de campos vacíos
    for field, error_message in required_fields.items():
        if not locals()[field]:  # Obtiene el valor de la variable por su nombre
            errors[field] = error_message

    # Validación de fechas
    if fecha_emision and fecha_vencimiento and fecha_emision >= fecha_vencimiento:
        errors["fecha_emision"] = (
            "❌ La fecha de emisión debe ser menor a la fecha de vencimiento."
        )

    if fecha_negociacion and fecha_emision and fecha_vencimiento:
        if not (fecha_emision < fecha_negociacion < fecha_vencimiento):
            errors["fecha_negociacion"] = (
                "❌ La fecha de negociación debe ser mayor a la fecha de emisión y menor a la fecha de vencimiento."
            )

    return errors


# start from here
st.title("Calculadora Renta Fija")
st.divider()
main_header_col1, main_header_col2 = st.columns(2)
with main_header_col1:

    with st.form("bond_form"):
        st.subheader("**Condiciones Faciales**")
        header_form_col1, header_form_col2, header_form_col3 = st.columns(3)

        with header_form_col1:
            valor_nominal = st.number_input(
                "**Valor Nominal Negociación**",
                min_value=0.0,
                value=0.0,
                step=0.01,
            )
            valor_nominal_error = st.empty()
            fecha_emision = st.date_input(
                "**Fecha de emisión**", format="DD/MM/YYYY", value=None
            )
            fecha_emision_error = st.empty()
            fecha_vencimiento = st.date_input(
                "**Fecha de Vencimiento**", format="DD/MM/YYYY", value=None
            )
            fecha_vencimiento_error = st.empty()
            periodo_cupon = st.selectbox(
                label="**Periodo Pago Cupón**",
                options=(
                    "Anual",
                    "Semestral",
                    "Trimestral",
                    "Mensual",
                    # "Cero Cupón",
                    # "Periodo Vencido",
                ),
                index=None,
                placeholder="Seleccionar",
            )
            periodo_cupon_error = st.empty()

        with header_form_col2:
            tasa_cupon = st.number_input(
                "**Tasa de cupón TF**",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=0.01,
            )
            tasa_cupon_error = st.empty()
            base_intereses = st.selectbox(
                label="**Base Intereses**",
                options=("30/360", "365/365"),
                index=None,
                placeholder="Seleccionar",
            )
            base_intereses_error = st.empty()
            fecha_negociacion = st.date_input(
                "**Fecha de Negociación**", format="DD/MM/YYYY", value=None
            )
            fecha_negociacion_error = st.empty()
            tasa_mercado = st.number_input(
                "**Tasa de Rendimiento EA**",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=0.01,
            )
            tasa_mercado_error = st.empty()
        with header_form_col3:
            modalidad_tasa_cupon = st.radio(
                "**Modalidad Tasa Cupón**",
                ["EA", "Nominal"],
                index=0,
                horizontal=True,
            )
            valor_nominal_base = st.number_input(
                "**Valor Nominal Base**",
                min_value=0.0,
                max_value=1000000.0,
                value=100.00,
                step=0.01,
            )
            valor_nominal_base_error = st.empty()

        # Create three columns and place the button in the middle column
        col_left, col_center, col_right = st.columns(
            [2, 1, 2]
        )  # Adjust ratios as needed
        with col_center:
            submitted = st.form_submit_button("Calcular")

# Container for results
with main_header_col2:
    with st.container(key="bond_results", border=True):
        st.subheader("**Resultados**")
        col_results1, col_results2, col_results3 = st.columns(3)
        with col_results1:
            precio_sucio_placeholder = st.empty()
            valor_giro_placeholder = st.empty()
        with col_results2:
            cupon_corrido_placeholder = st.empty()
        with col_results3:
            precio_limpio_placeholder = st.empty()

# 🔹 Initial default metric values
precio_sucio_placeholder.metric(label="Precio Sucio", value="0%")
valor_giro_placeholder.metric(label="Valor de Giro", value="$0")
cupon_corrido_placeholder.metric(label="Cupón Corrido", value="0%")
precio_limpio_placeholder.metric(label="Precio Limpio", value="0%")

st.header("Tabla detallada")

if submitted:
    # Validate form inputs
    errors = validate_inputs(
        valor_nominal,
        fecha_emision,
        fecha_vencimiento,
        periodo_cupon,
        tasa_cupon,
        base_intereses,
        fecha_negociacion,
        tasa_mercado,
        valor_nominal_base,
    )

    error_placeholders = {
        "valor_nominal": valor_nominal_error,
        "fecha_emision": fecha_emision_error,
        "fecha_vencimiento": fecha_vencimiento_error,
        "periodo_cupon": periodo_cupon_error,
        "tasa_cupon": tasa_cupon_error,
        "base_intereses": base_intereses_error,
        "fecha_negociacion": fecha_negociacion_error,
        "tasa_mercado": tasa_mercado_error,
        "valor_nominal_base": valor_nominal_base_error,
    }

    if errors:
        display_errors(errors, error_placeholders)

    else:

        df = generar_cashflows_df(
            fecha_emision=fecha_emision,
            fecha_vencimiento=fecha_vencimiento,
            fecha_negociacion=fecha_negociacion,
            periodo_cupon=periodo_cupon,
            base_intereses=base_intereses,
            modalidad_tasa_cupon=modalidad_tasa_cupon,
            tasa_cupon=tasa_cupon,
            valor_nominal_base=valor_nominal_base,
            tasa_mercado=tasa_mercado,
            valor_nominal=valor_nominal,
        )
        # show df
        config = {
            "CFt": st.column_config.NumberColumn(
                "CFt", format="%.3f%%", help="Cupón Futuro"
            ),
            "VP CF": st.column_config.NumberColumn(
                "VP CF", format="%.3f%%", help="Valor Presente del Cupón"
            ),
        }
        st.dataframe(df, column_config=config, use_container_width=True, height=500)

        # 🔹 Calculate new metric values
        precio_sucio = df["VP CF"].sum()
        valor_giro = (precio_sucio / 100) * valor_nominal
        cupon_corrido = cupon_corrido_calc(df=df, date_negociacion=fecha_negociacion)
        precio_limpio = precio_sucio - cupon_corrido

        # 🔹 Update metrics dynamically using `st.empty()`
        precio_sucio_placeholder.metric(
            label="**Precio Sucio**", value=f"{precio_sucio:.3f}%"
        )
        valor_giro_placeholder.write(f"**Valor de Giro: ${valor_giro:,.2f}**")
        cupon_corrido_placeholder.metric(
            label="**Cupón Corrido**", value=f"{cupon_corrido:.3f}%"
        )
        precio_limpio_placeholder.metric(
            label="**Precio Limpio**", value=f"{precio_limpio:.3f}%"
        )
