from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd
from math import pow


def generar_fechas(
    fecha_inicio: datetime, fecha_fin: datetime, periodicidad: str, modalidad: str
):
    """
    Genera una lista de fechas en formato 'DD/MM/YYYY' con base en la periodicidad y modalidad especificadas.

    Args:
        fecha_inicio (datetime): Fecha inicial en formato 'DD/MM/YYYY'.
        fecha_fin (datetime): Fecha final en formato 'DD/MM/YYYY'.
        periodicidad (str): Periodicidad de generación de fechas ('Mensual', 'Trimestral', 'Semestral', 'Anual').
        modalidad (str): Modalidad del cálculo ('30/360' o '365/365' días).

    Returns:
        list[str]: Lista de fechas generadas en formato 'DD/MM/YYYY'.
    """

    lista_fechas = []
    fecha_actual = fecha_inicio

    while fecha_actual <= fecha_fin:
        lista_fechas.append(fecha_actual.strftime("%d/%m/%Y"))

        if modalidad == "365/365":
            # Usar meses naturales
            if periodicidad == "Mensual":
                fecha_actual += relativedelta(months=1)
            elif periodicidad == "Trimestral":
                fecha_actual += relativedelta(months=3)
            elif periodicidad == "Semestral":
                fecha_actual += relativedelta(months=6)
            elif periodicidad == "Anual":
                fecha_actual += relativedelta(years=1)
            else:
                raise ValueError(
                    "Periodicidad no válida. Usa 'Mensual', 'Trimestral', 'Semestral' o 'Anual'."
                )

        elif modalidad == "30/360":
            # Usar días fijos (30 días por mes, 90 por trimestre, etc.)
            if periodicidad == "Mensual":
                fecha_actual += timedelta(days=30)
            elif periodicidad == "Trimestral":
                fecha_actual += timedelta(days=90)
            elif periodicidad == "Semestral":
                fecha_actual += timedelta(days=180)
            elif periodicidad == "Anual":
                fecha_actual += timedelta(days=360)
            else:
                raise ValueError(
                    "Periodicidad no válida. Usa 'Mensual', 'Trimestral', 'Semestral' o 'Anual'."
                )
        else:
            raise ValueError("Modalidad no válida. Usa '30/360' o '365/365' días.")

    return lista_fechas


def calcular_diferencias_fechas_pago_cupon(lista_fechas: list[str]):
    """
    Calcula la diferencia en días entre fechas consecutivas de una lista de fechas (Pago Cupon).

    Args:
        lista_fechas (list[str]): Lista de fechas en formato 'DD/MM/YYYY'.

    Returns:
        list[int]: Lista de diferencias en días entre fechas consecutivas.
    """
    if len(lista_fechas) < 2:
        return []

    # Convertir a Pandas Series con tipo datetime
    fechas = pd.Series(pd.to_datetime(lista_fechas, format="%d/%m/%Y"))

    # Calcular diferencias usando diff()
    diferencias = fechas.diff().dt.days.dropna().astype(int)
    diferencias_list = diferencias.tolist()
    diferencias_list.insert(
        0, 0
    )  # Se agrega un 0 al inicio de la lista para que coincida con la cantidad de cupones

    return diferencias_list


def calcular_numero_dias_descuento_cupon(
    fecha_negociacion: datetime, lista_fechas_pago_cupon: list[str]
):
    """
    Calcula la diferencia en días entre una fecha de negociación y una lista de fechas.

    Parámetros:
    fecha_negociacion (str): Fecha de negociación en formato 'DD/MM/YYYY'.
    lista_fechas_pago_cupon (list): Lista de fechas en formato 'DD/MM/YYYY'.

    Retorna:
    list[int]: Una lista de tuplas con cada fecha y su diferencia en días con la fecha de negociación.
    """
    # Convert `fecha_negociacion` from `datetime.date` to `datetime.datetime`
    fecha_negociacion_dt = datetime.combine(fecha_negociacion, datetime.min.time())
    # Calcular diferencias
    diferencias = [
        (datetime.strptime(fecha, "%d/%m/%Y") - fecha_negociacion_dt).days
        for fecha in lista_fechas_pago_cupon
    ]
    diferencias[0] = (
        0  # Se reemplaza un 0 al inicio de la lista porque sería la fecha inicial.
    )

    return diferencias


