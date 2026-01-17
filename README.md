# Smoking Process Monitoring and Simulation System

## 1. Introduction

The goal of the project is to create an intelligent system for monitoring and simulating the smoking process using the WisBlock Kit 4-EU868 sensor set from RAKwireless and a cloud-based system.

The system enables:
- real-time collection of environmental data (temperature, humidity, pressure, air quality),
- data visualization in the form of charts and progress bars,
- simulation of smoking process control using a microcontroller (ESP32, STM32, or Arduino),
- monitoring of safety sensor states (doors, windows),
- light signaling of process stages.

---

## 2. Division of Responsibilities

The project is implemented by a 7-person team:

| Person | Task |
|--------|------|
| Person 1 | Design and configuration of WisBlock sensors (temperature, humidity, pressure, air quality) |
| Person 2 | Implementation of LoRaWAN communication module and data transmission to Gateway |
| Person 3 | Development of cloud logic (data reception, analysis, error detection, alerts) |
| Person 4 | Creation of data visualization panel (online dashboard, charts, sensor statuses) |
| Person 5 | Integration of door/window sensors and process start button |
| Person 6 | Simulation of smoking process control (heater, smoke, LEDs) |
| Person 7 | Technical documentation and integration of all modules into one cohesive whole |

---

## 3. Technical Requirements

- **WisBlock Kit 4-EU868 Module** – measurement of temperature, humidity, pressure, and air quality.
- **LoRaWAN Gateway** – data transmission to the cloud.
- **Cloud** – real-time analysis, visualization, and alert generation.
- **Microcontroller** (ESP32 / STM32 / Arduino) – heater simulation, smoke generation, LED control.
- **Door and window sensors** – process safety control.
- **I/O Module** – smoking process initiation and light signaling of stages.

---

## 4. Smoking Process Flow (Simulation)

### 4.1 Process Initiation (I/O Module)
- User presses the **START** button.
- I/O Module sends initialization signal to the cloud.
- Cloud begins verification of initial conditions.

### 4.2 Condition Validation (Cloud ↔ I/O Module)
- Cloud sets **red status light** (Waiting).
- Cloud sends command to I/O Module: "Check door and window sensors".
- I/O Module reads sensor states and returns status to cloud.

**Decision:**
- If condition **not met** → I/O Module lights **red LED** (Process halted).
- If condition **met** → I/O Module lights **green LED** (Ready).

### 4.3 Simulation Start (Cloud → ESP32)
- Cloud sends **START** flag and smoking mode (e.g., Mode 1: Hot) to ESP32.
- ESP32 interprets data and begins process simulation.

### 4.4 Monitoring and Stage Control (loop)
Process runs in a loop until simulation completion:

1. **Environmental Data Measurement:**
    - WisBlock sensors transmit temperature, humidity, pressure, AQ to cloud.
    - Cloud aggregates data and updates charts.

2. **Process Status:**
    - ESP32 sends `STATUS_STAGE_N` flag to cloud.
    - Cloud updates progress bar and stage visualization.

3. **Light Signaling:**
    - Cloud sends command to I/O Module to light LED for current stage.

### 4.5 Process Completion
- ESP32 sends `PROCESS_END` flag to cloud.
- Cloud:
  - Sets progress bar to **100%**
  - Generates process summary report.
- Cloud sends command to I/O Module: light **solid green LED** (process complete).

---

## 5. Installation and Configuration

1. Configure WisBlock sensors and connect them to the microcontroller.
2. Configure LoRaWAN communication and connection to Gateway.
3. Configure cloud for data reception, analysis, and visualization.
4. Implement visualization panel (online dashboard, charts, sensor statuses).
5. Test the entire system, ensuring the smoking process works correctly.

---

## 6. Summary

The smoking process monitoring and simulation system enables:
- full control over conditions in the smoking chamber,
- real-time monitoring and visualization of environmental data,
- process state signaling using LEDs,
- generation of reports and alerts in case of errors or incorrect conditions.

The project combines elements of IoT, cloud computing, and process control, ensuring safety and optimization of the smoking process.
