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

# class ManagerModel(models.Model):
#     creator = models.OneToOneField(User, related_name='creator', on_delete=models.PROTECT) 
#     updated_by = models.ForeignKey(User, on_delete=models.PROTECT)
#     class Meta:
#         abstract = True

class Template(AuditModel):
    DESTINATION__CHOICES = (('CN', 'CN'), ('US', 'US'))
    name = models.CharField(max_length=50, unique=True)
    destination = models.CharField(max_length=2, choices=DESTINATION__CHOICES, default='CN')
    description = models.CharField(max_length=255, null=True)
    version = models.CharField(max_length=50, null=True)
    content = models.TextField(max_length =60000)

class Company(AuditModel):
    # owner = models.OneToOneField(User, related_name='owner', on_delete=models.PROTECT) 
    name = models.CharField(max_length=50, unique=True)
    address = models.CharField(max_length=255)
    telephone = models.CharField(max_length=15)
    city = models.CharField(max_length=30)
    province = models.CharField(max_length=30)
    country = models.CharField(max_length=30)
    postal = models.CharField(max_length=15, null=True)
    activated = models.BooleanField(default=False)

class Application(AuditModel): #ManagerModel
    template = models.ForeignKey(Template, on_delete=models.PROTECT)
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='applications')
    description = models.CharField(max_length=50)
    number = models.CharField(max_length=50)
    sequence = models.CharField(max_length=50)
    seqDescription = models.CharField(max_length=50, blank=True, null=True )
    class Meta:
        unique_together = ('number', 'sequence',)
    
class Employee(AuditModel):
    ROLE_CHOICES = (('ADMIN', 'ADMIN'), ('MGER', 'MANAGER'), ('BAS', 'BASIC'))
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True,)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employees')
    firstName = models.CharField(max_length = 50, null=True)
    lastName = models.CharField(max_length = 50, null=True)
    telephone = models.CharField(max_length=15, null=True)
    role = models.CharField(max_length=4, choices=ROLE_CHOICES, default='BAS')
   
class Contact(AuditModel): #ManagerModel
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='contacts')
    PHONE_CHOICES = (('BUS', 'Business Telephone Number'), ('FAX','Fax Telephone Number'), ('MOB', 'Mobile Telephone Number'))
    CONTACTTYPE_CHOICES = (('REG', 'REGULATORY'),('TEC', 'TECHNICAL'),('AGT', 'AGENT'),('PRO', 'PROMOTIONAL'))
    contactType = models.CharField(max_length=3, choices=CONTACTTYPE_CHOICES)
    phone = models.CharField(max_length=15)
    telephoneType = models.CharField(max_length=3, choices=PHONE_CHOICES, default='BUS')
    email = models.EmailField(max_length=50)
    contactName = models.CharField(max_length =50)

    class Meta:
        unique_together = ('application', 'contactType')

class Appinfo(AuditModel):
    APPTYPE_CHOICES = (('NDA', 'New Drug Application (NDA)'), ('ANDA', 'Abbreviated New Drug Application (ANDA)'), 
                        ('BLA', 'Biologic License Application (BLA)'), ('IND', 'Investigational New Drug (IND)'), 
                        ('DMF', 'Drug Master File (DMF)'), ('EUA', 'Emergency Use Authorization (EUA)'))
    application = models.OneToOneField(Application, on_delete=models.CASCADE, primary_key=True,)
    dunso = models.CharField(max_length=15)
    companyName = models.CharField(max_length=50)
    description = models.CharField(max_length=50, blank=True, null=True)
    appType = models.CharField(max_length=50)
    subId = models.CharField(max_length=15)
    subType = models.CharField(max_length=50)
    effType = models.CharField(max_length=50, blank=True, null=True)
    subSubType = models.CharField(max_length=50)
    # subNumber = models.CharField(max_length=15, null=True)
    # refNumber = models.CharField(max_length=15, null=True)
    # refType = models.CharField(max_length=50, null=True)

class File(AuditModel):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='files')
    name = models.CharField(max_length=50)
    url = models.URLField(max_length=100)
    size = models.IntegerField() #validator = [MaxValueValidator(120000000)]
    # status = models.IntegerField(max_length=1)

class FileState(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='states' )
    action = models.CharField(max_length=255)
    path = models.FilePathField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

class Node(AuditModel):
    TYPE_CHOICES = (('root', 'root'),('default', 'default'), ('folder', 'folder'), ('file', 'file'), ('tag', 'tag'))
    nid = models.AutoField(primary_key=True)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='nodes')
    id = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    text = models.CharField(max_length=100)
    type = models.CharField(max_length=15, choices=TYPE_CHOICES, default='default')
    sNumber = models.CharField(max_length=15)
    parent = models.CharField(max_length=15)
    original = models.BooleanField(default=False)

    class Meta:
        unique_together = ('application', 'id',)

class Tag(AuditModel):
    node = models.OneToOneField(Node, on_delete=models.CASCADE, primary_key=True,)
    sNumber = models.CharField(max_length=15)
    title = models.CharField(max_length=50)
    eCode = models.CharField(max_length=50)
    studyNumber = models.CharField(max_length=50, blank=True, null=True)
    stfType = models.CharField(max_length=50, blank=True, null=True)
    species = models.CharField(max_length=50, blank=True, null=True)
    root = models.CharField(max_length=50, blank=True, null=True)
    duration = models.CharField(max_length=50, blank=True, null=True)
    control = models.CharField(max_length=50, blank=True, null=True)
    tag = models.CharField(max_length=50, blank=True, null=True)
    manufacturer = models.CharField(max_length=50, blank=True, null=True)
    substance = models.CharField(max_length=50, blank=True, null=True)
    productName = models.CharField(max_length=50, blank=True, null=True)
    dosage = models.CharField(max_length=50, blank=True, null=True)

# rm -f db.sqlite3
# rm -r applications/migrations
# python manage.py makemigrations applications
# python manage.py migrate
#python manage.py createsuperuser
