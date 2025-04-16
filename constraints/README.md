# Dependency constraints and overrides

All files in this directory specify transitive dependency constraints for usage in our test environments. The files in this directory are _not_ shipped with the package, and users should specify those constraints themselves, according to what works in their own system. Learn more about pip constraints [here](https://pip.pypa.io/en/stable/user_guide/#constraints-files).

This is useful for specifying different minimum versions of a package for Python 3.13 and 3.9, since older versions might not support the newest Python and vice-versa.

For direct dependencies, we solve this by using the `python_version` [environment marker](https://peps.python.org/pep-0508/#environment-markers) in our dependencies.
