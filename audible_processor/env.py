import os
from typing import Any

class Vars:
    USE_AUTHOR_DIR = 'USE_AUTHOR_DIR'
    USE_TITLE_DIR = 'USE_TITLE_DIR'
    OUTPUT_DIR = 'OUTPUT_DIR'
    INPUT_DIR = 'INPUT_DIR'
    THREADS = 'THREADS'
    ACTIVATION_BYTES = 'ACTIVATION_BYTES'
    INTERVAL = 'INTERVAL'
    VERBOSITY = 'VERBOSITY'

def _cast_bool(name: str, value: Any) -> bool:
    if type(value) == bool:
        return value

    true_ = ('true', '1', 't', 'yes', 'y') # Valid truthy values
    false_ = ('false', '0', 'f', 'no', 'n') # Valid falsey values

    safe = str(value).strip().lower()
    if safe not in true_ + false_:
        raise ValueError(f'Invalid value `{value}` for variable `{name}`')
    return safe in true_

def _cast_int(name: str, value: Any) -> int:
    if type(value) == int:
        return value

    try:
        return int(value)
    except ValueError as e:
        raise ValueError(f'Invalid numeric value `{value}` for variable `{name}`')

def envDefault(name: str, default_value: Any = None) -> Any:
    value: str | None = os.getenv(name, None)
    if value is None:
        if default_value is None:
            raise ValueError(f'Variable `{name}` not set')
        else:
            value = default_value

    # Type casting
    if default_value is None:
        # Treat as string
        value = value.strip()
    else:
        t_ = type(default_value)
        if t_ == bool:
            value = _cast_bool(name, value)
        elif t_ == int:
            value = _cast_int(name, value)
        else:
            # Treat as string
            value = value.strip()

    return value
