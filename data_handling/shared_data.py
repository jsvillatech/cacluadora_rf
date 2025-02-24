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
