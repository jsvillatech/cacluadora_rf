import calendar
from datetime import datetime
from math import pow

import pandas as pd
from dateutil.relativedelta import relativedelta


def generar_fechas(
    fecha_inicio: datetime,
    fecha_fin: datetime,
    fecha_negociacion: datetime,
    periodicidad: str,
):
    """
    Genera una lista de fechas en formato 'DD/MM/YYYY' según la periodicidad indicada,
    asegurando que los meses con 31 días conserven su último día cuando corresponda.
    """
    lista_fechas = []
    fecha_actual = fecha_inicio

    while fecha_actual <= fecha_fin:
        # Solo agregamos la fecha si es > fecha_negociacion
        if fecha_actual > fecha_negociacion:
            lista_fechas.append(fecha_actual.strftime("%d/%m/%Y"))

        # Obtener el último día del mes actual
        _, ultimo_dia_mes_actual = calendar.monthrange(
            fecha_actual.year, fecha_actual.month
        )
        es_ultimo_dia_mes = fecha_actual.day == ultimo_dia_mes_actual

        # Calcular la nueva fecha basada en la periodicidad
        if periodicidad == "Mensual":
            nueva_fecha = fecha_actual + relativedelta(months=1)
        elif periodicidad == "Trimestral":
            nueva_fecha = fecha_actual + relativedelta(months=3)
        elif periodicidad == "Semestral":
            nueva_fecha = fecha_actual + relativedelta(months=6)
        elif periodicidad == "Anual":
            nueva_fecha = fecha_actual + relativedelta(years=1)
        else:
            raise ValueError(
                "Periodicidad no válida. Usa 'Mensual', 'Trimestral', 'Semestral' o 'Anual'."
            )

        # Ajustar la nueva fecha si la fecha original era el último día del mes
        if es_ultimo_dia_mes:
            _, ultimo_dia_nuevo_mes = calendar.monthrange(
                nueva_fecha.year, nueva_fecha.month
            )
            nueva_fecha = nueva_fecha.replace(day=ultimo_dia_nuevo_mes)

        fecha_actual = nueva_fecha

    return lista_fechas


def calcular_diferencias_fechas_pago_cupon(
    lista_fechas: list[str],
    periodicidad: str,
    base_intereses: str,
    ignorar_bisiesto: bool = True,
):
    """
    Calcula la diferencia en días entre fechas consecutivas de una lista de fechas (Pago Cupon)
    usando la convención 30/360 o 365/365, con opción de ignorar años bisiestos.

    Args:
        lista_fechas (list[str]): Lista de fechas en formato 'DD/MM/YYYY'.
        periodicidad (str): Periodicidad del pago.
        base_intereses (str): Base de intereses ('30/360' o '365/365').
        ignorar_bisiesto (bool): Si True, ignora el 29 de febrero en años bisiestos.

    Returns:
        list[int]: Lista de diferencias en días entre fechas consecutivas.
    """
    if len(lista_fechas) < 2:
        return []

    # Convertimos la lista de fechas a objetos datetime
    fechas = [pd.to_datetime(fecha, format="%d/%m/%Y") for fecha in lista_fechas]

    diferencias_list = []

    for i in range(0, len(fechas)):
        if i == 0:
            fecha_anterior = calcular_fecha_anterior(
                fecha=fechas[i],
                periodicidad=periodicidad,
                base_intereses=base_intereses,
                num_per=1,
            )
        else:
            fecha_anterior = fechas[i - 1]

        fecha_actual = fechas[i]

        if base_intereses == "365/365":
            # Cálculo exacto de diferencia real en días
            diferencia = (fecha_actual - fecha_anterior).days

            # 📌 Ignorar el 29 de febrero si la opción está activada
            if ignorar_bisiesto:
                for año in range(fecha_anterior.year, fecha_actual.year + 1):
                    if calendar.isleap(año):  # Verifica si es bisiesto
                        fecha_bisiesto = pd.Timestamp(year=año, month=2, day=29)
                        if fecha_anterior <= fecha_bisiesto <= fecha_actual:
                            diferencia -= 1  # Resta un día

        elif base_intereses == "30/360":
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
            raise ValueError("Base Intereses no válida. Usa '30/360' o '365/365'.")

        diferencias_list.append(diferencia)

    return diferencias_list


