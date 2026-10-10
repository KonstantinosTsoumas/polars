from pathlib import Path

# The compiled cdylib is installed next to this file, so the package
# directory itself is what `register_plugin_function` needs.
LIB = Path(__file__).parent
