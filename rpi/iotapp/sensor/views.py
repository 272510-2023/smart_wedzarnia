from django.shortcuts import render
from .models import SensorReading, DoorStatus
from django.http import JsonResponse

def dashboard(request):
    readings = SensorReading.objects.order_by("-timestamp")[:50][::-1]  # najnowsze 50, rosnąco
    door = DoorStatus.objects.order_by("-timestamp").first()

    context = {
        "timestamps": [r.timestamp.strftime("%H:%M:%S") for r in readings],
        "temperatures": [r.temperature for r in readings],
        "humidities": [r.humidity for r in readings],
        "pressures": [r.pressure for r in readings],
        "door_open": door.open_status if door else None,
        "alarm": door.alarm if door else None,
    }
    return render(request, "dashboard.html", context)


def dashboard_data_api(request):
    # Pobierz ostatnie 20 odczytów
    readings = SensorReading.objects.order_by('-timestamp')[:20][::-1]
    last_door = DoorStatus.objects.last()
    
    data = {
        'timestamps': [r.timestamp.strftime("%H:%M:%S") for r in readings],
        'temperatures': [r.temperature for r in readings],
        'humidities': [r.humidity for r in readings],
        'pressures': [r.pressure for r in readings],
        'door_open': last_door.open_status if last_door else False,
        'alarm': last_door.alarm if last_door else 0,
    }
    return JsonResponse(data)
