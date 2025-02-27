import pandas as pd
from logic.ibr_logic import (
    convertir_tasa_cupon_ibr_proyectado,
    convertir_tasa_cupon_ibr_online,
    sumar_negociacion_ibr,
)
from logic.shared_logic import (
    generar_fechas,
    calcular_diferencias_fechas_pago_cupon,
    calcular_numero_dias_descuento_cupon,
    calcular_cupones_futuros_cf,
    calcular_vp_cfs,
    calcular_flujo_pesos,
    convertir_nominal_a_efectiva_anual,
)


def generar_cashflows_df_ibr(
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
        periodicidad=periodo_cupon,
        modalidad=base_intereses,
    )
    dias_cupon = calcular_diferencias_fechas_pago_cupon(
        lista_fechas=fechas_cupon, modalidad=base_intereses
    )
    dias_descuento_cupon = calcular_numero_dias_descuento_cupon(
        fecha_negociacion=fecha_negociacion, lista_fechas_pago_cupon=fechas_cupon
    )
    # ⚠️ Handling missing IBR rate
    try:
        if archivo_subido:
            tasa_convertida = convertir_tasa_cupon_ibr_proyectado(
                base_dias_anio=base_intereses,
                periodicidad=periodo_cupon,
                tasa_anual_cupon=tasa_cupon,
                lista_fechas=fechas_cupon,
                fecha_inicio=fecha_emision,
                fecha_negociacion=fecha_negociacion,
                archivo=archivo_subido,
            )
        else:
            tasa_convertida = convertir_tasa_cupon_ibr_online(
                base_dias_anio=base_intereses,
                periodicidad=periodo_cupon,
                tasa_anual_cupon=tasa_cupon,
                lista_fechas=fechas_cupon,
                fecha_inicio=fecha_emision,
                fecha_negociacion=fecha_negociacion,
            )
    except ValueError as e:
        return {"error": str(e)}  # Return error message instead of crashing

    cf_t = calcular_cupones_futuros_cf(
        valor_nominal_base=valor_nominal_base, tasas_periodicas=tasa_convertida
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

    tasa_ibr_spread_negociacion = sumar_negociacion_ibr(
        tasa_negociacion=tasa_mercado,
        fecha_negociacion=fecha_negociacion,
        archivo=archivo_subido,
    )
    tasa_negociacion_efectiva = convertir_nominal_a_efectiva_anual(
        tasa_nominal_negociacion=tasa_ibr_spread_negociacion, periodo=periodo_cupon
    )

    return tasa_negociacion_efectiva
