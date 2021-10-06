# Detect missing `__init__.py` files

This pre-commit hook checks if there are any folders that both:
* (indirectly) contain a python file
* have no `__init__.py` file

### Why?
Since python 3.3 [Implicit namespace packages](https://stackoverflow.com/questions/37139786/is-init-py-not-required-for-packages-in-python-3-3) are supported.

However some tools like mypy, will [not recognize](https://github.com/python/mypy/issues/2773) folders with python files without `__init__.py` as packages.
Mypy is sometimes used with `--ignore-missing-imports`, which has the side effect of silently ignoring these packages.
So not only will mypy completely skip type checking your entire package, it does this without informing the user.

This hook prevents this issue.

### Flags
* `--fix`: create the missing `__init__.py` files
