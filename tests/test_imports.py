import importlib
import pkgutil

import dbtsl


def test_imports() -> None:
    """Test that nothing raises import error.

    This is a sanity check test to make sure we have no wrong imports or
    anything else that might raise an error. This might catch errors such as
    importing something from `typing` when we should be importing from `typing_extensions`
    in an older version of Python.
    """
    for pkg in pkgutil.walk_packages(path=dbtsl.__path__, prefix=f"{dbtsl.__name__}."):
        importlib.import_module(pkg.name)
