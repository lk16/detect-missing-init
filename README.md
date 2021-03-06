# Detect missing `__init__.py` files

This pre-commit hook checks if there are any folders that satisfy these conditions:
* it (directly or indirectly) contains a python file
* it contains no `__init__.py` file
* it is not the repository root. Can be [overridden](#arguments). [Why](https://github.com/timbrel/GitSavvy/issues/626#issuecomment-290631660)?

Missing files can be created automatically, see the Arguments section below.

### Usage
Add the below yaml snippet to your `pre-commit-config.yaml`.
Optionally run `pre-commit run --all-files` to check if the hook finds any problems. Otherwise it will run automatically on any future commit.

```yaml
  - repo: https://github.com/lk16/detect-missing-init
    rev: v0.1.6
    hooks:
    - id: detect-missing-init
      args: ['--create', "--track", "--python-folders", "tests,somefolder,otherfolder"]  # See the arguments section
```

### Arguments
Without arguments the hook just reports missing files without making any changes.
This is a design choice: the user should opt-in for any behavior other than the basic check for missing files.

* `--python-folders foo,bar/baz`: Required flag. Value should be a comma separated lists to of paths to be checked for missing `__init__.py` files. Paths should be relative to the repostiory root. To add the repo root to this list use `.`.
* `--create`: create the missing `__init__.py` files.
* `--track`: runs `git add` on all created `__init__.py` files. Implies `--create`.

### Why?
Since python 3.3 [implicit namespace packages](https://stackoverflow.com/questions/37139786/is-init-py-not-required-for-packages-in-python-3-3) are supported.

However some tools like mypy, will [not recognize](https://github.com/python/mypy/issues/2773) folders with python files without `__init__.py` as packages.
Mypy is sometimes used with `--ignore-missing-imports`, which has the side effect of silently ignoring these packages.
So not only will mypy completely skip type checking your entire package, it does this without informing the user.

This hook prevents this issue.

### FAQ
> Does this repo check itself with itself?

[Yes](.pre-commit-config.yaml#L41).

### Run tests
```sh
python -m py.test tests/ --cov=hook --cov-report term-missing
```
