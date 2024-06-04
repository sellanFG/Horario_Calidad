from django.db import models

# Create your models here.


class usuario(models.Model):
    id =  models.AutoField(primary_key=True),
    usuario= models.CharField,
    contrasena= models.CharField

    def __str__(self):
        return self.usuario
    
    class Meta:
        verbose_name_plural="Usuario"
