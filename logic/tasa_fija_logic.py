from math import pow


def convertir_tasa_cupon_tf(
    modalidad_tasa: str,
    periodicidad: str,
    tasa_anual_cupon: float,
    dias_pago_entre_cupon: list[int],
):
    """
    Convierte una tasa efectiva anual (EA) o nominal anual a una tasa efectiva o nominal en otra periodicidad.

    Parámetros:
    modalidad_tasa (str): Modalidad de la tasa ('EA' o 'Nominal').
    periodicidad (str): Periodo de conversión ('Mensual', 'Trimestral', 'Semestral', 'Anual').
    tasa_anual_cupon (float): Tasa anual expresada en decimal (Ej: 10% -> 0.10).
    dias_pago_entre_cupon (list[int]): Lista de número de días transcurridos de pago entre cupones.

    Retorna:
    list[float]: Tasa convertida a la periodicidad especificada.
    """
    tasa_anual_cupon = tasa_anual_cupon / 100

    periodos_por_anio = {"Mensual": 12, "Trimestral": 4, "Semestral": 2, "Anual": 1}

    if not dias_pago_entre_cupon:
        raise ValueError("La lista de días de pago entre cupones está vacía.")

    if periodicidad not in periodos_por_anio:
        raise ValueError(
            "Periodicidad no válida. Usa: 'Mensual', 'Trimestral', 'Semestral' o 'Anual'."
        )

    if modalidad_tasa == "EA":
        tasas = [
            pow(1 + tasa_anual_cupon, dias / 365) - 1 for dias in dias_pago_entre_cupon
        ]
        return tasas

    elif modalidad_tasa == "Nominal":
        tasas = [
            tasa_anual_cupon / periodos_por_anio[periodicidad]
            for _ in dias_pago_entre_cupon
        ]

        return tasas

    else:
        raise ValueError("Modalidad de tasa no válida. Usa 'EA' o 'Nominal'.")
