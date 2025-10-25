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

1.  **INICJACJA PROCESU (Moduł I/O)**
    * Użytkownik klika przycisk START (Moduł I/O).
    * Moduł I/O → Sygnał Inicjujący do **Chmury**.

2.  **WALIDACJA WARUNKÓW (Chmura ↔ Moduł I/O)**
    * Chmura wyświetla **Czerwoną Lampkę Statusu** na wizualizacji (Oczekiwanie).
    * Chmura → Komenda: Sprawdź Czujniki (Drzwi/Okna) do **Modułu I/O**.
    * Moduł I/O → Status do Chmury.
    * **IF Warunek Niespełniony:** Moduł I/O zapala **Czerwoną Diodę LED** (Wstrzymanie).
    * **IF Warunek Spełniony:** Moduł I/O zapala **Zieloną Diodę LED** (Gotowość).

3.  **START SYMULACJI (Chmura → ESP32)**
    * Chmura → Flaga **START** + Tryb Wędzenia (np. Tryb 1: Ciepłe) do **Mikrokontrolera (ESP32)**.
    * ESP32 rozpoczyna symulację procesu.

4.  **MONITORING I KONTROLA ETAPÓW (Pętla)**
    * **A. Pomiar Danych:** WisBlock (Czujniki) → Dane Środowiskowe (Temp, Wilgotność, Ciśnienie, QA) do **Chmury**.
    * **B. Status Procesu:** ESP32 → Flaga Statusu (`ETAP_N`) do **Chmury**.
    * **C. Wizualizacja:** Chmura aktualizuje pasek postępu i wykresy.
    * **D. Sygnalizacja Etapu:** Chmura → Komenda: Zapal LED dla Etapu N do **Modułu I/O**.

5.  **ZAKOŃCZENIE PROCESU**
    * ESP32 → Flaga **KONIEC PROCESU** do **Chmury**.
    * Chmura → Pasek postępu na **100%**, Generowanie Raportu.
    * Chmura → Komenda: Zapal **Zielony, Stały LED** (Koniec) do **Modułu I/O**.


## 5. Instalacja

1. Skonfiguruj czujniki WisBlock Kit i podłącz je do odpowiednich pinów mikrokontrolera.
2. Skonfiguruj komunikację LoRaWAN i połączenie z bramą (Gateway).
3. Skonfiguruj chmurę do odbierania i analizy danych.
4. Implementuj panel wizualizacji w chmurze (wykresy, statusy czujników).
5. Przetestuj cały system, aby upewnić się, że proces wędzenia działa zgodnie z założeniami.

## 6. Podsumowanie

Projekt systemu monitorowania i symulacji procesu wędzenia pozwala na dokładne śledzenie warunków panujących w komorze wędzarniczej, oferując użytkownikowi pełną kontrolę nad procesem wędzenia. Zbieranie i analiza danych w czasie rzeczywistym oraz możliwość generowania alertów zapewniają bezpieczeństwo i optymalizację procesu wędzenia.
