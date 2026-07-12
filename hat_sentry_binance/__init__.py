import warnings

# Suppress deprecation warnings from python-binance's transitive dep
# (websockets>=14 deprecated WebSocketClientProtocol, which python-binance still imports).
# We pin websockets<14 in requirements.txt, but guard imports here too.
warnings.filterwarnings(
    "ignore",
    message=".*WebSocketClientProtocol is deprecated.*",
    category=DeprecationWarning,
)
warnings.filterwarnings(
    "ignore",
    message=".*websockets.legacy is deprecated.*",
    category=DeprecationWarning,
)

from . import models  # noqa: E402, F401
