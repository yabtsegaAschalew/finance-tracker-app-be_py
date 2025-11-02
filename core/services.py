from core.models import Budget

def manage_income(request):
    current_user = request.user
    budget = Budget.objects.filter(current_user)

    pass

def manage_expense():
    pass
