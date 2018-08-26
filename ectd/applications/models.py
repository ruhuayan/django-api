from django.db import models
from django.contrib.auth.models import User
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# Create your models here.

class AuditModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True)
    class Meta:
        abstract = True

class Template(AuditModel):
    DESTINATION__CHOICES = (('CN', 'CN'), ('US', 'US'))
    name = models.CharField(max_length=50)
    destination = models.CharField(max_length=2, choices=DESTINATION__CHOICES, default='CN')
    description = models.CharField(max_length=255, null=True)
    version = models.CharField(max_length=50, null=True)
    content = models.TextField(max_length =60000)

class Company(AuditModel):
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=255)
    telephone = models.CharField(max_length=15)
    city = models.CharField(max_length=30)
    province = models.CharField(max_length=30)
    country = models.CharField(max_length=30)
    postal = models.CharField(max_length=15, null=True)
    activated = models.BooleanField(default=False)

class Application(AuditModel):
    template = models.ForeignKey(Template, on_delete=models.PROTECT)
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='applications')
    description = models.CharField(max_length=50)
    number = models.CharField(max_length=50)
    sequence = models.CharField(max_length=50)
    seqDescription = models.CharField(max_length=50)
    
class Employee(AuditModel):
    ROLE_CHOICES = (('ADMIN', 'ADMIN'), ('MGER', 'MANAGER'), ('BAS', 'BASIC'))
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employees')
    firstName = models.CharField(max_length = 50, null=True)
    lastName = models.CharField(max_length = 50, null=True)
    telephone = models.CharField(max_length=15, null=True)
    role = models.CharField(max_length=4, choices=ROLE_CHOICES, default='BAS')
   
class Contact(AuditModel):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='contact')
    CONTACTTYPE_CHOICES = (('REG', 'REGULATORY'),('TEC', 'TECHNICAL'),('AGT', 'AGENT'),('PRO', 'PROMOTIONAL'))
    contactType = models.CharField(max_length=3, choices=CONTACTTYPE_CHOICES)
    phone = models.CharField(max_length=15)
    email = models.EmailField(max_length=50)

class Appinfo(AuditModel):
    application = models.OneToOneField(Application, on_delete=models.CASCADE)
    dunso = models.CharField(max_length=15)
    companyName = models.CharField(max_length=50)
    description = models.CharField(max_length=50)
    appType = models.CharField(max_length=50)
    subId = models.CharField(max_length=15)
    subType = models.CharField(max_length=50)
    effType = models.CharField(max_length=50)
    subSubType = models.CharField(max_length=50)
    subNumber = models.CharField(max_length=15)
    refNumber = models.CharField(max_length=15)
    refType = models.CharField(max_length=50)

class File(AuditModel):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='files')
    name = models.CharField(max_length=50)
    url = models.URLField(max_length=100)
    # status = models.IntegerField(max_length=1)

class FileState(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='states' )
    action = models.CharField(max_length=255)
    path = models.FilePathField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

class Node(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='nodes')
    name = models.CharField(max_length=100)
    text = models.CharField(max_length=100)
    type = models.CharField(max_length=15)
    sNumber = models.CharField(max_length=15)
    parent = models.CharField(max_length=15)
    original = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Tag(AuditModel):
    node = models.OneToOneField(Node, on_delete=models.CASCADE)
    sNumber = models.CharField(max_length=15)
    title = models.CharField(max_length=50)
    eCode = models.CharField(max_length=50)
    studyNumber = models.CharField(max_length=50)
    stfType = models.CharField(max_length=50)
    species = models.CharField(max_length=50)
    root = models.CharField(max_length=50)
    duration = models.CharField(max_length=50)
    control = models.CharField(max_length=50)
    tag = models.CharField(max_length=50)
    manufacturer = models.CharField(max_length=50)
    substance = models.CharField(max_length=50)
    productName = models.CharField(max_length=50)
    dosage = models.CharField(max_length=50)

# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         Profile.objects.create(user=instance)

# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     instance.profile.save()