def calcular_numero_dias_descuento_cupon(fecha_negociacion, lista_fechas):
    """
    Calcula la diferencia en días entre una fecha de negociación y una lista de fechas.
    Si el período incluye un 29 de febrero en un año bisiesto, se resta un día adicional.

    :param fecha_negociacion: str, fecha de negociación en formato 'DD/MM/YYYY'
    :param lista_fechas: list, lista de fechas en formato 'DD/MM/YYYY'
    :return: list, diferencias en días para cada fecha de la lista
    """

    # Convertimos la fecha de negociación a datetime
    fecha_negociacion = pd.to_datetime(fecha_negociacion, format="%d/%m/%Y")
    # Convertimos las fechas de la lista a datetime
    fechas = [pd.to_datetime(fecha, format="%d/%m/%Y") for fecha in lista_fechas]

    diferencias_list = []

    for fecha_actual in fechas:
        diferencia = (fecha_actual - fecha_negociacion).days

        # Verificar si el rango de fechas incluye un 29 de febrero en un año bisiesto
        for año in range(fecha_negociacion.year, fecha_actual.year + 1):
            if calendar.isleap(año):  # Verifica si el año es bisiesto
                fecha_29_febrero = pd.Timestamp(year=año, month=2, day=29)
                if fecha_negociacion <= fecha_29_febrero <= fecha_actual:
                    diferencia -= (
                        1  # Restar un día si el período abarca el 29 de febrero
                    )

        diferencias_list.append(diferencia)

    return diferencias_list


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
    flujo_pesos = [CFt / 100 * valor_nominal for CFt in lista_cfs]
    return flujo_pesos


def convertir_tasa_nominal_a_efectiva_anual(
    tasa_nominal_negociacion: float, periodo: str
):
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


def calcular_fecha_anterior(
    fecha: datetime, periodicidad: str, base_intereses: str, num_per: int
):
    """
    Calcula una fecha anterior basada en la periodicidad, Base Intereses y número de períodos.

    Args:
        fecha (datetime): Fecha base en formato 'DD/MM/YYYY'.
        periodicidad (str): Periodicidad ('Mensual', 'Trimestral', 'Semestral', 'Anual').
        base_intereses (str): Base Intereses ('30/360' o '365/365').
        num_per (int): Número de períodos a restar.

    Returns:
        datetime: Fecha calculada.
    """
    fecha_calculada = fecha

    if base_intereses == "365/365":
        # Usar meses naturales
        if periodicidad == "Mensual":
            fecha_calculada -= relativedelta(months=num_per)
        elif periodicidad == "Trimestral":
            fecha_calculada -= relativedelta(months=3 * num_per)
        elif periodicidad == "Semestral":
            fecha_calculada -= relativedelta(months=6 * num_per)
        elif periodicidad == "Anual":
            fecha_calculada -= relativedelta(years=num_per)
        else:
            raise ValueError(
                "Periodicidad no válida. Usa 'Mensual', 'Trimestral', 'Semestral' o 'Anual'."
            )

    elif base_intereses == "30/360":
        # Ajuste según la convención 30/360
        dia = min(30, fecha.day)  # Si el día es 31, ajustarlo a 30
        if periodicidad == "Mensual":
            fecha_calculada = fecha.replace(day=dia) - relativedelta(months=num_per)
        elif periodicidad == "Trimestral":
            fecha_calculada = fecha.replace(day=dia) - relativedelta(months=3 * num_per)
        elif periodicidad == "Semestral":
            fecha_calculada = fecha.replace(day=dia) - relativedelta(months=6 * num_per)
        elif periodicidad == "Anual":
            fecha_calculada = fecha.replace(day=dia) - relativedelta(years=num_per)
        else:
            raise ValueError(
                "Periodicidad no válida. Usa 'Mensual', 'Trimestral', 'Semestral' o 'Anual'."
            )

    else:
        raise ValueError("Base Intereses no válida. Usa '30/360' o '365/365'.")

    return fecha_calculada


def sumar_tasas(tasa1: float, tasa2: float, modalidad: str):
    """
    Suma dos tasas de interés considerando su modalidad (nominal o efectiva).

    :param tasa1: float, primera tasa de interés en formato decimal (ejemplo: 0.05 para 5%).
    :param tasa2: float, segunda tasa de interés en formato decimal.
    :param modalidad: str, "Nominal" o "EA" para indicar el tipo de tasa.
    :param periodos: int, número de períodos de capitalización en un año (solo para tasas nominales).
    :return: float, tasa total sumada en el mismo formato de entrada.

    - Si la modalidad es "efectiva", se usa la fórmula de suma de tasas efectivas.
    - Si la modalidad es "nominal", se suman directamente, asumiendo que tienen la misma periodicidad.
    """
    if modalidad == "EA":
        tasa_total = ((1 + (tasa1 / 100)) * (1 + (tasa2 / 100)) - 1) * 100

    elif modalidad == "Nominal":
        tasa_total = (
            tasa1 + tasa2
        )  # Simplemente se suman si ambas son nominales con la misma periodicidad
    else:
        raise ValueError("Modalidad no válida. Usa 'nominal' o 'efectiva'.")

    return tasa_total


