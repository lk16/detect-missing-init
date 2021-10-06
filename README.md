# Detect missing `__init__.py` files

This pre-commit hook checks if there are any folders that satisfy these conditions:
* (indirectly) contain a python file
* have no `__init__.py` file
* are not the repository root. [Why](https://github.com/timbrel/GitSavvy/issues/626#issuecomment-290631660).

Missing files can be created automatically, see the Arguments section below.

### Usage
Add the below yaml snippet to your `pre-commit-config.yaml`.
Optionally run `pre-commit run --all-files` to check if the hook finds any problems. Otherwise it will run on any commit going forward.

```yaml
  - repo: https://github.com/lk16/detect-missing-init
    rev: v0.0.1  # Please check what the latest available version is
    hooks:
    - id: detect-mising-init
      args: ['--fix']  # See the arguments section
```

### Arguments
When no flags/arguments are specified, the hook just reports missing files and exits.

* `--fix`: create the missing `__init__.py` files.

### Why?
Since python 3.3 [implicit namespace packages](https://stackoverflow.com/questions/37139786/is-init-py-not-required-for-packages-in-python-3-3) are supported.

However some tools like mypy, will [not recognize](https://github.com/python/mypy/issues/2773) folders with python files without `__init__.py` as packages.
Mypy is sometimes used with `--ignore-missing-imports`, which has the side effect of silently ignoring these packages.
So not only will mypy completely skip type checking your entire package, it does this without informing the user.

This hook prevents this issue.

### FAQ
> Does this repo check itself with itself?

[Yes](.pre-commit-config.yaml#L41).


### TODO
- Add tests
- Add flag to expect `__init__.py` file in repo root
