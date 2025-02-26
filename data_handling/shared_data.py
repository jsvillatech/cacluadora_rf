import pandas as pd
from datetime import date


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

    # Convertir la columna "Fecha" a datetime.date
    df["Fecha"] = pd.to_datetime(df["Fecha"])

    # Filtrar por la lista de fechas usando isin()
    df_filtrado = df[df["Fecha"].isin(fechas_filtro)]

    return df_filtrado
