from celery import shared_task
from django.core.mail import send_mail
from datetime import datetime, timedelta
from .models import Budget

@shared_task
def send_budget_reminders():
    today = datetime.now().date()
    budgets = Budget.objects.select_related("user", "category").all()
    reminders_sent = []

    for budget in budgets:
        user = budget.user
        due_date = budget.due_date
        category_name = budget.category.name
        category_type = budget.category.type
        category_priority = budget.category.priority

        
        if due_date and today == due_date - timedelta(days=1):
            subject = "Reminder to pay your bills"
            message = f"Hello {user.first_name}, your due date for {category_name} is on {due_date.strftime('%d/%m/%Y')}."
            send_mail(subject, message, "yaba8084@gmail.com", [user.email], fail_silently=False)
            reminders_sent.append({"type": "due_date", "category": category_name, "user": user.id})

        
        if category_priority and category_priority.lower() == "high" and category_type.lower() == "expense":
            subject = f"Payment Reminder for {category_name}"
            message = (
                f"Hello {user.first_name}, your {category_name} payment is due on {due_date.strftime('%d/%m/%Y')}.\n"
                f"Please pay to avoid additional fees.\n"
                f"You can pay through our website."
            )
            send_mail(subject, message, "yaba8084@gmail.com", [user.email], fail_silently=False)
            reminders_sent.append({"type": "high_priority", "category": category_name, "user": user.id})

    return reminders_sent
