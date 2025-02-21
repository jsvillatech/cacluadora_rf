import streamlit as st
from datetime import datetime
import pandas as pd
import numpy as np
from data import generar_cashflows_df


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
            fecha_emision = st.date_input(
                "**Fecha de emisión**", format="DD/MM/YYYY", value=None
            )
            fecha_vencimiento = st.date_input(
                "**Fecha de Vencimiento**", format="DD/MM/YYYY", value=None
            )
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

        with header_form_col2:
            tasa_cupon = st.number_input(
                "**Tasa de cupón TF**",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=0.01,
            )
            base_intereses = st.selectbox(
                label="**Base Intereses**",
                options=("30/360", "365/365"),
                index=None,
                placeholder="Seleccionar",
            )
            fecha_negociacion = st.date_input(
                "**Fecha de Negociación**", format="DD/MM/YYYY", value=None
            )
            tasa_mercado = st.number_input(
                "**Tasa de Rendimiento EA**",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=0.01,
            )

        with header_form_col3:
            modalidad_tasa_cupon = st.radio(
                "**Modalidad Tasa Cupón**",
                ["EA", "Nominal"],
                index=None,
                horizontal=True,
            )
            valor_nominal_base = st.number_input(
                "**Valor Nominal Base**",
                min_value=0.0,
                max_value=1000000.0,
                value=100.00,
                step=0.01,
            )

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

st.header("Información Adicional")

if submitted:
    # st.write("Your birthday is:", fecha_emision)
    # st.metric(label="Precio Sucio", value=200)
    # st.error("Error en el cálculo del Precio Sucio")
    # errors = validate_inputs(start_date, end_date, name, age)
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
    st.dataframe(df)

    # 🔹 Calculate new metric values
    precio_sucio = df["VP CF"].sum()
    valor_giro = (precio_sucio / 100) * valor_nominal
    cupon_corrido = "2%"  # Example placeholder
    precio_limpio = f"{precio_sucio - 2:.2f}%"

    # 🔹 Update metrics dynamically using `st.empty()`
    precio_sucio_placeholder.metric(label="Precio Sucio", value=f"{precio_sucio:.3f}%")
    valor_giro_placeholder.write(f"**Valor de Giro: ${valor_giro:,.2f}**")
    cupon_corrido_placeholder.metric(label="Cupón Corrido", value=cupon_corrido)
    precio_limpio_placeholder.metric(label="Precio Limpio", value=precio_limpio)


# Handle form submission
# if submitted:
#    errors = validate_inputs(start_date, end_date, name, age)

#    if errors:
#        for error in errors:
#            st.error(error)
#    else:
#        process_data(start_date, end_date, name, age)  # Only runs if valid
