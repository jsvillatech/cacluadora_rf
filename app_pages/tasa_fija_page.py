import pandas as pd
import streamlit as st

from data_handling.shared_data import (
    calcular_convexidad,
    calcular_cupon_corrido,
    calcular_duracion_mod,
    calcular_dv01,
    calcular_macaulay,
    calcular_precio_sucio_desde_VP,
    calcular_tir_desde_df,
    clasificar_precio_limpio,
)
from data_handling.tasa_fija_data import generar_cashflows_df_tf
from utils.ui_helpers import display_errors
from utils.validation import validate_inputs

# start from here
st.title("Calculadora Tasa Fija")
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
                step=0.5,
                format="%.4f",
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
                step=0.5,
                format="%.4f",
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
                step=0.5,
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
            precio_sucio_placeholder.metric(label="Precio Sucio", value="0%")
            valor_nominal_placeholder = st.empty()
            valor_nominal_placeholder.metric(label="Valor Nominal", value="$0")
            valor_TIR_inversion_placeholder = st.empty()
            valor_TIR_inversion_placeholder.metric(label="TIR Inversión", value="0%")
            dv01_placeholder = st.empty()
            dv01_placeholder.metric(label="DV01", value="$0")

        with col_results2:
            cupon_corrido_placeholder = st.empty()
            cupon_corrido_placeholder.metric(label="Cupón Corrido", value="0%")
            valor_giro_placeholder = st.empty()
            valor_giro_placeholder.metric(label="Valor de Giro", value="$0")
            duracion_macaulay_placeholder = st.empty()
            duracion_macaulay_placeholder.metric(
                label="Duración Macaulay (Años)", value="0"
            )
            convexidad_placeholder = st.empty()
            convexidad_placeholder.metric(label="Convexidad", value="0")

        with col_results3:
            precio_limpio_placeholder = st.empty()
            precio_limpio_placeholder.metric(label="Precio Limpio", value="0%")
            precio_limpio_placeholder_venta = st.empty()
            duracion_modficada_placeholder = st.empty()
        label_chart_giro_place_holder = st.empty()
        result_chart_giro_place_holder = st.empty()
        label_chart_tasa_place_holder = st.empty()
        result_chart_tasa_place_holder = st.empty()


# Container for detailed table
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
        df = generar_cashflows_df_tf(
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
        # Inicia index desde 1.
        df.index = range(1, len(df) + 1)
        # show df
        config = {
            "CFt": st.column_config.NumberColumn(
                "CFt", format="%.6f%%", help="Cupón Futuro"
            ),
            "VP CF": st.column_config.NumberColumn(
                "VP CF", format="%.6f%%", help="Valor Presente del Cupón"
            ),
            "t*PV CF": st.column_config.NumberColumn(
                "t*PV CF", format="%.6f%%", help="Valor Presente * t"
            ),
            "(t*PV CF)*(t+1)": st.column_config.NumberColumn(
                "(t*PV CF)*(t+1)", format="%.6f%%", help="t*Valor Presente * t+1"
            ),
        }
        # show DF
        st.dataframe(df, column_config=config, use_container_width=True, height=900)

        # 🔹 Calculate new metric values
        precio_sucio = calcular_precio_sucio_desde_VP(df.copy())
        valor_giro = (precio_sucio / 100) * valor_nominal
        cupon_corrido = calcular_cupon_corrido(
            df=df.copy(),
            date_negociacion=fecha_negociacion,
            periodicidad=periodo_cupon,
            base_intereses=base_intereses,
        )
        precio_limpio = precio_sucio - cupon_corrido
        precio_limpio_venta = clasificar_precio_limpio(precio_limpio)
        valor_TIR_inversion = calcular_tir_desde_df(
            df=df.copy(),
            columna_flujos="Flujo Pesos ($)",
            valor_giro=valor_giro,
            fecha_negociacion=fecha_negociacion,
        )
        d_macaulay = calcular_macaulay(
            df=df.copy(), columna="t*PV CF", precio_sucio=precio_sucio
        )
        d_mod = calcular_duracion_mod(macaulay=d_macaulay, tasa=tasa_mercado)
        dv01 = calcular_dv01(d_mod=d_mod, valor_giro=valor_giro)
        conv = calcular_convexidad(
            df=df,
            columna="(t*PV CF)*(t+1)",
            tasa_mercado=tasa_mercado,
            precio_sucio=precio_sucio,
            periodicidad=periodo_cupon,
            base_intereses=base_intereses,
        )

        # 🔹 Update metrics dynamically using `st.empty()`
        precio_sucio_placeholder.metric(
            label="**Precio Sucio**", value=f"{precio_sucio:.3f}%"
        )
        valor_giro_placeholder.write(f"**Valor de Giro: ${valor_giro:,.2f}**")
        valor_nominal_placeholder.write(f"**Valor Nominal: ${valor_nominal:,.2f}**")
        cupon_corrido_placeholder.metric(
            label="**Cupón Corrido**", value=f"{cupon_corrido:.3f}%"
        )
        precio_limpio_placeholder.metric(
            label="**Precio Limpio**", value=f"{precio_limpio:.3f}%"
        )
        precio_limpio_placeholder_venta.markdown(
            precio_limpio_venta.replace("\n", "  \n")
        )
        valor_TIR_inversion_placeholder.metric(
            "**TIR Inversión**", f"{valor_TIR_inversion:.3f}%"
        )
        duracion_macaulay_placeholder.metric(
            "**Duración Macaulay (Años)**", f"{d_macaulay:.3f}"
        )
        duracion_modficada_placeholder.metric("**Duración\\***", f"{d_mod:.3f}")
        dv01_placeholder.write(f"**DV01:**  \n**${dv01:,.2f}**")
        convexidad_placeholder.write(f"**Convexidad**  \n**{conv:,.3f}**")

        # Create a DataFrame with the values, using the category names as the index
        datos_giro = {"Value": [valor_giro, valor_nominal]}
        df_giro = pd.DataFrame(datos_giro, index=["Valor Giro", "Valor Nominal"])

        # Create a DataFrame with the values, using the category names as the index
        datos_tasa = {"Value": [tasa_cupon, tasa_mercado]}
        df_tasa = pd.DataFrame(datos_tasa, index=["Tasa Cupón", "Tasa Mercado"])

        # Display the bar chart
        label_chart_giro_place_holder.write("Valor Giro vs Nominal")
        result_chart_giro_place_holder.bar_chart(df_giro, horizontal=True)
        label_chart_tasa_place_holder.write("Tasa Mercado vs Cupón")
        result_chart_tasa_place_holder.bar_chart(df_tasa, horizontal=True)
