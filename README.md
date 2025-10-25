# System Monitorowania i Symulacji Procesu Wędzenia

## 1. Wprowadzenie

Celem projektu jest stworzenie inteligentnego systemu monitorującego i symulującego proces wędzenia z wykorzystaniem zestawu czujników WisBlock Kit 4-EU868 firmy RAKwireless oraz systemu chmurowego.  
System umożliwia:
- zbieranie danych środowiskowych (temperatura, wilgotność, ciśnienie, jakość powietrza) w czasie rzeczywistym,
- wizualizację danych w formie wykresów i pasków postępu,
- symulację sterowania procesem wędzenia za pomocą mikrokontrolera (ESP32, STM32 lub Arduino),
- kontrolę stanu czujników bezpieczeństwa (drzwi, okna),
- sygnalizację świetlną etapów procesu.

---

## 2. Podział obowiązków

Projekt realizowany jest przez 7-osobowy zespół:

| Osoba | Zadanie |
|-------|---------|
| Osoba 1 | Projekt i konfiguracja czujników WisBlock (temperatura, wilgotność, ciśnienie, jakość powietrza) |
| Osoba 2 | Implementacja modułu komunikacji LoRaWAN i transmisji danych do Gateway |
| Osoba 3 | Opracowanie logiki chmurowej (odbiór danych, analiza, wykrywanie błędów, alerty) |
| Osoba 4 | Tworzenie panelu wizualizacji danych (dashboard online, wykresy, statusy czujników) |
| Osoba 5 | Integracja czujników drzwi/okien i przycisku uruchamiającego proces |
| Osoba 6 | Symulacja sterowania procesem wędzenia (grzałka, dym, LEDy) |
| Osoba 7 | Dokumentacja techniczna i integracja wszystkich modułów w jedną spójną całość |

---

## 3. Wymagania techniczne

- **Moduł WisBlock Kit 4-EU868** – pomiar temperatury, wilgotności, ciśnienia i jakości powietrza.  
- **Gateway LoRaWAN** – transmisja danych do chmury.  
- **Chmura** – analiza, wizualizacja i generowanie alertów w czasie rzeczywistym.  
- **Mikrokontroler** (ESP32 / STM32 / Arduino) – symulacja grzałki, wytwarzanie dymu, sterowanie LEDami.  
- **Czujniki drzwi i okien** – kontrola bezpieczeństwa procesu.  
- **Moduł I/O** – inicjacja procesu wędzenia i sygnalizacja świetlna etapów.

---

## 4. Przebieg procesu wędzenia (symulacja)

### 4.1 Inicjacja procesu (Moduł I/O)
- Użytkownik naciska przycisk **START**.  
- Moduł I/O wysyła sygnał inicjujący do chmury.  
- Chmura rozpoczyna weryfikację warunków początkowych.

### 4.2 Walidacja warunków (Chmura ↔ Moduł I/O)
- Chmura ustawia **czerwoną lampkę statusu** (Oczekiwanie).  
- Chmura wysyła do Modułu I/O komendę: „Sprawdź czujniki drzwi i okien”.  
- Moduł I/O odczytuje stany czujników i zwraca status do chmury.  

**Decyzja:**
- Jeśli warunek **niespełniony** → Moduł I/O zapala **czerwoną diodę LED** (Wstrzymanie procesu).  
- Jeśli warunek **spełniony** → Moduł I/O zapala **zieloną diodę LED** (Gotowość).

### 4.3 Start symulacji (Chmura → ESP32)
- Chmura wysyła flagę **START** i tryb wędzenia (np. Tryb 1: Ciepłe) do ESP32.  
- ESP32 interpretuje dane i rozpoczyna symulację procesu.

### 4.4 Monitoring i kontrola etapów (pętla)
Proces działa w pętli do zakończenia symulacji:

1. **Pomiar danych środowiskowych:**  
    - Czujniki WisBlock przesyłają temperaturę, wilgotność, ciśnienie, QA do chmury.  
    - Chmura agreguje dane i aktualizuje wykresy.

2. **Status procesu:**  
    - ESP32 wysyła flagę `STATUS_ETAP_N` do chmury.  
    - Chmura aktualizuje pasek postępu i wizualizację etapów.

3. **Sygnalizacja świetlna:**  
    - Chmura wysyła komendę do Modułu I/O, aby zapalił LED dla bieżącego etapu.

### 4.5 Zakończenie procesu
- ESP32 wysyła flagę `KONIEC_PROCESU` do chmury.  
- Chmura:
  - Ustawia pasek postępu na **100%**  
  - Generuje raport podsumowujący proces.  
- Chmura wysyła do Modułu I/O komendę: zapal **zielony, stały LED** (koniec procesu).

---

## 5. Instalacja i konfiguracja

1. Skonfiguruj czujniki WisBlock i podłącz je do mikrokontrolera.  
2. Skonfiguruj komunikację LoRaWAN i połączenie z bramą (Gateway).  
3. Skonfiguruj chmurę do odbioru, analizy i wizualizacji danych.  
4. Zaimplementuj panel wizualizacji (dashboard online, wykresy, statusy czujników).  
5. Przetestuj cały system, upewniając się, że proces wędzenia działa poprawnie.

---

## 6. Podsumowanie

System monitorowania i symulacji procesu wędzenia umożliwia:
- pełną kontrolę nad warunkami w komorze wędzarniczej,
- monitorowanie w czasie rzeczywistym i wizualizację danych środowiskowych,
- sygnalizację stanów procesu za pomocą LEDów,
- generowanie raportów i alertów w przypadku błędów lub nieprawidłowych warunków.  

Projekt łączy w sobie elementy IoT, chmury i sterowania procesami, zapewniając bezpieczeństwo i optymalizację procesu wędzenia.
