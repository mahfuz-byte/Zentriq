class MissingTenantContextError(RuntimeError):
    """A school-owned model was used with no school in the current context."""
