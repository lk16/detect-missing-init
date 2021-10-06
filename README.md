# Detect missing `__init__.py` files

This pre-commit hook checks if there are any folders that satisfy these conditions:
* (indirectly) contain a python file
* have no `__init__.py` file
* are not the repository root. [Why](https://github.com/timbrel/GitSavvy/issues/626#issuecomment-290631660).

### Usage
Add the following to your `pre-commit-config.yaml`:

```yaml
  - repo: https://github.com/lk16/detect-missing-init
    rev: v0.0.1  # Please check what the latest version is
    hooks:
    - id: detect-mising-init
      args: ['--fix']  # Leave this line out if you don't want the hook to make any changes
```

### Why?
Since python 3.3 [Implicit namespace packages](https://stackoverflow.com/questions/37139786/is-init-py-not-required-for-packages-in-python-3-3) are supported.

However some tools like mypy, will [not recognize](https://github.com/python/mypy/issues/2773) folders with python files without `__init__.py` as packages.
Mypy is sometimes used with `--ignore-missing-imports`, which has the side effect of silently ignoring these packages.
So not only will mypy completely skip type checking your entire package, it does this without informing the user.

This hook prevents this issue.

### Flags
* `--fix`: create the missing `__init__.py` files


### FAQ
> Does this repo check itself with itself?

[Yes](pre-commit-config.yaml).
