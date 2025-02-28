import datetime
import pandas as pd
from data_handling.shared_data import filtrar_por_fecha


def procesar_fechas(lista_fechas, fecha_neg, archivo, spread, periodicidad):

    periodos_por_anio = {"Mensual": 12, "Trimestral": 4, "Semestral": 2, "Anual": 1}
    # Llamar a la función filtrar_por_fecha con los parámetros requeridos
    df_filtrado = filtrar_por_fecha(
        archivo=archivo, nombre_hoja="IPC Estimado", fechas_filtro=lista_fechas
    )
    spread = spread / 100
    # Filtrar todas las fechas mayores a fecha_neg
    filtrado_neg = df_filtrado[
        pd.to_datetime(df_filtrado["Fecha"]) > pd.Timestamp(fecha_neg)
    ].copy()

    # Obtener el valor del rate de la fecha anterior a la primera fecha en filtrado_neg
    primera_fecha = filtrado_neg["Fecha"].min()
    rate_anterior = (
        df_filtrado.loc[df_filtrado["Fecha"] < primera_fecha, "IPC estimado"].values[-1]
        if not df_filtrado[df_filtrado["Fecha"] < primera_fecha].empty
        else None
    )
    # Desplazar los valores de rate hacia abajo
    filtrado_neg["IPC estimado"] = filtrado_neg["IPC estimado"].shift(1)

    # Reemplazar el rate de la primera fecha con el rate_anterior
    filtrado_neg.loc[filtrado_neg["Fecha"] == primera_fecha, "IPC estimado"] = (
        rate_anterior
    )

    # Sumar el spread a cada valor de rate
    filtrado_neg["IPC estimado"] = filtrado_neg["IPC estimado"] + spread

    # Convertir las fechas a formato "DD/MM/YYYY"
    fechas_str = filtrado_neg["Fecha"].dt.strftime("%d/%m/%Y").tolist()
    tasas = filtrado_neg["IPC estimado"].tolist()

    # periodo
    tasas = [
        tasas[i] / periodos_por_anio[periodicidad] for i in range(0, len(fechas_str))
    ]

    # Retornar listas con las fechas como strings y las tasas ajustadas
    return fechas_str, tasas
