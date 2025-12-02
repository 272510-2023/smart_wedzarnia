from django.db import models

# Create your models here.
class SensorReading(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    marker = models.IntegerField()
    temperature = models.FloatField()
    humidity = models.FloatField()
    pressure = models.FloatField()
    gas_resistance = models.FloatField()

    def __str__(self):
        return f"{self.timestamp} | {self.temperature}°C | {self.humidity}"

class DoorStatus(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    open_status = models.BooleanField()
    alarm = models.IntegerField()
