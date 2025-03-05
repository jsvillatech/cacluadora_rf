import streamlit as st

from data_handling.ipc_data import generar_cashflows_df_ipc, obtener_tasa_negociacion_EA
from data_handling.shared_data import (
    calcular_cupon_corrido,
    calcular_precio_sucio_desde_VP,
    calcular_tir_desde_df,
    clasificar_precio_limpio,
)
from utils.ui_helpers import display_errors
from utils.validation import validate_inputs

# Initialize session state
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None  # Store the uploaded file persistently


# Function to store the uploaded file persistently
def store_file():
    st.session_state.uploaded_file = st.session_state.file_uploader_key


# Title
st.title("Calculadora IPC")
st.divider()

upload_col1, upload_col2 = st.columns(2)

with upload_col1:
    # Radio button to enable/disable file uploader (Outside Form)
    radio_data = st.radio(
        "**Fuente de Datos**",
        ("Online", "Excel de Proyecciones"),
        key="radio_option",
        index=1,
        disabled=True,
    )

with upload_col2:
    # Clear uploaded file when switching to "Online"
    if st.session_state.radio_option == "Online":
        st.session_state.uploaded_file = None  # Reset uploaded file

    # Display file uploader only if "Excel" is selected
    if st.session_state.radio_option == "Excel de Proyecciones":
        uploaded_file = st.file_uploader(
            "Selecciona el excel con los datos de IBR Proyectados",
            key="file_uploader_key",
            type=["xlsx"],
            on_change=store_file,
        )

# Main form
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
                format="%.2f",
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
                options=("Anual", "Semestral", "Trimestral", "Mensual"),
                index=None,
                placeholder="Seleccionar",
            )
            periodo_cupon_error = st.empty()

        with header_form_col2:
            tasa_cupon = st.number_input(
                "**Tasa de cupón (Spread)**",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=0.01,
                format="%0.3f",
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
                "**Tasa Negociacion (Spread)**",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=0.01,
                format="%0.3f",
            )
            tasa_mercado_error = st.empty()

        with header_form_col3:
            modalidad_tasa_cupon = st.radio(
                "**Modalidad Tasa Cupón**",
                ["EA", "Nominal"],
                index=0,
                horizontal=True,
                disabled=True,
            )
            valor_nominal_base = st.number_input(
                "**Valor Nominal Base**",
                min_value=0.0,
                max_value=1000000.0,
                value=100.00,
                step=0.01,
                format="%0.2f",
            )
            valor_nominal_base_error = st.empty()
            modalidad_tasa_ipc = st.radio(
                "**Modalidad IPC**",
                ["Inicio", "Final"],
                index=0,
                horizontal=True,
            )

        # Create three columns and place the button in the middle column
        col_left, col_center, col_right = st.columns([2, 1, 2])
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
            valor_tasa_negociacion_EA_placeholder = st.empty()
            valor_tasa_negociacion_EA_placeholder.metric(
                label="Tasa Neg. (IPC+Sprd) EA", value="0%"
            )

        with col_results2:
            cupon_corrido_placeholder = st.empty()
            cupon_corrido_placeholder.metric(label="Cupón Corrido", value="0%")
            valor_giro_placeholder = st.empty()
            valor_giro_placeholder.metric(label="Valor de Giro", value="$0")
            valor_TIR_inversion_placeholder = st.empty()
            valor_TIR_inversion_placeholder.metric(label="TIR Inversión", value="0%")

        with col_results3:
            precio_limpio_placeholder = st.empty()
            precio_limpio_placeholder.metric(label="Precio Limpio", value="0%")
            precio_limpio_placeholder_venta = st.empty()

# Container for detailed table
st.header("Tabla detallada")

if submitted:
    # Retrieve file from session state
    uploaded_file = st.session_state.uploaded_file
    if radio_data == "Excel" and uploaded_file is None:
        st.error("Por favor sube el archivo de proyecciones.")
    else:
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
            if uploaded_file:
                st.success(f"File '{uploaded_file.name}' included in calculation!")
            else:
                st.success("Datos de BanRep utilizados en el cálculo.")

            df_errors_placeholder = st.empty()
            df = generar_cashflows_df_ipc(
                fecha_emision=fecha_emision,
                fecha_vencimiento=fecha_vencimiento,
                fecha_negociacion=fecha_negociacion,
                periodo_cupon=periodo_cupon,
                base_intereses=base_intereses,
                tasa_cupon=tasa_cupon,
                valor_nominal_base=valor_nominal_base,
                tasa_mercado=tasa_mercado,
                valor_nominal=valor_nominal,
                archivo_subido=uploaded_file,
                modalidad_tasa_ipc=modalidad_tasa_ipc,
            )
            if isinstance(df, dict) and "error" in df:
                df_errors_placeholder.error(df["error"])
            else:
                # show df
                config = {
                    "CFt": st.column_config.NumberColumn(
                        "CFt", format="%.3f%%", help="Cupón Futuro"
                    ),
                    "VP CF": st.column_config.NumberColumn(
                        "VP CF", format="%.4f%%", help="Valor Presente del Cupón"
                    ),
                }
                st.dataframe(
                    df, use_container_width=True, height=500, column_config=config
                )

                # Calculate new metric values
                precio_sucio = calcular_precio_sucio_desde_VP(df)
                valor_giro = (precio_sucio / 100) * valor_nominal
                cupon_corrido = calcular_cupon_corrido(
                    df=df,
                    date_negociacion=fecha_negociacion,
                    periodicidad=periodo_cupon,
                    base_intereses=base_intereses,
                )
                precio_limpio = precio_sucio - cupon_corrido
                precio_limpio_venta = clasificar_precio_limpio(precio_limpio)
                valor_TIR_negociar = obtener_tasa_negociacion_EA(
                    tasa_mercado=tasa_mercado,
                    fecha_negociacion=fecha_negociacion,
                    archivo_subido=uploaded_file,
                    periodo_cupon=periodo_cupon,
                )
                valor_TIR_inversion = calcular_tir_desde_df(
                    df=df,
                    columna_flujos="Flujo Pesos ($)",
                    valor_giro=valor_giro,
                    periodo=periodo_cupon,
                )
                # Update metrics dynamically
                precio_sucio_placeholder.metric(
                    "**Precio Sucio**", f"{precio_sucio:.3f}%"
                )
                valor_giro_placeholder.write(f"**Valor de Giro: ${valor_giro:,.2f}**")
                valor_nominal_placeholder.write(
                    f"**Valor Nominal: ${valor_nominal:,.2f}**"
                )
                cupon_corrido_placeholder.metric(
                    "**Cupón Corrido**", f"{cupon_corrido:.3f}%"
                )
                precio_limpio_placeholder.metric(
                    "**Precio Limpio**", f"{precio_limpio:.3f}%"
                )
                precio_limpio_placeholder_venta.markdown(
                    precio_limpio_venta.replace("\n", "  \n")
                )
                valor_tasa_negociacion_EA_placeholder.metric(
                    "**Tasa Negociación EA**", f"{valor_TIR_negociar:.3f}%"
                )
                valor_TIR_inversion_placeholder.metric(
                    "**TIR Inversión**", f"{valor_TIR_inversion:.3f}%"
                )
