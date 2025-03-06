from datetime import date


# validate form function
def validate_inputs(
    valor_nominal,
    fecha_emision,
    fecha_vencimiento,
    periodo_cupon,
    tasa_cupon,
    base_intereses,
    fecha_negociacion,
    tasa_mercado,
    valor_nominal_base,
    radio_data=None,
):
    """Validates form inputs and returns a dictionary of errors."""
    errors = {}

    # Lista de campos obligatorios y sus mensajes de error
    required_fields = {
        "valor_nominal": "❌ El valor nominal no puede estar vacío.",
        "fecha_emision": "❌ La fecha de emisión no puede estar vacía.",
        "fecha_vencimiento": "❌ La fecha de vencimiento no puede estar vacía.",
        "periodo_cupon": "❌ El período del cupón no puede estar vacío.",
        "tasa_cupon": "❌ La tasa del cupón no puede estar vacía.",
        "base_intereses": "❌ La base de intereses no puede estar vacía.",
        "fecha_negociacion": "❌ La fecha de negociación no puede estar vacía.",
        "tasa_mercado": "❌ La tasa de mercado no puede estar vacía.",
        "valor_nominal_base": "❌ El valor nominal base no puede estar vacío.",
    }

    # Verificación automática de campos vacíos
    for field, error_message in required_fields.items():
        if not locals()[field]:  # Obtiene el valor de la variable por su nombre
            errors[field] = error_message

    # Obtener la fecha actual
    today = date.today()

    # Validación de fechas
    if fecha_emision and fecha_vencimiento and fecha_emision >= fecha_vencimiento:
        errors["fecha_emision"] = (
            "❌ La fecha de emisión debe ser menor a la fecha de vencimiento."
        )

    if fecha_negociacion and fecha_emision and fecha_vencimiento:
        if not (fecha_emision <= fecha_negociacion <= fecha_vencimiento):
            errors["fecha_negociacion"] = (
                "❌ La fecha de negociación debe ser mayor a la fecha de emisión y menor a la fecha de vencimiento."
            )

    # Nueva validación: fecha de emisión debe ser menor o igual a hoy
    if fecha_emision and fecha_emision > today:
        errors["fecha_emision"] = (
            "❌ La fecha de emisión no puede estar en el futuro para transacciones online."
        )
    if fecha_negociacion and fecha_negociacion > today and radio_data == "Online":
        errors["fecha_negociacion"] = (
            "❌ La fecha de negociación no puede estar en el futuro para transacciones online."
        )
    if fecha_vencimiento and fecha_vencimiento > today and radio_data == "Online":
        errors["fecha_vencimiento"] = (
            "❌ La fecha de Vencimiento no puede estar en el futuro para transacciones online."
        )

    return errors
