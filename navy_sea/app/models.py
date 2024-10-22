from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager


class NewUserManager(UserManager):
    def create_user(self,email,password=None, **extra_fields):
        if not email:
            raise ValueError('User must have an email address')
        
        email = self.normalize_email(email) 
        user = self.model(email=email, **extra_fields) 
        user.set_password(password)
        user.save(using=self.db)
        return user


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(("email адрес"), unique=True)
    password = models.CharField(verbose_name="Пароль")    
    is_staff = models.BooleanField(default=False, verbose_name="Является ли пользователь менеджером?")
    is_superuser = models.BooleanField(default=False, verbose_name="Является ли пользователь админом?")
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True,
        help_text=('The groups this user belongs to. A user will get all permissions '
                   'granted to each of their groups.'),
        verbose_name=('groups')
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',
        blank=True,
        help_text=('Specific permissions for this user.'),
        verbose_name=('user permissions')
    )

    USERNAME_FIELD = 'email'

    objects = NewUserManager()


class ShipManager(models.Manager):
    def get_one_ship(self, ship_id):
        return self.get(id=ship_id)


class Ship(models.Model):
    STATUS_CHOICES = [
        ("a", "Active"), 
        ("d", "Deleted")
    ]
    ship_name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    year = models.IntegerField()
    length = models.IntegerField()
    displacement = models.IntegerField()
    country = models.CharField(max_length=255)
    photo = models.CharField(null=True, blank=True, max_length=255)
    status = models.CharField(choices=STATUS_CHOICES, max_length=7, default='a')

    objects = ShipManager()

    def __str__(self):
        return self.ship_name


class FightManager(models.Manager):
    def get_one_fight(self, fight_id):
        return self.get(id=fight_id)

    def get_total_ships(self, fight):
        return FightShip.objects.filter(fight=fight).count()


class Fight(models.Model):
    STATUS_CHOICES = [
        ('dr', "Draft"),
        ('del', "Deleted"), 
        ('f', "Formed"), 
        ('c', "Completed"), 
        ('r', "Rejected")
    ]
    fight_name = models.CharField(null=True, max_length=255)
    result = models.CharField(null=True, max_length=255)
    status = models.CharField(choices=STATUS_CHOICES, max_length=9, default='dr')
    created_at = models.DateTimeField(auto_now_add=True)
    formed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    creator = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='created_fights')
    moderator = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderated_fights')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['creator'], condition=models.Q(status='dr'), name='unique_draft_per_user')
        ]

    objects = FightManager()

    def __str__(self):
        return self.fight_name


class FightShip(models.Model):
    fight = models.ForeignKey(Fight, on_delete=models.CASCADE)
    ship = models.ForeignKey(Ship, on_delete=models.CASCADE)
    admiral = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['fight', 'ship'], name='unique_fight_ship')
        ]
