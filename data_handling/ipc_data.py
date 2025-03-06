import pandas as pd

from logic.ipc_logic import (
    procesar_tasa_cupon_ipc_datos,
    sumar_spread_ipc,
)
from logic.shared_logic import (
    calcular_cupones_futuros_cf,
    calcular_diferencias_fechas_pago_cupon,
    calcular_flujo_pesos,
    calcular_numero_dias_descuento_cupon,
    calcular_vp_cfs,
    generar_fechas,
)


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
    modalidad,
    modo_ipc,
):
    """
    Returns a complete bond cash flow DataFrame.
    """
    fechas_cupon = generar_fechas(
        fecha_inicio=fecha_emision,
        fecha_fin=fecha_vencimiento,
        fecha_negociacion=fecha_negociacion,
        periodicidad=periodo_cupon,
    )
    dias_cupon = calcular_diferencias_fechas_pago_cupon(
        lista_fechas=fechas_cupon,
        periodicidad=periodo_cupon,
        base_intereses=base_intereses,
    )
    dias_descuento_cupon = calcular_numero_dias_descuento_cupon(
        fecha_negociacion=fecha_negociacion, lista_fechas=fechas_cupon
    )

    try:
        tasas_cupon = procesar_tasa_cupon_ipc_datos(
            base_dias_anio=base_intereses,
            periodicidad=periodo_cupon,
            tasa_anual_cupon=tasa_cupon,
            lista_fechas=fechas_cupon,
            dias_cupon=dias_cupon,
            fecha_negociacion=fecha_negociacion,
            modalidad=modalidad,
            archivo=archivo_subido,
            modo_ipc=modo_ipc,
        )
    except ValueError as e:
        return {"error": str(e)}  # Return error message instead of crashing

    cf_t = calcular_cupones_futuros_cf(
        valor_nominal_base=valor_nominal_base, tasas_periodicas=tasas_cupon
    )

    # IPC+SPREAD negociacion -> Tasa Negociacion EA
    tasa_negociacion_efectiva = sumar_spread_ipc(
        tasa_spread=tasa_mercado,
        fecha=fecha_negociacion,
        modalidad=modalidad,
        archivo=archivo_subido,
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
