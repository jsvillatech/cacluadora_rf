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
