import requests
import datetime
import pandas as pd
import holidays
from data_handling.shared_data import filtrar_por_fecha

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


def convertir_tasa_cupon_ibr(
    base_dias_anio: str,
    periodicidad: str,
    tasa_anual_cupon: float,
    lista_fechas: list[str],
    fecha_inicio: datetime.date,
    fecha_negociacion: datetime.date,
    archivo=None,
):
    """
    Convierte una tasa nominal anual a una nominal en otra periodicidad.

    Parámetros:
    base_dias_anio (str): Base de cálculo de días ('30/360' o '365/365').
    periodicidad (str): Periodo de conversión ('Mensual', 'Trimestral', 'Semestral', 'Anual').
    tasa_anual_cupon (float): Tasa anual expresada en decimal (Ej: 10% -> 0.10).
    lista_fechas (list[str]): Lista de fechas de cada cupón en formato 'DD/MM/YYYY'.
    fecha_inicio (datetime.date): Fecha de inicio para la consulta de tasas IBR.
    fecha_negociacion (datetime.date): Fecha de negociación en formato 'DD/MM/YYYY'.
    archivo (str, opcional): Nombre del archivo Excel que contiene las tasas IBR.

    Retorna:
    list[float]: Lista de tasas convertidas a la periodicidad especificada.
    """
    tasa_anual_cupon = tasa_anual_cupon / 100

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

    # Convertir lista de fechas a objetos datetime y calcular fechas reales de IBR
    fechas_cupones = [
        datetime.datetime.strptime(f, "%d/%m/%Y").date() for f in lista_fechas
    ]
    fechas_reales_ibr = [fecha_publicacion_ibr(f) for f in fechas_cupones]

    # Obtener tasas IBR en batch
    if archivo is None:
        tasas_ibr = fetch_ibr_data_banrep(
            fecha_inicio=min(fechas_reales_ibr), fecha_fin=max(fechas_reales_ibr)
        )
    else:
        tasas_ibr = filtrar_por_fecha(
            archivo=archivo, nombre_hoja="IBR Estimada", fechas_filtro=fechas_reales_ibr
        )

    # Asegurar que tasas_ibr es una serie o lista antes de dividir
    if isinstance(tasas_ibr, pd.DataFrame):
        if tasas_ibr.empty:
            raise ValueError(
                "No se encontraron datos IBR en el rango de fechas especificado."
            )
        tasas_ibr = tasas_ibr.iloc[:, 1]

    # Convertir a diccionario asegurando que la estructura es correcta
    tasas_ibr_dict = dict(zip(fechas_reales_ibr, tasas_ibr.astype(float) / 100))

    ### CASO 1: La fecha de negociación es la misma que la de emisión ###
    if fecha_inicio == fecha_negociacion:
        fecha_real_ibr = fecha_publicacion_ibr(fecha_inicio)
        tasa_ibr_real = tasas_ibr_dict.get(fecha_real_ibr, None)

        if tasa_ibr_real is None:
            raise ValueError(
                f"No se encontró la tasa IBR para la fecha: {fecha_real_ibr}."
            )

        tasa_ibr_spread = tasa_ibr_real + tasa_anual_cupon
        tasas = [
            tasa_ibr_spread / periodos_por_anio[periodicidad] for _ in lista_fechas
        ]
        tasas[0] = 0  # El primer cupón tiene tasa 0 por convención
        return tasas

    ### CASO 2: El título se negocia después de su emisión ###
    else:
        tasas = []

        # Obtener IBR del día anterior a la fecha de emisión para el primer cupón
        fecha_real_ibr_1 = fecha_publicacion_ibr(fecha_inicio)
        tasa_ibr_1 = tasas_ibr_dict.get(fecha_real_ibr_1, None)

        if tasa_ibr_1 is None:
            raise ValueError(
                f"No se encontró la tasa IBR para la fecha: {fecha_real_ibr_1}."
            )

        # Calcular la tasa para el primer cupón
        tasa_ibr_spread_1 = tasa_ibr_1 + tasa_anual_cupon
        tasas.append(0)  # Se agrega 0 porque es el valor de la tasa en el primer cupón
        tasas.append(tasa_ibr_spread_1 / periodos_por_anio[periodicidad])

        # Obtener IBR del día anterior a la fecha de negociación para los siguientes cupones
        for i in range(2, len(lista_fechas)):
            fecha_real_ibr_i = fechas_reales_ibr[i]
            tasa_ibr_i = tasas_ibr_dict.get(fecha_real_ibr_i, None)

            if tasa_ibr_i is None:
                raise ValueError(
                    f"No se encontró la tasa IBR para la fecha: {fecha_real_ibr_i}."
                )

            tasa_ibr_spread_i = tasa_ibr_i + tasa_anual_cupon
            tasas.append(tasa_ibr_spread_i / periodos_por_anio[periodicidad])

        return tasas


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