def restar_tasas_efectivas(tasa1: float, tasa2: float):
    """
    Resta dos tasas de interés efectivas.

    :param tasa1: float, primera tasa de interés en porcentaje.
    :param tasa2: float, segunda tasa de interés en porcentaje.
    :return: float, resultado de la resta en porcentaje.
    """

    return ((1 + tasa1) / (1 + tasa2) - 1) * 100


def calcular_t_pv_cf(vp_cft, conteo_dias_descuento, base_intereses="365/365"):
    """
    Calcula una lista de valores resultantes de multiplicar cada valor presente (VP CFt)
    por el factor de tiempo, donde el factor se obtiene dividiendo el número de días
    (de cada periodo) entre la base de intereses correspondiente (365 para "365/365" o 360 para "30/360").

    Parámetros
    ----------
    vp_cft : list of float
        Lista con los valores presentes (VP CFt) correspondientes a cada periodo.
    base_intereses : str
        String que indica la base de cálculo para el tiempo. Debe ser "365/365" o "30/360".
    conteo_dias_descuento : list of int
        Lista de días que se utilizará para el factor de tiempo (t = día / denominador).

    Retorna
    -------
    list of float
        Lista de valores calculados, donde cada elemento es el resultado de multiplicar
        vp_cft[i] por conteo_dias_descuento[i] / denominador, dependiendo de la base de intereses.

    Ejemplo
    -------
    >>> valores_vp = [1000.0, 2000.0, 3000.0]
    >>> base = "365/365"
    >>> dias = [30, 60, 90]
    >>> calcular_vp_diario(valores_vp, base, dias)
    [82.1917808219178, 164.3835616438356, 246.5753424657534]
    """
    # Verificar que las listas vp_cft y conteo_dias tengan la misma longitud
    if len(vp_cft) != len(conteo_dias_descuento):
        raise ValueError(
            "Las listas vp_cft y conteo_dias deben tener la misma longitud."
        )

    # Seleccionar el denominador en base al parámetro base_intereses
    if base_intereses == "365/365":
        denominador = 365
    elif base_intereses == "30/360":
        denominador = 360
    else:
        raise ValueError('El parámetro "base_intereses" debe ser "365/365" o "30/360".')

    # Calcular la lista resultante
    resultado = []
    for vp, dias in zip(vp_cft, conteo_dias_descuento):
        t = dias / denominador
        resultado.append(vp * t)

    return resultado


def calcular_t_pv_cf_t1(t_vp_cft, conteo_dias_descuento, base_intereses="365/365"):
    """
    Calcula una lista de valores resultantes de multiplicar cada valor presente (t*VP CFt)
    por el factor de tiempo +1, donde el factor se obtiene dividiendo el número de días
    (de cada periodo) entre la base de intereses correspondiente (365 para "365/365" o 360 para "30/360").

    Parámetros
    ----------
    t*vp_cft : list of float
        Lista con los valores presentes (VP CFt) correspondientes a cada periodo.
    base_intereses : str
        String que indica la base de cálculo para el tiempo. Debe ser "365/365" o "30/360".
    conteo_dias_descuento : list of int
        Lista de días que se utilizará para el factor de tiempo (t = día / denominador).

    Retorna
    -------
    list of float
        Lista de valores calculados, donde cada elemento es el resultado de multiplicar
        vp_cft[i] por conteo_dias_descuento[i] / denominador, dependiendo de la base de intereses.

    Ejemplo
    -------
    >>> valores_vp = [1000.0, 2000.0, 3000.0]
    >>> base = "365/365"
    >>> dias = [30, 60, 90]
    >>> calcular_vp_diario(valores_vp, base, dias)
    [82.1917808219178, 164.3835616438356, 246.5753424657534]
    """
    # Verificar que las listas vp_cft y conteo_dias tengan la misma longitud
    if len(t_vp_cft) != len(conteo_dias_descuento):
        raise ValueError(
            "Las listas vp_cft y conteo_dias deben tener la misma longitud."
        )

    # Seleccionar el denominador en base al parámetro base_intereses
    if base_intereses == "365/365":
        denominador = 365
    elif base_intereses == "30/360":
        denominador = 360
    else:
        raise ValueError('El parámetro "base_intereses" debe ser "365/365" o "30/360".')

    # Calcular la lista resultante
    resultado = []
    for t_vp_cf, dias in zip(t_vp_cft, conteo_dias_descuento):
        t = dias / denominador
        resultado.append(t_vp_cf * (t + 1))

    return resultado
