class ErrorCampo(ValueError):
    """Error de validación ligado a un campo del formulario.
    `clave` es el nombre del campo; la pantalla muestra `mensaje` en rojo debajo."""

    def __init__(self, clave, mensaje):
        super().__init__(mensaje)
        self.clave = clave
        self.mensaje = mensaje
