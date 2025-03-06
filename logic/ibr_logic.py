import datetime

import holidays
import pandas as pd
import requests

from data_handling.shared_data import filtrar_por_fecha
from logic.shared_logic import (
    calcular_fecha_anterior,
    convertir_tasa_nominal_a_efectiva_anual,
    sumar_tasas,
)
from utils.helper_functions import shift_list_with_replacement

co_holidays = holidays.Colombia()  # Festivos en Colombia


def fetch_ibr_data_banrep(fecha_inicio: datetime.date, fecha_fin: datetime.date):
    """
    Fetches series data from the Banco de la República API for the given date range and extracts only the data field.

    Parameters:
        fecha_inicio (datetime.date): The start date.
        fecha_fin (datetime.date): The end date.

    Returns:
        pd.DataFrame: A DataFrame containing the date and the corresponding IBR value.
    """
    url = "https://suameca.banrep.gov.co/buscador-de-series/rest/buscadorSeriesRestService/consultaDatosSeries"

    # Convert dates to the required format (YYYYMMDD)
    fecha_inicio_str = fecha_inicio.strftime("%Y%m%d")
    fecha_fin_str = fecha_fin.strftime("%Y%m%d")

    # JSON payload
    payload = {
        "series": [{"idPeriodicidades": [1], "idSerie": 242}],
        "fechaInicio": int(fecha_inicio_str),
        "fechaFin": int(fecha_fin_str),
    }

    headers = {"Content-Type": "application/json"}

    try:
        # Make the POST request
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        # Extract and transform the data field into a DataFrame
        json_response = response.json()
        data = json_response[0].get("data", []) if json_response else []

        if not data:
            return pd.DataFrame(columns=["Fecha", "Tasa_ibr_mes_nominal"])

        df = pd.DataFrame(data, columns=["Unix_Timestamp", "Tasa_ibr_mes_nominal"])
        df["Fecha"] = pd.to_datetime(df["Unix_Timestamp"], unit="ms").dt.normalize()
        df = df[["Fecha", "Tasa_ibr_mes_nominal"]]

        return df
    except requests.RequestException:
        raise Exception("Sorry, something went wrong, try again later")


def obtener_tasa_ibr_real(fecha: datetime.date, archivo):
    """
    Procesa una única fecha llamando a `filtrar_por_fecha` si hay un archivo,
    o `fetch_ibr_data_banrep` si no lo hay.

    :param fecha_negociacion: str, fecha en formato 'DD/MM/YYYY'.
    :param archivo: str (opcional), ruta del archivo si los datos vienen de ahí.
    :return: float, valor de la tasa IBR si existen datos; de lo contrario, lanza una excepción.
    """
    ibr_fecha_real = fecha_publicacion_ibr(fecha)

    if archivo:
        df = filtrar_por_fecha(archivo, "IBR Estimada", [ibr_fecha_real])
    else:
        df = fetch_ibr_data_banrep(ibr_fecha_real, ibr_fecha_real)

    if df.empty:
        raise ValueError(f"No existen datos para la fecha {ibr_fecha_real}")

    return df.iloc[0, 1]  # Retorna el valor numérico de la tasa IBR


def obtener_tasa_ibr_real_batch(lista_fechas: list[datetime.date], archivo):
    """
    Procesa una lista de fechas llamando a `filtrar_por_fecha` si hay un archivo,
    o `fetch_ibr_data_banrep` si no lo hay.

    :param lista_fechas: list, lista de fechas en formato 'DD/MM/YYYY'.
    :param archivo: str (opcional), ruta del archivo si los datos vienen de ahí.
    :return: list, valores de la tasa IBR si existen datos; de lo contrario, lanza una excepción.
    """
    ibr_fechas_reales = [fecha_publicacion_ibr(fecha) for fecha in lista_fechas]
    # Convertir a DataFrame para hacer la unión
    ibr_fechas_df = pd.DataFrame({"Fecha": ibr_fechas_reales})

    if archivo:
        df = filtrar_por_fecha(archivo, "IBR Estimada", ibr_fechas_reales)
    else:
        df = fetch_ibr_data_banrep(min(ibr_fechas_reales), max(ibr_fechas_reales))

    if df.empty:
        raise ValueError(f"No existen datos para las fechas {ibr_fechas_reales}")

    # Asegurarse de que la columna de fechas tenga el mismo tipo
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    ibr_fechas_df["Fecha"] = pd.to_datetime(ibr_fechas_df["Fecha"])

    # Realizar la intersección (inner join)
    df = df.merge(ibr_fechas_df, on="Fecha", how="inner")

    if df.empty:
        raise ValueError(
            f"No hay fechas en común entre los datos disponibles y {ibr_fechas_reales}"
        )

    return df.iloc[:, 1].tolist()  # Retorna una lista con los valores de la tasa IBR


