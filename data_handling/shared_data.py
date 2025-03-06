import datetime
from datetime import date

import pandas as pd
from pyxirr import xirr

from logic.shared_logic import calcular_fecha_anterior
from utils.financial_functions import truncate


def calcular_cupon_corrido(
    df: pd.DataFrame, date_negociacion: date, periodicidad: str, base_intereses: str
):
    """
    Calcula el cupón corrido de un bono en función de la fecha de negociación.

    Parámetros:
    -----------
    df : pd.DataFrame
        DataFrame que contiene la información de los cupones, incluyendo:
        - "Fechas Cupón" (datetime): Fechas de pago de cupones.
        - "CFt" (float): Flujo de caja del cupón correspondiente.
        - "Días Cupón" (int): Número de días del período del cupón.

    date_negociacion : date
        Fecha en la que se realiza la negociación del bono.

    periodicidad : str
        Frecuencia de pago del cupón (ejemplo: "mensual", "semestral", "anual").

    base_intereses : str
        Base Intereses (str): Base Intereses del cálculo ('30/360' o '365/365' días).

    Retorna:
    --------
    float
        El valor del cupón corrido calculado.
    """

    # Convertir la fecha de negociación a un objeto Timestamp de pandas
    target_date = pd.to_datetime(date_negociacion, format="%d/%m/%Y")

    # Convertir las fechas del dataframe a un objeto Timestamp de pandas
    df["Fechas Cupón"] = pd.to_datetime(df["Fechas Cupón"], format="%d/%m/%Y")

    # Obtener la fecha del próximo cupón
    fecha_prox_cupon = df["Fechas Cupón"].min()

    # Obtener la tasa del próximo cupón
    min_cft = df.loc[df["Fechas Cupón"].idxmin(), "CFt"]

    # Obtener la cantidad de días entre cupones
    min_cupon_dias = df.loc[df["Fechas Cupón"].idxmin(), "Días Cupón"]

    # Calcular la fecha del cupón anterior
    per_anterior = calcular_fecha_anterior(
        fecha=fecha_prox_cupon,
        periodicidad=periodicidad,
        base_intereses=base_intereses,
        num_per=1,
    )

    # Calcular el número de días de intereses desde el cupón anterior hasta la fecha de negociación
    dias_intereses = day_count(
        date1=per_anterior, date2=target_date, base=base_intereses
    )

    # Calcular el cupón corrido
    cupon_corrido = (min_cft / min_cupon_dias) * dias_intereses

    return cupon_corrido


def day_count(date1: pd.Timestamp, date2: pd.Timestamp, base: str):
    """
    Retorna el número de días entre date1 y date2 según la base de conteo indicada.

    Parámetros:
    -----------
    date1 : pd.Timestamp
        Fecha inicial (anterior o igual a date2).
    date2 : pd.Timestamp
        Fecha final (posterior o igual a date1).
    base : str
        Base de conteo de días. Puede ser "30/360" o "365/365".

    Retorna:
    --------
    int
        Número de días entre date1 y date2 conforme a la convención seleccionada.
    """
    if base == "30/360":
        # Usamos la convención 30/360 US (Bond Basis).
        y1, m1, d1 = date1.year, date1.month, date1.day
        y2, m2, d2 = date2.year, date2.month, date2.day

        # Ajustes día=31 -> 30 (regla US)
        if d1 == 31:
            d1 = 30
        if d2 == 31 and d1 == 30:
            d2 = 30

        return (y2 - y1) * 360 + (m2 - m1) * 30 + (d2 - d1)

    elif base == "365/365":
        # En 365/365, retornamos la diferencia real de días de calendario.
        return (date2 - date1).days

    else:
        raise ValueError("Base de conteo no soportada. Use '30/360' o '365/365'.")


def calcular_precio_sucio_desde_VP(df, col_vp="VP CF"):
    """
    Calcula el precio sucio a partir de la columna que contiene los valores presentes de los flujos.

    Args:
        df (pandas.DataFrame): DataFrame que contiene la información de los flujos y sus valores presentes.
        col_vp (str, optional): Nombre de la columna en la que se almacenan los valores presentes de cada flujo.
                                Por defecto, "VP CF".

    Returns:
        float: El precio sucio calculado, redondeado a 3 decimales.
    """
    # Suma de la columna con los valores presentes de cada flujo
    precio_sucio = df[col_vp].sum()
    # Redondeo a 3 decimales
    precio_sucio_trunc = truncate(precio_sucio, decimals=3)

    return precio_sucio_trunc


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


