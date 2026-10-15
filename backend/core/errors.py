class MissingTenantContextError(RuntimeError):
    """A school-owned model was used with no school in the current context."""


class SystemScopeRequiredError(RuntimeError):
    """The unscoped `all_schools` manager was used outside `system_scope`."""
