# Logging

Some library functions will send logs to standard out. You can configure the log levels using `grwiki.configure_logging` like:

```
import grwiki
import logging

grwiki.configure_logging(
    level=logging.INFO,  # Info by default, can also put logging.CRITICAL or other values
    log_file=None  # Standard out by default, otherwise you can give a file path
)
```