def leer_datos_excel(archivo_subido, nombre_hoja: str):
    """
    Lee un archivo Excel, extrae los datos de la hoja especificada y garantiza
    que la primera columna sea una fecha en formato 'DD/MM/YYYY'.

    Parámetros:
        archivo_subido: Objeto de archivo subido desde Streamlit (st.file_uploader).
        nombre_hoja (str): Nombre de la hoja de Excel que se desea extraer.

    Retorna:
        pd.DataFrame: Un DataFrame con la primera columna como fecha y las
                      demás columnas con sus nombres originales.

    Lanza:
        ValueError: Si el archivo no se ha subido, la hoja no existe, los datos están vacíos
                    o la primera columna no tiene el formato de fecha correcto.
    """
    if archivo_subido is None:
        raise ValueError("❌ No se ha subido ningún archivo.")

    try:
        df = pd.read_excel(archivo_subido, sheet_name=nombre_hoja)
        df.columns = (
            df.columns.str.strip()
        )  # Eliminar espacios en los nombres de las columnas
    except ValueError:
        raise ValueError(
            f"❌ La hoja '{nombre_hoja}' no se encontró en el archivo Excel."
        )

    if df.empty:
        raise ValueError(f"❌ La hoja '{nombre_hoja}' está vacía.")

    # Obtener el nombre original de la primera columna
    nombre_primera_columna = df.columns[0]

    # Convertir la primera columna a formato de fecha
    df[nombre_primera_columna] = pd.to_datetime(
        df[nombre_primera_columna], format="%d/%m/%Y", errors="coerce"
    )

    # Verificar si hay valores nulos después de la conversión
    if df[nombre_primera_columna].isna().any():
        raise ValueError(
            f"❌ La primera columna '{nombre_primera_columna}' tiene valores no válidos. "
            "Asegúrate de que las fechas estén en formato 'DD/MM/YYYY'."
        )

    return df  # ✅ Retorna el DataFrame con las columnas originales


def filtrar_por_fecha(archivo, nombre_hoja: str, fechas_filtro: list):
    """
    Filtra un DataFrame cargado desde un archivo por una lista de fechas.

    Parámetros:
    - archivo: Archivo Excel a leer.
    - fechas_filtro: Lista de fechas de tipo datetime.date a buscar.
    - nombre_hoja: Nombre de la hoja de Excel que se desea

    Retorna:
    - Un DataFrame filtrado con las fechas especificadas o vacío si no hay coincidencias.
    """
    df = leer_datos_excel(archivo, nombre_hoja)  # Cargar los datos desde el archivo
    # Convertir la lista de fechas a datetime64[ns]
    fechas_filtro = pd.to_datetime(fechas_filtro)
    # Filtrar por la lista de fechas usando isin()
    df_filtrado = df[df["Fecha"].isin(fechas_filtro)]

    return df_filtrado


def calcular_tir_desde_df(
    df: pd.DataFrame,
    columna_flujos: str,
    valor_giro: float,
    fecha_negociacion: datetime.date,
):
    """
    Calcula la Tasa Interna de Retorno (TIR) a partir de un DataFrame con flujos de efectivo.

    :param df: DataFrame de pandas con los datos de flujo de efectivo.
    :param columna_flujos: Nombre de la columna que contiene los flujos de caja.
    :param valor_giro: Valor nominal inicial de la inversión (debe ser negativo).
    :param fecha_negociacion: Fecha de negociacion.
    :return: TIR en porcentaje.
    """

    fechas = df["Fechas Cupón"].tolist()
    # agregar fecha de negociacion
    fechas.insert(0, fecha_negociacion.strftime("%d/%m/%Y"))
    fechas_cupones = [datetime.datetime.strptime(f, "%d/%m/%Y").date() for f in fechas]

    # Convertir la columna de flujos de caja en una lista
    cash_flows = df[columna_flujos].tolist()
    # Agregar la inversión inicial negativa al inicio
    cash_flows.insert(0, -valor_giro)
    # Crea la lista de tuplas (fecha, monto):
    lista_de_tuplas = dict(zip(fechas_cupones, cash_flows))

    tir = xirr(lista_de_tuplas)

    return tir * 100
