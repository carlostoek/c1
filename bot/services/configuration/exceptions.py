"""
Excepciones personalizadas para ConfigurationService.
"""


class ConfigurationError(Exception):
    """Error base de configuración."""
    pass


class ConfigNotFoundError(ConfigurationError):
    """Configuración no encontrada."""
    def __init__(self, config_type: str, identifier: str):
        self.config_type = config_type
        self.identifier = identifier
        super().__init__(f"{config_type} '{identifier}' no encontrado")


class ConfigAlreadyExistsError(ConfigurationError):
    """Configuración ya existe."""
    def __init__(self, config_type: str, identifier: str):
        self.config_type = config_type
        self.identifier = identifier
        super().__init__(f"{config_type} '{identifier}' ya existe")


class ConfigValidationError(ConfigurationError):
    """Error de validación de configuración."""
    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(f"Validación fallida en '{field}': {message}")


class ConfigInUseError(ConfigurationError):
    """Configuración en uso, no se puede eliminar."""
    def __init__(self, config_type: str, identifier: str, used_by: str):
        self.config_type = config_type
        self.identifier = identifier
        self.used_by = used_by
        super().__init__(f"{config_type} '{identifier}' está en uso por {used_by}")