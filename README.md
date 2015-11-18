# storm-deployment-stats

## Requisites

- python
- python-ldap
- Jinja2

## Install on OSX

Assuming brew installed:

```
brew install python
pip install python-ldap
pip install Jinja2
```

## Generate report

Run:

```{Python}

python generate.py

```

If no errors occours, `report.html` is generated.
