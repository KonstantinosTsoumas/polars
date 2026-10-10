from pathlib import Path

# The compiled shared object is installed next to this file, so the directory
# itself is what `register_plugin_function` needs to be pointed at.
LIB = Path(__file__).parent
