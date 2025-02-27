import datetime
import pandas as pd
from data_handling.shared_data import filtrar_por_fecha


def procesar_fechas(lista_fechas, fecha_neg, archivo, spread, periodicidad):

    periodos_por_anio = {"Mensual": 12, "Trimestral": 4, "Semestral": 2, "Anual": 1}
    # Llamar a la función filtrar_por_fecha con los parámetros requeridos
    df_filtrado = filtrar_por_fecha(
        archivo=archivo, nombre_hoja="IPC Estimada", fechas_filtro=lista_fechas
    )
    spread = spread / 100
    # Filtrar todas las fechas mayores a fecha_neg
    filtrado_neg = df_filtrado[df_filtrado["fecha"] > fecha_neg].copy()

    # Obtener el valor del rate de la fecha anterior a la primera fecha en filtrado_neg
    primera_fecha = filtrado_neg["fecha"].min()
    rate_anterior = (
        df_filtrado.loc[df_filtrado["fecha"] < primera_fecha, "rate"].values[-1]
        if not df_filtrado[df_filtrado["fecha"] < primera_fecha].empty
        else None
    )

    # Desplazar los valores de rate hacia abajo
    filtrado_neg["rate"] = filtrado_neg["rate"].shift(1)

    # Reemplazar el rate de la primera fecha con el rate_anterior
    filtrado_neg.loc[filtrado_neg["fecha"] == primera_fecha, "rate"] = rate_anterior

    # Sumar el spread a cada valor de rate
    filtrado_neg["rate"] = filtrado_neg["rate"] + spread

    # Convertir las fechas a formato "DD/MM/YYYY"
    fechas_str = filtrado_neg["fecha"].dt.strftime("%d/%m/%Y").tolist()
    tasas = filtrado_neg["rate"].tolist()

    # periodo
    tasas = [tasas[i] / periodos_por_anio[periodicidad] for i in lista_fechas]

    # Retornar listas con las fechas como strings y las tasas ajustadas
    return fechas_str, tasas