def jueves_anterior(fecha: datetime.date) -> datetime.date:
    """
    Retorna el jueves anterior (o la misma fecha si ya es jueves).
    """
    fecha_aux = fecha
    while fecha_aux.weekday() != 3:  # 3 = Jueves
        fecha_aux -= datetime.timedelta(days=1)
    return fecha_aux


def viernes_anterior(fecha: datetime.date) -> datetime.date:
    """
    Retorna el viernes anterior (o el mismo viernes si 'fecha' fuera viernes).
    """
    fecha_aux = fecha
    while fecha_aux.weekday() != 4:  # 4 = Viernes
        fecha_aux -= datetime.timedelta(days=1)
    return fecha_aux


def fecha_publicacion_ibr(fecha_objetivo: datetime.date) -> datetime.date:
    """
    Dada una fecha 'fecha_objetivo', determina la fecha de publicación del IBR
    según las reglas:

    1) El IBR publicado el viernes (11:00 a.m.) rige para el lunes siguiente.
       - Si el lunes NO es día hábil bancario, ese IBR del viernes rige para el martes.

    2) Durante un fin de semana habitual (viernes, sábado, domingo),
       se usa la tasa publicada el jueves anterior (11:00 a.m.).

    3) Si el lunes es festivo, se usa la tasa publicada el jueves anterior.

    4) Para martes, miércoles y jueves “normales” (sin ser festivos intercalados),
       se asume que se usa la tasa publicada el día hábil anterior.
    """
    dia_semana = fecha_objetivo.weekday()  # Lunes=0, Martes=1, ..., Domingo=6

    # ---------------------------
    # CASO: Viernes, Sábado, Domingo
    # => Tasa del jueves anterior
    # ---------------------------
    if dia_semana in (4, 5, 6):
        return jueves_anterior(fecha_objetivo)

    # ---------------------------
    # CASO: Lunes
    # ---------------------------
    if dia_semana == 0:
        # ¿Es día hábil o festivo?
        if not es_dia_habil_bancario(fecha_objetivo):
            # Lunes festivo => jueves anterior
            return jueves_anterior(fecha_objetivo)
        else:
            # Lunes hábil => viernes anterior
            return viernes_anterior(fecha_objetivo)

    # ---------------------------
    # CASO: Martes
    # ---------------------------
    if dia_semana == 1:
        # Revisamos si el lunes anterior fue festivo
        fecha_lunes = fecha_objetivo - datetime.timedelta(days=1)
        if not es_dia_habil_bancario(fecha_lunes):
            # Si el lunes no fue hábil => tasa del viernes anterior
            return viernes_anterior(fecha_objetivo)
        else:
            # Si fue hábil => tasa del día hábil anterior (lunes)
            return dia_habil_anterior(fecha_objetivo)

    # ---------------------------
    # CASO: Miércoles o Jueves
    # => Tasa del día hábil anterior
    # ---------------------------
    return dia_habil_anterior(fecha_objetivo)
