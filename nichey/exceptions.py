
# When a prompt that's too large gets sent to a model API
class ContextExceeded(Exception):
    pass

class EntityNotExists(Exception):
    pass

class SourceNotExists(Exception):
    pass
