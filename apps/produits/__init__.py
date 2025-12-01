# Ensure additional models are registered
try:
    from . import models_catalog  # noqa: F401
except Exception:
    # Avoid hard failures during migrations if dependencies not ready
    pass