def convertir_tasa_cupon(
    base_dias_anio: str,
    modalidad_tasa: str,
    periodicidad: str,
    tasa_anual_cupon: float,
    dias_pago_entre_cupon: list[int],
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

    if modalidad_tasa == "EA":
        tasas = [
            pow(1 + tasa_anual_cupon, dias / base[base_dias_anio]) - 1
            for dias in dias_pago_entre_cupon
        ]
        return tasas

    elif modalidad_tasa == "Nominal":
        tasas = [
            tasa_anual_cupon / periodos_por_anio[periodicidad]
            for _ in dias_pago_entre_cupon
        ]
        tasas[0] = 0  # se reemplaza 0 porque es el valor de la tasa en el primer cupón
        return tasas

    else:
        raise ValueError("Modalidad de tasa no válida. Usa 'EA' o 'Nominal'.")


def calcular_cupones_futuros_cf(
    valor_nominal_base: float, tasas_periodicas: list[float]
):
    """
    Calcula los cupones futuros de un bono basado en una lista de tasas periódicas.

    Parámetros:
    valor_nominal (float): Valor nominal del bono.
    tasas_periodicas (list[float]): Lista de tasas de cupón por período (en decimal).

    Retorna:
    list: Lista con los valores de los cupones futuros en cada período.
    """

    cupones = [valor_nominal_base * tasa for tasa in tasas_periodicas]
    cupones[-1] += valor_nominal_base  # Agregar el valor nominal al último cupón

    return cupones


def calcular_vp_cfs(
    lista_cfs: list[float],
    tasa_mercado: float,
    base_anio: str,
    lista_dias_descuento: list[int],
):
    """
    Calcula el valor presente de una lista de cupones futuros descontados a la fecha de negociación.

    Parámetros:
    - lista_cfs (list[float]): Lista de flujos de caja futuros.
    - tasa_mercado (float): Tasa efectiva anual en decimal.
    - base_anio (str): '30/360' o '365/365'.
    - lista_dias_descuento (list[int]): Lista de días de descuento para cada flujo de caja.

    Retorna:
    - list[float]: Lista con los valores presentes de cada flujo de caja.
    """

    tasa_mercado = tasa_mercado / 100

    base = {
        "30/360": 360,
        "365/365": 365,
    }

    if base_anio not in base:
        raise ValueError("Base no válida. Usa '30/360' o '365/365'.")

    vp_cfs = [
        CFt / pow(1 + tasa_mercado, dias / base[base_anio])
        for CFt, dias in zip(lista_cfs, lista_dias_descuento)
    ]

    return vp_cfs


def calcular_flujo_pesos(valor_nominal: float, lista_cfs: list[float]):
    """
    Calcula el flujo en pesos de una lista de cupones futuros.

    Parámetros:
    valor_nominal (float): Valor nominal del bono.
    lista_cfs (list): Lista de cupones futuros.

    Retorna:
    list: Lista con los valores de los flujos en pesos.
    """
    flujo_pesos = [CFt / 100 * valor_nominal for CFt in lista_cfs]
    return flujo_pesos


# Function to validate form inputs
def validate_inputs(start, end, name, age):
    """Validates form inputs and returns a list of errors (if any)."""
    errors = []

    if start < end:
        errors.append("❌ Start Date must be greater than End Date.")

    if not name.strip():
        errors.append("❌ Name cannot be empty.")

    if age < 18:
        errors.append("❌ Age must be at least 18.")

    return errors
