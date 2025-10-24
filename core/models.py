from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    date_joined = models.DateTimeField(default=timezone.now)
    currency = models.CharField(max_length=3, default='USD')
    first_name = models.CharField( max_length=150, blank=False)
    last_name = models.CharField( max_length=150, blank=False)
    email = models.EmailField(blank=False)
    is_active = models.BooleanField(default=False)
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='core_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='core_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    class Meta:
        db_table = "tblUsers"

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    type = models.CharField(
        max_length=10, 
        choices=[('income', 'Income'), ('expense', 'Expense')]
    )
    class Meta:
        ordering = ['name']
        db_table = "tblCategory"
    
    def __str__(self):
        return self.name

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user', 'date']), 
            models.Index(fields=['category']),
        ]
        db_table = "tblTransaction"
    
    def __str__(self):
        return f"{self.category.name}: ${self.amount}"
    
    @property
    def type(self):
        return self.category.type

    class IncomeExpenseChoices(models.TextChoices):
        INCOME = 'income', 'Income'
        EXPENSE = 'expense', 'Expense'


class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    month = models.DateField()  # First day of month
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        unique_together = ['user', 'category', 'month']
        indexes = [models.Index(fields=['user', 'month'])]
        db_table = "tblBudget"