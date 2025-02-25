import streamlit as st
from data_handling.shared_data import clasificar_precio_limpio
from utils.ui_helpers import display_errors
from utils.validation import validate_inputs
from data_handling.tasa_fija_data import generar_cashflows_df
from data_handling.shared_data import cupon_corrido_calc

# Initialize session state if not already set
if "disable_uploader" not in st.session_state:
    st.session_state.disable_uploader = True
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None  # Store the uploaded file persistently


# Function to toggle the file uploader state
def toggle_uploader():
    st.session_state.disable_uploader = st.session_state.radio_option == "Online"


# Function to store the uploaded file persistently
def store_file():
    st.session_state.uploaded_file = st.session_state.file_uploader_key


# Title
st.title("Calculadora IBR")
st.divider()

upload_col1, upload_col2 = st.columns(2)

with upload_col1:
    # Radio button to enable/disable file uploader (Outside Form)
    st.radio(
        "**Usar los datos online o subir un archivo excel?**",
        ("Online", "Excel"),
        key="radio_option",
        on_change=toggle_uploader,
        index=0,
    )
with upload_col2:
    # File uploader (Outside Form) but stores in session state
    file = st.file_uploader(
        "Selecciona el excel con los datos de IBR",
        disabled=st.session_state.disable_uploader,
        key="file_uploader_key",
        on_change=store_file,
        type=["xlsx"],
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
                "**Tasa de cupón IBR +**",
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
                index=1,
                horizontal=True,
                disabled=True,
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
            valor_giro_placeholder = st.empty()
            valor_giro_placeholder.metric(label="Valor de Giro", value="$0")
        with col_results2:
            cupon_corrido_placeholder = st.empty()
            cupon_corrido_placeholder.metric(label="Cupón Corrido", value="0%")
        with col_results3:
            precio_limpio_placeholder = st.empty()
            precio_limpio_placeholder.metric(label="Precio Limpio", value="0%")
            precio_limpio_placeholder_venta = st.empty()

# Container for detailed table
st.header("Tabla detallada")

if submitted:
    # Retrieve file from session state
    uploaded_file = st.session_state.uploaded_file
    if uploaded_file:
        st.success(f"File '{uploaded_file.name}' included in calculation!")

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

        st.dataframe(df, use_container_width=True, height=500)

        # Calculate new metric values
        precio_sucio = df["VP CF"].sum()
        valor_giro = (precio_sucio / 100) * valor_nominal
        cupon_corrido = cupon_corrido_calc(df=df, date_negociacion=fecha_negociacion)
        precio_limpio = precio_sucio - cupon_corrido
        precio_limpio_venta = clasificar_precio_limpio(precio_limpio)

        # Update metrics dynamically
        precio_sucio_placeholder.metric("**Precio Sucio**", f"{precio_sucio:.3f}%")
        valor_giro_placeholder.write(f"**Valor de Giro: ${valor_giro:,.2f}**")
        cupon_corrido_placeholder.metric("**Cupón Corrido**", f"{cupon_corrido:.3f}%")
        precio_limpio_placeholder.metric("**Precio Limpio**", f"{precio_limpio:.3f}%")
        precio_limpio_placeholder_venta.markdown(
            precio_limpio_venta.replace("\n", "  \n")
        )
