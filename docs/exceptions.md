# Exceptions

There are a few custom exceptions that can be thrown. All exceptions are available at the root of the package, like:

```
from gwiki import ContextExceeded
```

- `ContextExceeded`: If you pass the option `fail_on_overflow=True` when instantiating a language model, then if `.run` is called with a prompt that exceeds the LM's context length, this exception will be raised.
- `EntityNotExists`: If you try to add a reference for an entity given its ID or slug, this exception will be raised if the entity does not exist in the wiki's database. Note that this exception **is not raised when searching for a non-existent entity**.
- `SourceNotExists`: Same as `EntityNotExists` except for sources.
