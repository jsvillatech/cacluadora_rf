import requests
import datetime
import pandas as pd
import holidays

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
    modalidad_tasa: str,
    periodicidad: str,
    tasa_anual_cupon: float,
    dias_pago_entre_cupon: list[int],
    fecha_inicio: datetime.date,
    fecha_fin: datetime.date,
    archivo=None,
):
    """
    Convierte una tasa efectiva anual (EA) o nominal anual a una tasa efectiva o nominal en otra periodicidad.

    Parámetros:
    base_dias_anio (str): Base de cálculo de días ('30/360' o '365/365').
    modalidad_tasa (str): Modalidad de la tasa ('EA' o 'Nominal').
    periodicidad (str): Periodo de conversión ('Mensual', 'Trimestral', 'Semestral', 'Anual').
    tasa_anual_cupon (float): Tasa anual expresada en decimal (Ej: 10% -> 0.10).
    dias_pago_entre_cupon (list[int]): Lista de número de días transcurridos de pago entre cupones.

    Retorna:
    list[float]: Tasa convertida a la periodicidad especificada.
    """
    tasa_anual_cupon = tasa_anual_cupon / 100

    base = {"30/360": 360, "365/365": 365}

    periodos_por_anio = {"Mensual": 12, "Trimestral": 4, "Semestral": 2, "Anual": 1}

    if not dias_pago_entre_cupon:
        raise ValueError("La lista de días de pago entre cupones está vacía.")

    if periodicidad not in periodos_por_anio:
        raise ValueError(
            "Periodicidad no válida. Usa: 'Mensual', 'Trimestral', 'Semestral' o 'Anual'."
        )

    if base_dias_anio not in base:
        raise ValueError("Base no válida. Usa '30/360' o '365/365'.")

    # Obtener datos del IBR
    if archivo is None:
        tasas = [
            tasa_anual_cupon / periodos_por_anio[periodicidad]
            for _ in dias_pago_entre_cupon
        ]
    tasas[0] = 0  # se reemplaza 0 porque es el valor de la tasa en el primer cupón

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
