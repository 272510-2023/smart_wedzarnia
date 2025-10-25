# Projekt Systemu Monitorowania i Symulacji Procesu Wędzenia

## 1. Wprowadzenie

Celem projektu jest stworzenie inteligentnego systemu monitorującego i symulującego proces wędzenia z wykorzystaniem zestawu czujników WisBlock Kit 4-EU868 firmy RAKwireless oraz systemu chmurowego. Projekt ma na celu zebranie, analizę i wizualizację danych środowiskowych (temperatura, wilgotność, ciśnienie, jakość powietrza) w czasie rzeczywistym oraz symulację sterowania procesem wędzenia za pomocą mikrokontrolera (np. ESP32, STM32 lub Arduino).

## 2. Podział obowiązków

Projekt realizowany jest przez 7-osobowy zespół. Proponowany podział zadań:
1. **Osoba 1** – Projekt i konfiguracja czujników WisBlock (temperatura, wilgotność, ciśnienie, powietrze).
2. **Osoba 2** – Implementacja modułu komunikacji LoRaWAN i transmisji danych do Gateway.
3. **Osoba 3** – Opracowanie logiki chmurowej (odbiór danych, analiza, wykrywanie błędów, alerty).
4. **Osoba 4** – Tworzenie panelu wizualizacji danych (dashboard online, wykresy, statusy czujników).
5. **Osoba 5** – Integracja czujników drzwi/okien i przycisku uruchamiającego proces.
6. **Osoba 6** – Symulacja sterowania procesem wędzenia (mikrokontroler – grzałka, dym, LEDy).
7. **Osoba 7** – Dokumentacja techniczna i integracja wszystkich modułów w jedną spójną całość.

## 3. Wymagania techniczne

- **Moduł RAKwireless WisBlock Kit 4-EU868** – pomiar temperatury, wilgotności, ciśnienia, jakości powietrza.
- **Gateway LoRaWAN** – transmisja danych do chmury.
- **Chmura** – analiza i wizualizacja danych w czasie rzeczywistym.
- **Mikrokontroler** (opcjonalnie ESP32 / STM32 / Arduino) – symulacja grzałki, dymu i sygnalizacji LED.
- **Czujniki drzwi i okien** – kontrola bezpieczeństwa procesu.
- **Moduł I/O** – inicjacja procesu wędzenia.

## 4. Przebieg procesu wędzenia (symulacja)

========================================
1. INICJACJA PROCESU (Moduł I/O)
========================================
- Użytkownik naciska przycisk START.
- Moduł I/O wysyła sygnał inicjujący do Chmury.
- Chmura wie, że należy rozpocząć weryfikację warunków początkowych.

========================================
2. WALIDACJA WARUNKÓW (Chmura ↔ Moduł I/O)
========================================
- Chmura ustawia czerwoną lampkę statusu (Oczekiwanie) w wizualizacji.
- Chmura wysyła do Modułu I/O komendę: "Sprawdź czujniki drzwi i okien".
- Moduł I/O odczytuje stany czujników i zwraca status do Chmury.

- Jeżeli warunek niespełniony:
    - Moduł I/O zapala czerwoną diodę LED (Wstrzymanie procesu)
- Jeżeli warunek spełniony:
    - Moduł I/O zapala zieloną diodę LED (Gotowość do rozpoczęcia)

========================================
3. START SYMULACJI (Chmura → ESP32)
========================================
- Chmura wysyła do ESP32 flagę START oraz tryb wędzenia (np. Tryb 1: Ciepłe)
- ESP32 interpretuje dane i rozpoczyna symulację procesu

========================================
4. MONITORING I KONTROLA ETAPÓW (Pętla)
========================================
Pętla działa do zakończenia procesu:

    A. Pomiar danych środowiskowych:
        - Czujniki WisBlock przesyłają dane: temperatura, wilgotność, ciśnienie, QA do Chmury
        - Chmura agreguje dane i aktualizuje wykresy

    B. Status procesu:
        - ESP32 wysyła flagę STATUS_ETAP_N do Chmury
        - Chmura aktualizuje pasek postępu i wizualizację etapów

    C. Sygnalizacja świetlna:
        - Chmura wysyła komendę do Modułu I/O, aby zapalił LED dla bieżącego etapu

========================================
5. ZAKOŃCZENIE PROCESU
========================================
- ESP32 wysyła flagę KONIEC_PROCESU do Chmury
- Chmura:
    - Ustawia pasek postępu na 100%
    - Generuje raport podsumowujący proces
- Chmura wysyła do Modułu I/O komendę: zapal zielony, stały LED (koniec procesu)

## 5. Instalacja

1. Skonfiguruj czujniki WisBlock Kit i podłącz je do odpowiednich pinów mikrokontrolera.
2. Skonfiguruj komunikację LoRaWAN i połączenie z bramą (Gateway).
3. Skonfiguruj chmurę do odbierania i analizy danych.
4. Implementuj panel wizualizacji w chmurze (wykresy, statusy czujników).
5. Przetestuj cały system, aby upewnić się, że proces wędzenia działa zgodnie z założeniami.

## 6. Podsumowanie

Projekt systemu monitorowania i symulacji procesu wędzenia pozwala na dokładne śledzenie warunków panujących w komorze wędzarniczej, oferując użytkownikowi pełną kontrolę nad procesem wędzenia. Zbieranie i analiza danych w czasie rzeczywistym oraz możliwość generowania alertów zapewniają bezpieczeństwo i optymalizację procesu wędzenia.
