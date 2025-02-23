import pandas as pd
from math import pow
from datetime import date
from logic.renta_fija_logic import (
    generar_fechas,
    calcular_diferencias_fechas_pago_cupon,
    calcular_numero_dias_descuento_cupon,
    convertir_tasa_cupon,
    calcular_cupones_futuros_cf,
    calcular_vp_cfs,
    calcular_flujo_pesos,
)


def generar_cashflows_df(
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
        periodicidad=periodo_cupon,
        modalidad=base_intereses,
    )
    dias_cupon = calcular_diferencias_fechas_pago_cupon(lista_fechas=fechas_cupon)
    dias_descuento_cupon = calcular_numero_dias_descuento_cupon(
        fecha_negociacion=fecha_negociacion, lista_fechas_pago_cupon=fechas_cupon
    )
    tasa_convertida = convertir_tasa_cupon(
        base_dias_anio=base_intereses,
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
        base_anio=base_intereses,
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


def cupon_corrido_calc(df: pd.DataFrame, date_negociacion: date):

    # Convert the date_negociacion to a pandas Timestamp
    target_date = pd.to_datetime(date_negociacion, format="%d/%m/%Y")

    # Ensure the 'Fechas Cupón' column is in datetime format
    df["Fechas Cupón"] = pd.to_datetime(df["Fechas Cupón"], format="%d/%m/%Y")

    # Filter dates that are less than or equal to the target date
    valid_rows = df[df["Fechas Cupón"] <= target_date]

    # Return the minimum valid date and the 'rate' column
    if not valid_rows.empty:
        # caclualte the cupon corrido
        cupon_corrido = 0
        min_date_row = valid_rows.loc[valid_rows["Fechas Cupón"].idxmax()]
        date_difference = (target_date - min_date_row["Fechas Cupón"]).days

        # defaults to the first cupon when negociacion date is less than the first cupon date
        if min_date_row["Días Cupón"] == 0:
            cupon_corrido = (df["CFt"][1] / df["Días Cupón"][1]) * date_difference
        else:
            cupon_corrido = (
                min_date_row["CFt"] / min_date_row["Días Cupón"]
            ) * date_difference

        return cupon_corrido
    else:
        return None  # Return None if no valid date is found


def clasificar_precio_limpio(precio_limpio: float):
    """
    Clasifica el precio según su valor en relación con 100.

    Parámetros:
        precio_limpio (float): El precio a evaluar.

    Retorna:
        str: Una cadena que indica la categoría del precio.
    """
    if precio_limpio == 100:
        return "Precio a la par. \n Se negocia exactamente a su valor nominal."
    elif precio_limpio < 100:
        return "Precio al descuento. \n Se negocia por debajo de su valor nominal."
    else:
        return "Precio con prima. \n Se negocia por encima de su valor nominal."
