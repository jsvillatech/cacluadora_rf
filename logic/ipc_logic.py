import datetime

from data_handling.shared_data import filtrar_por_fecha
from logic.shared_logic import (
    calcular_fecha_anterior,
    restar_tasas_efectivas,
    sumar_tasas,
)
from utils.helper_functions import shift_list_with_replacement


def procesar_tasa_cupon_ipc_datos(
    base_dias_anio: str,
    periodicidad: str,
    tasa_anual_cupon: float,
    lista_fechas: list[str],
    dias_cupon: list[int],
    fecha_negociacion: datetime.date,
    modalidad: str,
    archivo,
    modo_ipc: str,
):
    """
    Procesa una tasa Spread Cupon. Método online.

    Parámetros:
    base_dias_anio (str): Base de cálculo de días ('30/360' o '365/365').
    periodicidad (str): Periodo de conversión ('Mensual', 'Trimestral', 'Semestral', 'Anual').
    tasa_anual_cupon (float): Tasa anual expresada en decimal (Ej: 10% -> 0.10).
    lista_fechas (list[str]): Lista de fechas de cada cupón en formato 'DD/MM/YYYY'.
    dias_cupon (list[int]): Lista de de dias entre cupones.
    fecha_negociacion (datetime.date): Fecha de negociación en formato 'DD/MM/YYYY'.
    modalidad: str, "Nominal" o "EA" para indicar el tipo de tasa.
    archivo: archivo con las proyecciones
    modo_ipc: "Inicio" o "Final"


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

    # Convertir lista de fechas a objetos datetime
    fechas_cupones = [
        datetime.datetime.strptime(f, "%d/%m/%Y").date() for f in lista_fechas
    ]

    tasas = []

    if modo_ipc == "Inicio":
        fecha_per_anterior = calcular_fecha_anterior(
            fecha=min(fechas_cupones),
            periodicidad=periodicidad,
            base_intereses=base_dias_anio,
            num_per=1,
        )
        tasa_per_anterior = sumar_spread_ipc(
            tasa_spread=tasa_anual_cupon,
            fecha=fecha_per_anterior,
            modalidad=modalidad,
            archivo=archivo,
        )
        # Calcular la tasa para el primer cupón
        tasa_ibr_spread_1 = (tasa_per_anterior) / 100
        tasas.append(
            (1 + tasa_ibr_spread_1) ** (dias_cupon[0] / base[base_dias_anio]) - 1
        )

        # Obtener IPC del día anterior a la fecha de negociación para los siguientes cupones
        ibr_negociacion = sumar_spread_ipc(
            tasa_spread=tasa_anual_cupon,
            fecha=fecha_negociacion,
            modalidad=modalidad,
            archivo=archivo,
        )
        for dias in range(1, len(dias_cupon)):
            tasa_ibr_spread_i = (ibr_negociacion) / 100
            tasas.append(
                (1 + tasa_ibr_spread_i) ** (dias_cupon[dias] / base[base_dias_anio]) - 1
            )

    else:

        tasa_negociacion = sumar_spread_ipc(
            tasa_spread=tasa_anual_cupon,
            fecha=fecha_negociacion,
            modalidad=modalidad,
            archivo=archivo,
        )
        for dias in dias_cupon:
            tasa_ibr_spread_i = (tasa_negociacion) / 100
            tasas.append((1 + tasa_ibr_spread_i) ** (dias / base[base_dias_anio]) - 1)

    return tasas


def procesar_tasa_flujos_real_ipc(
    base_dias_anio: str,
    periodicidad: str,
    tasa_anual_cupon: float,
    lista_fechas: list[str],
    dias_cupon: list[int],
    modalidad: str,
    archivo,
    modo_ipc,
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

    if modo_ipc == "Inicio":
        # Fecha del Periodo anterior (inicio del cupon actual)
        fecha_per_anterior = calcular_fecha_anterior(
            fecha=min(fechas_cupones),
            periodicidad=periodicidad,
            base_intereses=base_dias_anio,
            num_per=1,
        )
        tasa_per_anterior = sumar_spread_ipc(
            tasa_spread=tasa_anual_cupon,
            fecha=fecha_per_anterior,
            modalidad=modalidad,
            archivo=archivo,
        )
        tasa_fechas = sumar_spread_ipc_batch(
            tasa_spread=tasa_anual_cupon,
            lista_fechas=fechas_cupones,
            modalidad=modalidad,
            archivo=archivo,
        )
        # reemplazar por la anterior
        tasa_fechas = shift_list_with_replacement(
            tasa_fechas, shift=1, fill_value=tasa_per_anterior
        )
        # (1 + tasa_ibr_spread_i) ** (dias_cupon[dias] / 365) - 1
        # nominal
        tasas_final = [
            round((1 + (t / 100)) ** (dias_cupon[index] / base[base_dias_anio]) - 1, 5)
            for index, t in enumerate(tasa_fechas)
        ]

        # for display
        tasa_fechas = [
            round(restar_tasas_efectivas(tasa1=x, tasa2=tasa_anual_cupon / 100), 2)
            for x in tasa_fechas
        ]

    else:

        tasa_fechas = sumar_spread_ipc_batch(
            tasa_spread=tasa_anual_cupon,
            lista_fechas=fechas_cupones,
            modalidad=modalidad,
            archivo=archivo,
        )
        tasas_final = [
            round((1 + (t / 100)) ** (dias_cupon[index] / base[base_dias_anio]) - 1, 5)
            for index, t in enumerate(tasa_fechas)
        ]

        # for display
        tasa_fechas = [
            round(
                restar_tasas_efectivas(tasa1=x / 100, tasa2=tasa_anual_cupon / 100), 2
            )
            for x in tasa_fechas
        ]

    return tasas_final, tasa_fechas


def sumar_spread_ipc(
    tasa_spread: float,
    fecha: datetime.date,
    modalidad: str,
    archivo=None,
):
    """
    Calcula la tasa total IPC sumando la tasa spread a la tasa IPC real
    obtenida desde el Banco de la República o desde un archivo de proyecciones.

    Parámetros:
        tasa_spread (float): La tasa adicional que se suma a la tasa IPC.
        fecha (datetime.date): La fecha de la negociación.
        archivo (optional): Archivo con datos de proyección. Si es None, se usa data en línea.
        modalidad: str, "Nominal" o "EA" para indicar el tipo de tasa.

    Retorna:
        float: la tasa IPC completa (spread+IPC)

    Excepciones:
        Exception: Si ocurre un error al obtener la tasa IPC o si no hay datos disponibles.
    """
    try:
        tasa_ibr_real = obtener_tasa_ipc_real(fecha=fecha, archivo=archivo)

        # Sumar la tasa de negociación a la tasa IPC real
        tasa_ibr_spread = sumar_tasas(
            tasa1=tasa_ibr_real, tasa2=tasa_spread, modalidad=modalidad
        )

        return tasa_ibr_spread

    except Exception as e:
        raise Exception(f"Error al calcular la tasa de negociación IPC: {str(e)}")


def sumar_spread_ipc_batch(
    tasa_spread: float,
    lista_fechas: list[datetime.date],
    modalidad: str,
    archivo=None,
):
    """
    Calcula la tasa total IPC sumando la tasa spread a la tasa IPC real
    obtenida desde el Banco de la República o desde un archivo de proyecciones.

    Parámetros:
        tasa_spread (float): La tasa adicional que se suma a la tasa IPC.
        lista_fechas (list[datetime.date]): La fecha de la negociación.
        archivo (optional): Archivo con datos de proyección. Si es None, se usa data en línea.
        modalidad: str, "Nominal" o "EA" para indicar el tipo de tasa.

    Retorna:
        list[float]: la tasa IPC completa (spread+IPC)

    Excepciones:
        Exception: Si ocurre un error al obtener la tasa IPC o si no hay datos disponibles.
    """
    try:
        tasa_ibr_real = obtener_tasa_ipc_real_batch(
            lista_fechas=lista_fechas, archivo=archivo
        )

        # Sumar la tasa de negociación a la tasa IPC real
        tasa_ibr_spread = [
            sumar_tasas(tasa1=ibr, tasa2=tasa_spread, modalidad=modalidad)
            for ibr in tasa_ibr_real
        ]

        return tasa_ibr_spread

    except Exception as e:
        raise Exception(f"Error al calcular la tasa de negociación IPC: {str(e)}")


def obtener_tasa_ipc_real(fecha: datetime.date, archivo):
    """
    Procesa una única fecha llamando a `filtrar_por_fecha` si hay un archivo,
    o `fetch_ipc_data_banrep` si no lo hay.

    :param fecha_negociacion: str, fecha en formato 'DD/MM/YYYY'.
    :param archivo: str (opcional), ruta del archivo si los datos vienen de ahí.
    :return: float, valor de la tasa IPC si existen datos; de lo contrario, lanza una excepción.
    """

    if archivo:
        df = filtrar_por_fecha(archivo, "IPC Estimado", [fecha])
    else:
        pass  # TODO: do it

    if df.empty:
        raise ValueError(f"No existen datos para la fecha {fecha}")

    return df.iloc[0, 1]  # Retorna el valor numérico de la tasa IPC


def obtener_tasa_ipc_real_batch(lista_fechas: list[datetime.date], archivo):
    """
    Procesa una lista de fechas llamando a `filtrar_por_fecha` si hay un archivo,
    o `fetch_ibr_data_banrep` si no lo hay.

    :param lista_fechas: list, lista de fechas en formato 'DD/MM/YYYY'.
    :param archivo: str (opcional), ruta del archivo si los datos vienen de ahí.
    :return: list, valores de la tasa IPC si existen datos; de lo contrario, lanza una excepción.
    """

    if archivo:
        df = filtrar_por_fecha(archivo, "IPC Estimado", lista_fechas)
    else:
        # df = fetch_ipc_data_banrep(min(ibr_fechas_reales), max(ibr_fechas_reales))
        # Asegurarse de que la columna de fechas tenga el mismo tipo
        # df["Fecha"] = pd.to_datetime(df["Fecha"])
        # ibr_fechas_df["Fecha"] = pd.to_datetime(ibr_fechas_df["Fecha"])
        # Realizar la intersección (inner join)
        # df = df.merge(ibr_fechas_df, on="Fecha", how="inner")
        # if df.empty:
        #    raise ValueError(
        #    f"No hay fechas en común entre los datos disponibles y {ibr_fechas_reales}"
        # )
        # TODO: This one as well
        pass

    if df.empty:
        raise ValueError(f"No existen datos para las fechas {lista_fechas}")

    # fechas_faltantes = set(lista_fechas) - set(df.iloc[:, 0])
    # if fechas_faltantes:
    #    raise ValueError(
    #        f"No existen datos para las siguientes fechas: {sorted(fechas_faltantes)}. Por favor verificar archivo."
    #    )

    return df.iloc[:, 1].tolist()  # Retorna una lista con los valores de la tasa IPC