def obtener_tasa_negociacion_EA(
    tasa_mercado: float,
    fecha_negociacion: datetime.date,
    archivo_subido,
    periodo_cupon: str,
    modalidad: str,
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
    periodo_cupon : str
        Períodos del cupón en el año (por ejemplo, 'Mesual','Trimestral', 'Semestral').
    modalidad: str
        "Nominal" o "EA" para indicar el tipo de tasa.

    Retorna:
    --------
    float
        Tasa efectiva anual (EA) ajustada con el spread de negociación del IBR.
    """

    tasa_ibr_spread_negociacion = sumar_spread_ibr(
        tasa_spread=tasa_mercado,
        fecha=fecha_negociacion,
        modalidad=modalidad,
        archivo=archivo_subido,
    )
    tasa_negociacion_efectiva = convertir_tasa_nominal_a_efectiva_anual(
        tasa_nominal_negociacion=tasa_ibr_spread_negociacion, periodo=periodo_cupon
    )

    return tasa_negociacion_efectiva


def sumar_spread_ibr(
    tasa_spread: float,
    fecha: datetime.date,
    modalidad: str,
    archivo=None,
):
    """
    Calcula la tasa total IBR sumando la tasa spread a la tasa IBR real
    obtenida desde el Banco de la República o desde un archivo de proyecciones.

    Parámetros:
        tasa_spread (float): La tasa adicional que se suma a la tasa IBR.
        fecha (datetime.date): La fecha de la negociación.
        archivo (optional): Archivo con datos de proyección. Si es None, se usa data en línea.
        modalidad: str, "Nominal" o "EA" para indicar el tipo de tasa.

    Retorna:
        float: la tasa IBR completa (spread+IBR)

    Excepciones:
        Exception: Si ocurre un error al obtener la tasa IBR o si no hay datos disponibles.
    """
    try:
        tasa_ibr_real = obtener_tasa_ibr_real(fecha=fecha, archivo=archivo)

        # Sumar la tasa de negociación a la tasa IBR real
        tasa_ibr_spread = sumar_tasas(
            tasa1=tasa_ibr_real, tasa2=tasa_spread, modalidad=modalidad
        )

        return tasa_ibr_spread

    except Exception as e:
        raise Exception(f"Error al calcular la tasa de negociación IBR: {str(e)}")


def sumar_spread_ibr_batch(
    tasa_spread: float,
    lista_fechas: list[datetime.date],
    modalidad: str,
    archivo=None,
):
    """
    Calcula la tasa total IBR sumando la tasa spread a la tasa IBR real
    obtenida desde el Banco de la República o desde un archivo de proyecciones.

    Parámetros:
        tasa_spread (float): La tasa adicional que se suma a la tasa IBR.
        lista_fechas (list[datetime.date]): La fecha de la negociación.
        archivo (optional): Archivo con datos de proyección. Si es None, se usa data en línea.
        modalidad: str, "Nominal" o "EA" para indicar el tipo de tasa.

    Retorna:
        list[float]: la tasa IBR completa (spread+IBR)

    Excepciones:
        Exception: Si ocurre un error al obtener la tasa IBR o si no hay datos disponibles.
    """
    try:
        tasa_ibr_real = obtener_tasa_ibr_real_batch(
            lista_fechas=lista_fechas, archivo=archivo
        )

        # Sumar la tasa de negociación a la tasa IBR real
        tasa_ibr_spread = [
            sumar_tasas(tasa1=ibr, tasa2=tasa_spread, modalidad=modalidad)
            for ibr in tasa_ibr_real
        ]

        return tasa_ibr_spread

    except Exception as e:
        raise Exception(f"Error al calcular la tasa de negociación IBR: {str(e)}")


def procesar_tasa_cupon_ibr_datos(
    base_dias_anio: str,
    periodicidad: str,
    tasa_anual_cupon: float,
    lista_fechas: list[str],
    fecha_negociacion: datetime.date,
    modalidad: str,
    archivo,
):
    """
    Procesa una tasa Spread Cupon. Método online.

    Parámetros:
    base_dias_anio (str): Base de cálculo de días ('30/360' o '365/365').
    periodicidad (str): Periodo de conversión ('Mensual', 'Trimestral', 'Semestral', 'Anual').
    tasa_anual_cupon (float): Tasa anual expresada en decimal (Ej: 10% -> 0.10).
    lista_fechas (list[str]): Lista de fechas de cada cupón en formato 'DD/MM/YYYY'.
    modalidad: str, "Nominal" o "EA" para indicar el tipo de tasa.
    fecha_negociacion (datetime.date): Fecha de negociación en formato 'DD/MM/YYYY'.

    Retorna:
    list[float]: Lista de tasas convertidas a la periodicidad especificada.
    """

    base = {"30/360": 360, "365/365": 365}
    periodos_por_anio = {"Mensual": 12, "Trimestral": 4, "Semestral": 2, "Anual": 1}

    if not lista_fechas:
        raise ValueError("La lista de fechas de cupones está vacía.")

    if periodicidad not in periodos_por_anio:
        raise ValueError(
            "Periodicidad no válida. Usa: 'Mensual', 'Trimestral', 'Semestral' o 'Anual'."
        )

    if base_dias_anio not in base:
        raise ValueError("Base no válida. Usa '30/360' o '365/365'.")

    tasas = []

    # Convertir lista de fechas a objetos datetime
    fechas_cupones = [
        datetime.datetime.strptime(f, "%d/%m/%Y").date() for f in lista_fechas
    ]

    # Fecha del Periodo anterior (inicio del cupon actual)
    fecha_per_anterior = calcular_fecha_anterior(
        fecha=min(fechas_cupones),
        periodicidad=periodicidad,
        base_intereses=base_dias_anio,
        num_per=1,
    )
    tasa_per_anterior = sumar_spread_ibr(
        tasa_spread=tasa_anual_cupon,
        fecha=fecha_per_anterior,
        modalidad=modalidad,
        archivo=archivo,
    )

    # Calcular la tasa para el primer cupón
    tasa_ibr_spread_1 = (tasa_per_anterior) / 100
    tasas.append(tasa_ibr_spread_1 / periodos_por_anio[periodicidad])

    # Obtener IBR del día anterior a la fecha de negociación para los siguientes cupones
    ibr_negociacion = sumar_spread_ibr(
        tasa_spread=tasa_anual_cupon,
        fecha=fecha_negociacion,
        modalidad=modalidad,
        archivo=archivo,
    )
    for _ in range(1, len(lista_fechas)):
        tasa_ibr_spread_i = (ibr_negociacion) / 100
        tasas.append(tasa_ibr_spread_i / periodos_por_anio[periodicidad])

    return tasas


def procesar_tasa_flujos_real_ibr(
    base_dias_anio: str,
    periodicidad: str,
    tasa_anual_cupon: float,
    lista_fechas: list[str],
    modalidad: str,
    archivo,
):
    """
    Procesa una tasa Spread Cupon. Método online.

    Parámetros:
    base_dias_anio (str): Base de cálculo de días ('30/360' o '365/365').
    periodicidad (str): Periodo de conversión ('Mensual', 'Trimestral', 'Semestral', 'Anual').
    tasa_anual_cupon (float): Tasa anual expresada en decimal (Ej: 10% -> 0.10).
    lista_fechas (list[str]): Lista de fechas de cada cupón en formato 'DD/MM/YYYY'.
    modalidad: str, "Nominal" o "EA" para indicar el tipo de tasa.
    fecha_negociacion (datetime.date): Fecha de negociación en formato 'DD/MM/YYYY'.

    Retorna:
    list[float]: Lista de tasas convertidas a la periodicidad especificada.
    """

    base = {"30/360": 360, "365/365": 365}
    periodos_por_anio = {"Mensual": 12, "Trimestral": 4, "Semestral": 2, "Anual": 1}

    if not lista_fechas:
        raise ValueError("La lista de fechas de cupones está vacía.")

    if periodicidad not in periodos_por_anio:
        raise ValueError(
            "Periodicidad no válida. Usa: 'Mensual', 'Trimestral', 'Semestral' o 'Anual'."
        )

    if base_dias_anio not in base:
        raise ValueError("Base no válida. Usa '30/360' o '365/365'.")

    tasas_final = []

    # Convertir lista de fechas a objetos datetime
    fechas_cupones = [
        datetime.datetime.strptime(f, "%d/%m/%Y").date() for f in lista_fechas
    ]

    # Fecha del Periodo anterior (inicio del cupon actual)
    fecha_per_anterior = calcular_fecha_anterior(
        fecha=min(fechas_cupones),
        periodicidad=periodicidad,
        base_intereses=base_dias_anio,
        num_per=1,
    )
    tasa_per_anterior = sumar_spread_ibr(
        tasa_spread=tasa_anual_cupon,
        fecha=fecha_per_anterior,
        modalidad=modalidad,
        archivo=archivo,
    )
    tasa_fechas = sumar_spread_ibr_batch(
        tasa_spread=tasa_anual_cupon,
        lista_fechas=fechas_cupones,
        modalidad=modalidad,
        archivo=archivo,
    )
    # reemplazar por la anterior
    tasa_fechas = shift_list_with_replacement(
        tasa_fechas, shift=1, fill_value=tasa_per_anterior
    )

    # nominal
    tasas_final = [
        round((t / 100) / periodos_por_anio[periodicidad], 5) for t in tasa_fechas
    ]

    # for display
    tasa_fechas = [round(x - tasa_anual_cupon, 2) for x in tasa_fechas]

    return tasas_final, tasa_fechas


def es_dia_habil_bancario(fecha: datetime.date) -> bool:
    """Determina si 'fecha' es un día hábil bancario en Colombia."""
    # weekday(): Monday=0, Sunday=6
    if fecha.weekday() in (5, 6):  # Sábados (5) y Domingos (6) no son hábiles
        return False
    # Festivos según el calendario de Colombia
    if fecha in co_holidays:
        return False
    return True


def dia_habil_anterior(fecha: datetime.date) -> datetime.date:
    """
    Retorna el día hábil bancario anterior a 'fecha'.
    Iteramos hacia atrás (día a día) hasta encontrar un día hábil.
    """
    un_dia = datetime.timedelta(days=1)
    fecha_anterior = fecha - un_dia
    while not es_dia_habil_bancario(fecha_anterior):
        fecha_anterior -= un_dia
    return fecha_anterior


def jueves_habil_anterior(fecha: datetime.date) -> datetime.date:
    """
    Retorna el día que HARÍA las veces de 'jueves' de publicación.
    1) Encuentra el jueves de calendario anterior (o el mismo si ya es jueves).
    2) Si ese jueves no es hábil, retrocede hasta un día hábil (sea miércoles, martes...).
    """
    fecha_aux = fecha
    while fecha_aux.weekday() != 3:  # 3 = jueves
        fecha_aux -= datetime.timedelta(days=1)
    while not es_dia_habil_bancario(fecha_aux):
        fecha_aux -= datetime.timedelta(days=1)
    return fecha_aux


def viernes_habil_anterior(fecha: datetime.date) -> datetime.date:
    """
    Retorna el día que HARÍA las veces de 'viernes' de publicación.
    1) Ubica el viernes de calendario anterior (o el mismo 'fecha' si cae en viernes).
    2) Si ese viernes es festivo / no hábil, retrocede hasta encontrar un día hábil.
    """
    # 1) Llevar 'fecha_aux' al viernes de calendario anterior (o igual si ya es viernes)
    fecha_aux = fecha
    while fecha_aux.weekday() != 4:  # 4 = viernes
        fecha_aux -= datetime.timedelta(days=1)
    # 2) Si ese viernes no es hábil, retrocedemos (aunque ya no sea viernes)
    while not es_dia_habil_bancario(fecha_aux):
        fecha_aux -= datetime.timedelta(days=1)
    return fecha_aux


def fecha_publicacion_ibr(fecha_objetivo: datetime.date) -> datetime.date:
    dia_semana = fecha_objetivo.weekday()  # Lunes=0, Martes=1, ...

    # Viernes, Sábado, Domingo -> usa el jueves_habil_anterior
    if dia_semana in (4, 5, 6):
        return jueves_habil_anterior(fecha_objetivo)

    # Lunes
    if dia_semana == 0:
        if not es_dia_habil_bancario(fecha_objetivo):
            # Lunes festivo => jueves_habil_anterior
            return jueves_habil_anterior(fecha_objetivo)
        else:
            # Lunes hábil => viernes_habil_anterior
            return viernes_habil_anterior(fecha_objetivo)

    # Martes
    if dia_semana == 1:
        # Revisamos si el lunes anterior fue festivo
        fecha_lunes = fecha_objetivo - datetime.timedelta(days=1)
        if not es_dia_habil_bancario(fecha_lunes):
            # => tasa del viernes_habil_anterior
            return viernes_habil_anterior(fecha_objetivo)
        else:
            # Si fue hábil => tasa del día hábil anterior
            return dia_habil_anterior(fecha_objetivo)

    # Miércoles o Jueves -> tasa del día hábil anterior
    return dia_habil_anterior(fecha_objetivo)
