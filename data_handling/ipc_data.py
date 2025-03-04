import pandas as pd
from logic.ipc_logic import procesar_fechas
import datetime
from logic.shared_logic import (
    generar_fechas,
    calcular_diferencias_fechas_pago_cupon,
    calcular_numero_dias_descuento_cupon,
    calcular_cupones_futuros_cf,
    calcular_vp_cfs,
    calcular_flujo_pesos,
    convertir_nominal_a_efectiva_anual,
)
from data_handling.shared_data import filtrar_por_fecha


def generar_cashflows_df_ipc(
    fecha_emision,
    fecha_vencimiento,
    fecha_negociacion,
    periodo_cupon,
    base_intereses,
    tasa_cupon,
    valor_nominal_base,
    tasa_mercado,
    valor_nominal,
    archivo_subido,
):
    """
    Returns a complete bond cash flow DataFrame.
    """
    fechas_cupon = generar_fechas(
        fecha_inicio=fecha_emision,
        fecha_fin=fecha_vencimiento,
        fecha_negociacion=fecha_negociacion,
        periodicidad=periodo_cupon,
        modalidad=base_intereses,
    )
    nuevas_fechas, rates = procesar_fechas(
        lista_fechas=fechas_cupon,
        fecha_neg=fecha_negociacion,
        archivo=archivo_subido,
        spread=tasa_cupon,
        periodicidad=periodo_cupon,
    )
    dias_cupon = calcular_diferencias_fechas_pago_cupon(
        lista_fechas=nuevas_fechas, modalidad=base_intereses
    )
    dias_descuento_cupon = calcular_numero_dias_descuento_cupon(
        fecha_negociacion=fecha_negociacion, lista_fechas_pago_cupon=nuevas_fechas
    )

    cf_t = calcular_cupones_futuros_cf(
        valor_nominal_base=valor_nominal_base, tasas_periodicas=rates
    )

    # IBR+SPREAD negociacion -> Tasa Negociacion EA
    tasa_negociacion_efectiva = obtener_tasa_negociacion_EA(
        tasa_mercado, fecha_negociacion, archivo_subido, periodo_cupon
    )

    vp_cfs = calcular_vp_cfs(
        lista_cfs=cf_t,
        tasa_mercado=tasa_negociacion_efectiva,
        lista_dias_descuento=dias_descuento_cupon,
    )
    flujo_pesos = calcular_flujo_pesos(valor_nominal=valor_nominal, lista_cfs=cf_t)

    cashflows = {
        "Fechas Cupón": fechas_cupon,
        "Días Cupón": dias_cupon,
        "Días Dcto Cupón": dias_descuento_cupon,
        "CFt": cf_t,
        "VP CF": vp_cfs,
        # "t*PV CF": round(t_pv_cf, 8),
        # "(t*PV CF)*(t+1)": round(t_pv_cf_t1, 8),
        "Flujo Pesos ($)": flujo_pesos,
    }

    # 🔍 Ensure all columns have the same length
    for key, value in cashflows.items():
        if len(value) != len(dias_cupon):
            raise ValueError(f"Column '{key}' has inconsistent length!")

    return pd.DataFrame(cashflows)


def obtener_tasa_negociacion_EA(
    tasa_mercado, fecha_negociacion, archivo_subido, periodo_cupon
):
    """
    Convierte una tasa nominal mensual a una tasa efectiva anual (EA) considerando
    el spread de negociación del IBR.

    Parámetros:
    -----------
    tasa_mercado : float
        Tasa nominal del mercado en la fecha de negociación.
    fecha_negociacion : str o datetime
        Fecha en la que se realiza la negociación.
    archivo_subido : str o archivo
        Archivo con los datos necesarios para calcular el spread de negociación del IBR.
    periodo_cupon : int
        Número de períodos del cupón en el año (por ejemplo, 12 si es mensual).

    Retorna:
    --------
    float
        Tasa efectiva anual (EA) ajustada con el spread de negociación del IBR.
    """

    tasa_ibr_spread_negociacion = sumar_negociacion_ipc(
        tasa_negociacion=tasa_mercado,
        fecha_negociacion=fecha_negociacion,
        archivo=archivo_subido,
    )
    tasa_negociacion_efectiva = convertir_nominal_a_efectiva_anual(
        tasa_nominal_negociacion=tasa_ibr_spread_negociacion, periodo=periodo_cupon
    )

    return tasa_negociacion_efectiva


def sumar_negociacion_ipc(
    tasa_negociacion: float, fecha_negociacion: datetime.date, archivo=None
):
    """
    Calcula la tasa de negociación IBR sumando la tasa de negociación a la tasa IBR real
    obtenida desde el Banco de la República o desde un archivo de proyecciones.

    Parámetros:
        tasa_negociacion (float): La tasa adicional que se suma a la tasa IBR.
        fecha_negociacion (datetime.date): La fecha de la negociación.
        archivo (optional): Archivo con datos de proyección. Si es None, se usa data en línea.

    Retorna:
        pd.Series: Serie con la tasa de negociación IBR si se usa data en línea.
        None: Si se usa data desde un archivo (pendiente de implementación).

    Excepciones:
        Exception: Si ocurre un error al obtener la tasa IBR o si no hay datos disponibles.
    """
    try:

        tasas_ipc = filtrar_por_fecha(
            archivo=archivo,
            nombre_hoja="IPC Estimado",
            fechas_filtro=[fecha_negociacion],
        )
        if tasas_ipc.empty:
            raise ValueError(
                f"No se encontraron datos de IBR en BanRep para la fecha dada {fecha_negociacion}."
            )
        # Sumar la tasa de negociación a la tasa IBR
        tasa_ibr_spread = (tasas_ipc.iloc[0]["IPC estimado"]) * 100 + tasa_negociacion

        return tasa_ibr_spread

    except Exception as e:
        raise Exception(f"Error al calcular la tasa de negociación IBR: {str(e)}")
