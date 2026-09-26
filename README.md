# 🚨 Air Alert Status Monitor for Ukraine

A lightweight, cross-platform desktop application that monitors the operational status of air alerts in Ukraine for a specified region. The status is displayed visually via a system tray icon (e.g., Green for safe, Red for alert).

Idea was to have quickly visible state of Air alert as tray icon.

This project is designed for ease of use and minimal system resource consumption, providing real-time alerts based on external API data.

## WARNING:
> ❗❗❗ **Please, use _official source as primary source_ for alerts and do not rely only on this application**. 

Application provided AS IS, without any guarantee and use **non-official volunteer's APIs** to receive information about alerts. These sources do not provide any guarantee for accuracy or promptness of data. 

## 🚀 Features

*   **Real-time Monitoring:** Polls a specified API endpoint at a configurable interval.
*   **Visual Status Indicator:** Uses a system tray icon to display the current alert status color (Green, Red, etc.).
*   **Configurable:** All API endpoints, polling intervals, and target regions are managed via the `settings.ini` file.
*   **Robust Error Handling:** Differentiates between "No Alert," "Alert Detected," and various system/API errors (e.g., "Parsing Error," "Network Failure").

## ⚙️ Installation & Setup

Follow these steps to get the application running locally.

### Prerequisites

*   Python 3.13+
*   A functioning virtual environment (recommended)

### 1. Clone the Repository
```bash
git clone [repository-url]
cd tray-alerts-icon
```

### 2. Install Dependencies
The application relies on several external libraries. Install them using the following command (inside your virtual env):
```bash
pip install -r requirements.txt
```

### 3. Configure Settings
The application allow to configure region of monitoring and Alert provider in settings window.
Please, use proxy server to not abuse usage of free APIs.

|API Provder|Direct/Proxy|Posibilities|
|---|---|---|
|proxy.alerts.in.ua|Proxy|Levels of alerts, alerts for different levels of regions (currently app support only oblast level and Kyiv|
|proxy.ubilling.net.ua|Proxy|Just air alert, no alerts levels, only regions|
|ubilling.net.ua|Direct|Just air alert, no alerts levels, only regions|


Also you could use `settings.ini` manually change settings:

`settings.ini`
```ini
[server]
# Name of Alert API provider
name = "proxy.alerts.in.ua"
# How often (in seconds) the application should poll the API
interval = 5

[place]
# The specific region to monitor (e.g., "м. Київ")
region = "м. Київ"

[settings]
# Controls whether a notification toast should appear on alert detection
notifications = True
```
> 💡 **Note:** Ensure the `region` value matches the expected format from the API.

#### Supported regions:
| Region |
|---|
| Хмельницька область |
| Вінницька область |
| Рівненська область |
| Волинська область |
| Дніпропетровська область |
| Житомирська область |
| Закарпатська область |
| Запорізька область |
| Івано-Франківська область |
| Київська область |
| Кіровоградська область |
| Луганська область |
| Миколаївська область |
| Одеська область |
| Полтавська область |
| Сумська область |
| Тернопільська область |
| Харківська область |
| Херсонська область |
| Черкаська область |
| Чернігівська область |
| Чернівецька область |
| Львівська область |
| Донецька область |
| Автономна Республіка Крим |
| м. Севастополь |
| м. Київ |


### 🏃 Usage

To run the application:
```bash
python alert_tray_icon/main.py
```

To create a standalone executable for Windows:
```bash
# Builds a single, self-contained executable
pyinstaller --onefile --noconsole alert_tray_icon/main.py
```

## 🎨 Status Key

The system tray icon color visually represents the current alert status:

| Color          | Meaning                 | Description                                                                                                  |
|:---------------|:------------------------|:-------------------------------------------------------------------------------------------------------------|
| **🟢 Green**   | **No Alert**            | No active alerts in the specified region based on API response.                                              |
| **🔴 Crimson** | **Alert**    | Active air alert status has been received from the API. No data from API related to threat level received.   |
| **🔴 Red**     | **Alert: Red level**    | Active air alert status. Threat level is Red (high): ballistic missile, cruise missile, massive drone attack |
| **🟡 Yellow**  | **Alert: Yellow level** | Active air alert status. Threat level is Yellow (medium): drone attack                                       |
| **⚪ White**     | **Initial/No Data**     | The application has initialized but has not yet received sufficient data to determine a status.              |
| **⚫ Black**    | **Failure**  | A persistent network issue or API connection failure occurred (e.g., DNS error, timeout).                    |

## 📖 Project Structure

- `alert_tray_icon/main.py`: Start application.
- `alert_tray_icon/app.py`: Application bootstrap API polling worker and tray icon state updator.
- `alert_tray_icon/icon.py`: TrayIcon class and related structures.
- `alert_tray_icon/config.py`: Configuration class. Load/Save .ini file.
- `alert_tray_icon/worker.py`: PollingThread class responsible for execution of Alert API providers.
- `alert_tray_icon/providers/base.py`: Base class for AlertProvider
- `alert_tray_icon/providers/ubilling.py`: Provider class for API of `ubilling.net.ua/aerialalerts`
- `alert_tray_icon/providers/alerts.py`: Provider class for API of `alerts.in.ua`
- `settings.ini`: Configuration file for API details and region.
- `requirements.txt`: Lists all Python dependencies required for the project to run.
- `requirements-dev.txt`: Lists all Python dependencies required for the project to run, check and buid.

## 🤝 Contributing

We welcome contributions! If you find bugs or want to add features, please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/amazing-feature`).
3.  Commit your changes (`git commit -m 'feat: Add awesome feature'`).
4.  Push to the branch and open a Pull Request.


## 📄 License

This project is licensed under the [GNU GPL v3](LICENSE). See the [LICENSE](LICENSE) file for details.