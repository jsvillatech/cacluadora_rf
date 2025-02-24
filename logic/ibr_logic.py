import requests
import datetime
import pandas as pd


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
