# Projekt Systemu Monitorowania i Symulacji Procesu Wędzenia

## 1. Wprowadzenie

Celem projektu jest stworzenie inteligentnego systemu monitorującego i symulującego proces wędzenia z wykorzystaniem zestawu czujników WisBlock Kit 4-EU868 firmy RAKwireless oraz systemu chmurowego. Projekt ma na celu zebranie, analizę i wizualizację danych środowiskowych (temperatura, wilgotność, ciśnienie, jakość powietrza) w czasie rzeczywistym oraz symulację sterowania procesem wędzenia za pomocą mikrokontrolera (np. ESP32, STM32 lub Arduino).

## 2. Opis działania systemu

### 2.1. Inicjacja procesu wędzenia

Proces rozpoczyna się po naciśnięciu przycisku **START** przez użytkownika. System następnie sprawdza w chmurze status czujników drzwi i okien, aby upewnić się, że komora wędzarnicza jest zamknięta. Jeśli któreś z drzwi lub okien są otwarte, w chmurze pojawia się ostrzeżenie, a proces nie może zostać uruchomiony.

### 2.2. Pomiar i przesyłanie danych

Dane z czujników temperatury, wilgotności, ciśnienia i jakości powietrza są zbierane co minutę przez moduł RAKwireless WisBlock. Dane są następnie przesyłane za pośrednictwem LoRaWAN do Gateway, który przekazuje je do serwera chmurowego. W chmurze dane są analizowane i prezentowane użytkownikowi w formie wykresów i wskaźników w czasie rzeczywistym.

### 2.3. Tryby wędzenia

Użytkownik ma możliwość wyboru jednego z dwóch trybów wędzenia:
- **Tryb 1 – Wędzenie na ciepło**: temperatura 40–60°C, wilgotność 60–80%.
- **Tryb 2 – Wędzenie na gorąco**: temperatura 60–90°C, wilgotność 55–70%.

### 2.4. Przetwarzanie i wizualizacja danych w chmurze

Dane przesyłane do chmury są gromadzone w bazie danych, gdzie następnie są analizowane i wizualizowane na panelu użytkownika. Użytkownik ma dostęp do wykresów zmian temperatury, wilgotności, jakości powietrza i ciśnienia w czasie rzeczywistym. W przypadku przekroczenia dopuszczalnych wartości system generuje alerty lub powiadomienia. W chmurze możliwe jest również śledzenie historii procesów oraz generowanie raportów.

## 3. Podział obowiązków

Projekt realizowany jest przez 7-osobowy zespół. Proponowany podział zadań:
1. **Osoba 1** – Projekt i konfiguracja czujników WisBlock (temperatura, wilgotność, ciśnienie, powietrze).
2. **Osoba 2** – Implementacja modułu komunikacji LoRaWAN i transmisji danych do Gateway.
3. **Osoba 3** – Opracowanie logiki chmurowej (odbiór danych, analiza, wykrywanie błędów, alerty).
4. **Osoba 4** – Tworzenie panelu wizualizacji danych (dashboard online, wykresy, statusy czujników).
5. **Osoba 5** – Integracja czujników drzwi/okien i przycisku uruchamiającego proces.
6. **Osoba 6** – Symulacja sterowania procesem wędzenia (mikrokontroler – grzałka, dym, LEDy).
7. **Osoba 7** – Dokumentacja techniczna i integracja wszystkich modułów w jedną spójną całość.

## 4. Wymagania techniczne

- **Moduł RAKwireless WisBlock Kit 4-EU868** – pomiar temperatury, wilgotności, ciśnienia, jakości powietrza.
- **Gateway LoRaWAN** – transmisja danych do chmury.
- **Chmura** – analiza i wizualizacja danych w czasie rzeczywistym.
- **Mikrokontroler** (opcjonalnie ESP32 / STM32 / Arduino) – symulacja grzałki, dymu i sygnalizacji LED.
- **Czujniki drzwi i okien** – kontrola bezpieczeństwa procesu.
- **Moduł I/O** – inicjacja procesu wędzenia.

## 5. Przebieg procesu wędzenia (symulacja)

1. Użytkownik naciska przycisk **START**.
2. System sprawdza w chmurze status czujników drzwi i okien.
3. Jeżeli wszystkie czujniki wskazują zamknięcie, proces może się rozpocząć.
4. Dane z czujników środowiskowych są zbierane i przesyłane do chmury co jakiś czas.
5. Mikrokontroler symuluje proces nagrzewania i generowania dymu.
6. W chmurze wizualizowane są dane w czasie rzeczywistym (temperatura, wilgotność, ciśnienie, jakość powietrza).
7. Po osiągnięciu docelowych parametrów proces przechodzi w fazę stabilizacji.
8. Po zakończeniu wędzenia system generuje raport i zapisuje dane w chmurze.

```mermaid
graph TD
    subgraph START - Inicjacja
        A[Użytkownik klika przycisk Start na Wyspie IO] --> B{Wyspa IO wysyła żądanie do Chmury};
    end

    subgraph WALIDACJA - Sprawdzenie Warunków
        B --> C{Chmura otrzymuje żądanie};
        C -->|NIE MOŻNA WYKONAĆ - Warunek niespełniony| D[Chmura zapala Czerwoną Lampkę Statusu (Wizualizacja)];
        D --> E[Chmura wysyła żądanie Sprawdzenia Statusu do Wyspy IO];
        E --> F{Moduł IO sprawdza: Drzwi/Okna zamknięte?};
        F -->|NIE| G[Moduł IO zapala Czerwoną Lampkę (Błąd/Oczekiwanie)];
        F -->|TAK| H[Moduł IO zapala Zieloną Lampkę (Gotowość)];
    end

    subgraph PROCES - Symulacja
        H --> I{Chmura wysyła flagę START do ESP32};
        I --> J[ESP32 rozpoczyna symulację procesu];

        subgraph Monitoring i Aktualizacja Statusu
            K[ESP32: Generowanie i wysyłanie flag statusu (Etap N)] --> L(Chmura: Aktualizacja paska postępu/statusu);
            M[Czujniki: Pomiar Temp. i Wilgotności] --> L;
            L --> N[Chmura wysyła komendę LED dla Etapu N do Modułu IO];
            N --> O[Moduł IO: zaświeca odpowiedni LED dla Etapu Procesu];
        end
        O --> K; % Pętla: Kolejny Etap

    end

    subgraph KONIEC
        K -->|Flaga KONIEC PROCESU| P[Chmura: Aktualizacja paska postępu na 100%];
        P --> Q[Chmura wysyła komendę do Modułu IO];
        Q --> R[Moduł IO: zaświeca LED KONIEC PROCESU];
    end
```

## 6. Instalacja

1. Skonfiguruj czujniki WisBlock Kit i podłącz je do odpowiednich pinów mikrokontrolera.
2. Skonfiguruj komunikację LoRaWAN i połączenie z bramą (Gateway).
3. Skonfiguruj chmurę do odbierania i analizy danych.
4. Implementuj panel wizualizacji w chmurze (wykresy, statusy czujników).
5. Przetestuj cały system, aby upewnić się, że proces wędzenia działa zgodnie z założeniami.

## 7. Podsumowanie

Projekt systemu monitorowania i symulacji procesu wędzenia pozwala na dokładne śledzenie warunków panujących w komorze wędzarniczej, oferując użytkownikowi pełną kontrolę nad procesem wędzenia. Zbieranie i analiza danych w czasie rzeczywistym oraz możliwość generowania alertów zapewniają bezpieczeństwo i optymalizację procesu wędzenia.
