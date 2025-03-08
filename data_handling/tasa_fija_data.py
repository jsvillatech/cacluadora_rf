import pandas as pd

from logic.shared_logic import (
    calcular_cupones_futuros_cf,
    calcular_diferencias_fechas_pago_cupon,
    calcular_flujo_pesos,
    calcular_numero_dias_descuento_cupon,
    calcular_t_pv_cf,
    calcular_vp_cfs,
    generar_fechas,
)
from logic.tasa_fija_logic import convertir_tasa_cupon_tf


def generar_cashflows_df_tf(
    fecha_emision,
    fecha_vencimiento,
    fecha_negociacion,
    periodo_cupon,
    base_intereses,
    modalidad_tasa_cupon,
    tasa_cupon,
    valor_nominal_base,
    tasa_mercado,
    valor_nominal,
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
        fecha_negociacion=fecha_negociacion,
        lista_fechas=fechas_cupon,
    )
    tasa_convertida = convertir_tasa_cupon_tf(
        modalidad_tasa=modalidad_tasa_cupon,
        periodicidad=periodo_cupon,
        tasa_anual_cupon=tasa_cupon,
        dias_pago_entre_cupon=dias_cupon,
    )
    cf_t = calcular_cupones_futuros_cf(
        valor_nominal_base=valor_nominal_base, tasas_periodicas=tasa_convertida
    )
    vp_cfs = calcular_vp_cfs(
        lista_cfs=cf_t,
        tasa_mercado=tasa_mercado,
        lista_dias_descuento=dias_descuento_cupon,
    )
    flujo_pesos = calcular_flujo_pesos(valor_nominal=valor_nominal, lista_cfs=cf_t)
    t_pv_cf = calcular_t_pv_cf(
        vp_cft=vp_cfs, conteo_dias_descuento=dias_descuento_cupon
    )

    cashflows = {
        "Fechas Cupón": fechas_cupon,
        "Días Cupón": dias_cupon,
        "Días Dcto Cupón": dias_descuento_cupon,
        "CFt": cf_t,
        "VP CF": vp_cfs,
        "t*PV CF": t_pv_cf,
        # "(t*PV CF)*(t+1)": round(t_pv_cf_t1, 8),
        "Flujo Pesos ($)": flujo_pesos,
    }

    # 🔍 Ensure all columns have the same length
    for key, value in cashflows.items():
        if len(value) != len(dias_cupon):
            raise ValueError(f"Column '{key}' has inconsistent length!")

    return pd.DataFrame(cashflows)
