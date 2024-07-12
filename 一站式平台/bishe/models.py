from django.db import models

# Create your models here.
# class User(models.Model):
#     username = models.CharField(max_length=32)
#     password = models.CharField(max_length=32)
#     email = models.CharField(max_length=32)
#     phone = models.CharField(max_length=32)
#     UID = models.IntegerField(unique=True)
#     def __str__(self):
#         return self.username
#
#     class Meta:
#         db_table = 'User'
#
# class Models(models.Model):
#     UID = models.ForeignKey(User.UID,on_delete=models.CASCADE)
#     name = models.CharField(max_length=32)
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#
#     def __str__(self):
#         return self.name
#
#     class Meta:
#         db_table = 'Models'
#
# class Dataset(models.Model):
#     UID = models.ForeignKey(User.UID,on_delete=models.CASCADE)
#     name = models.CharField(max_length=32)
#     dataset = models.ImageField(upload_to='dataset')
#     def __str__(self):
#         return self.name
#
#     class Meta:
#         db_table = 'dataset'