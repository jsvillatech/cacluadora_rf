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
            # Ajuste según la convención 30/360
            dia = min(30, fecha_actual.day)  # Si el día es 31, lo ajustamos a 30
            if periodicidad == "Mensual":
                fecha_actual = fecha_actual.replace(day=dia) + relativedelta(months=1)
            elif periodicidad == "Trimestral":
                fecha_actual = fecha_actual.replace(day=dia) + relativedelta(months=3)
            elif periodicidad == "Semestral":
                fecha_actual = fecha_actual.replace(day=dia) + relativedelta(months=6)
            elif periodicidad == "Anual":
                fecha_actual = fecha_actual.replace(day=dia) + relativedelta(years=1)
            else:
                raise ValueError(
                    "Periodicidad no válida. Usa 'Mensual', 'Trimestral', 'Semestral' o 'Anual'."
                )

        else:
            raise ValueError("Modalidad no válida. Usa '30/360' o '365/365' días.")

    return lista_fechas


def calcular_diferencias_fechas_pago_cupon(lista_fechas: list[str], modalidad: str):
    """
    Calcula la diferencia en días entre fechas consecutivas de una lista de fechas (Pago Cupon)
    usando la convención 30/360 o 365/365.

    Args:
        lista_fechas (list[str]): Lista de fechas en formato 'DD/MM/YYYY'.
        modalidad (str): Modalidad del cálculo ('30/360' o '365/365').

    Returns:
        list[int]: Lista de diferencias en días entre fechas consecutivas.
    """
    if len(lista_fechas) < 2:
        return []

    # Convertimos la lista de fechas a objetos datetime
    fechas = [pd.to_datetime(fecha, format="%d/%m/%Y") for fecha in lista_fechas]

    diferencias_list = [
        0
    ]  # Se agrega un 0 al inicio para coincidir con la cantidad de cupones

    for i in range(1, len(fechas)):
        fecha_anterior = fechas[i - 1]
        fecha_actual = fechas[i]

        if modalidad == "365/365":
            # Cálculo exacto de diferencia real en días
            diferencia = (fecha_actual - fecha_anterior).days

        elif modalidad == "30/360":
            # Extraemos año, mes y día y ajustamos a la convención 30/360
            Y1, M1, D1 = (
                fecha_anterior.year,
                fecha_anterior.month,
                min(30, fecha_anterior.day),
            )
            Y2, M2, D2 = (
                fecha_actual.year,
                fecha_actual.month,
                min(30, fecha_actual.day),
            )

            # Aplicamos la fórmula 30/360
            diferencia = (Y2 - Y1) * 360 + (M2 - M1) * 30 + (D2 - D1)

        else:
            raise ValueError("Modalidad no válida. Usa '30/360' o '365/365'.")

        diferencias_list.append(diferencia)

    return diferencias_list


def calcular_numero_dias_descuento_cupon(
    fecha_negociacion: datetime, lista_fechas_pago_cupon: list[str]
):
    """
    Calcula la diferencia en días entre una fecha de negociación y una lista de fechas,
    ignorando años bisiestos (29 de febrero).

    Parámetros:
    fecha_negociacion (datetime.date): Fecha de negociación.
    lista_fechas_pago_cupon (list): Lista de fechas en formato 'DD/MM/YYYY'.

    Retorna:
    list[int]: Lista con la diferencia en días ignorando los bisiestos.
    """
    # Convertir `fecha_negociacion` a datetime completo
    fecha_negociacion_dt = datetime.combine(fecha_negociacion, datetime.min.time())
    fecha_negociacion_365 = (fecha_negociacion_dt.year * 365) + (
        fecha_negociacion_dt.timetuple().tm_yday
        - (
            1
            if fecha_negociacion_dt.month > 2 and fecha_negociacion_dt.year % 4 == 0
            else 0
        )
    )

    diferencias = []

    for fecha in lista_fechas_pago_cupon:
        fecha_dt = datetime.strptime(fecha, "%d/%m/%Y")
        fecha_365 = (fecha_dt.year * 365) + (
            fecha_dt.timetuple().tm_yday
            - (1 if fecha_dt.month > 2 and fecha_dt.year % 4 == 0 else 0)
        )
        diferencias.append(max(0, fecha_365 - fecha_negociacion_365))

    # Ensure the first element is 0
    diferencias[0] = 0

    return diferencias


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
    lista_dias_descuento: list[int],
):
    """
    Calcula el valor presente de una lista de cupones futuros descontados a la fecha de negociación.

    Parámetros:
    - lista_cfs (list[float]): Lista de flujos de caja futuros.
    - tasa_mercado (float): Tasa efectiva anual en decimal.
    - lista_dias_descuento (list[int]): Lista de días de descuento para cada flujo de caja.

    Retorna:
    - list[float]: Lista con los valores presentes de cada flujo de caja.
    """

    tasa_mercado = tasa_mercado / 100

    vp_cfs = [
        CFt
        / pow(1 + tasa_mercado, dias / 365)  # siempre por 365 ya sea 365/365 o 30/360
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
    flujo_pesos = [round(CFt, 3) / 100 * valor_nominal for CFt in lista_cfs]
    return flujo_pesos


def convertir_nominal_a_efectiva_anual(tasa_nominal_negociacion: float, periodo: str):
    """
    Convierte una tasa nominal a tasa efectiva anual (EA).
    :param tasa_nominal: Tasa nominal en porcentaje (ej. 18.1 para 18.1%)
    :param periodo: Periodicidad de la tasa ('mensual', 'trimestral', 'semestral', 'anual')
    :return: Tasa efectiva anual en porcentaje
    """
    periodos_por_año = {
        "Mensual": 12,
        "Trimestral": 4,
        "Semestral": 2,
        "Anual": 1,  # Si es anual, la tasa nominal ya es efectiva
    }

    if periodo not in periodos_por_año:
        raise ValueError(
            "El periodo debe ser 'mensual', 'trimestral', 'semestral' o 'anual'"
        )

    n = periodos_por_año[periodo]

    if n == 1:
        return tasa_nominal_negociacion  # Si es anual, ya es efectiva

    # Convertir tasa nominal a decimal y calcular efectiva anual
    tasa_efectiva_anual = (1 + (tasa_nominal_negociacion / 100) / n) ** n - 1

    return tasa_efectiva_anual * 100  # Convertir a porcentaje


def tir_a_ea(tir: float, periodo: str):
    """
    Convierte una TIR en una Tasa Efectiva Anual (EA).

    Parámetros:
    tir (float): TIR en porcentaje (ejemplo: 1.45 para 1.45%)
    periodo (str): Periodo de la TIR. Opciones: 'Mensual', 'Trimestral', 'Semestral', 'Anual'

    Retorna:
    float: Tasa Efectiva Anual en porcentaje
    """
    tir_decimal = tir / 100  # Convertir a decimal

    if periodo == "Mensual":
        ea = (1 + tir_decimal) ** 12 - 1
    elif periodo == "Trimestral":
        ea = (1 + tir_decimal) ** 4 - 1
    elif periodo == "Semestral":
        ea = (1 + tir_decimal) ** 2 - 1
    elif periodo == "Anual":
        ea = (1 + tir_decimal) ** 1 - 1
    else:
        raise ValueError("El periodo debe ser 'mensual', 'trimestral' o 'semestral'")

    return ea * 100  # Convertir a porcentaje sin redondear
