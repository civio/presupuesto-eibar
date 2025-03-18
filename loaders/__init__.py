import six

if six.PY2:
    from eibar_budget_loader import EibarBudgetLoader
else:
    from .eibar_budget_loader import EibarBudgetLoader
