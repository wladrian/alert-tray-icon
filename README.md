# 🚨 Air Alert Status Monitor for Ukraine

A lightweight, cross-platform desktop application that monitors the operational status of air alerts in Ukraine for a specified region. The status is displayed visually via a system tray icon (e.g., Green for safe, Red for alert).

This project is designed for ease of use and minimal system resource consumption, providing real-time alerts based on external API data.

## 🚀 Features

*   **Real-time Monitoring:** Polls a specified API endpoint at a configurable interval.
*   **Visual Status Indicator:** Uses a system tray icon to display the current alert status color (Green, Red, etc.).
*   **Configurable:** All API endpoints, polling intervals, and target regions are managed via the `settings.ini` file.
*   **Robust Error Handling:** Differentiates between "No Alert," "Alert Detected," and various system/API errors (e.g., "Parsing Error," "Network Failure").

## ⚙️ Installation & Setup

Follow these steps to get the application running locally.

### Prerequisites

*   Python 3.8+
*   A functioning virtual environment (recommended)

### 1. Clone the Repository
```bash
git clone [repository-url]
cd tray-alerts-icon
```

### 2. Install Dependencies
The application relies on several external libraries. Install them using the following command:
```bash
pip install -r requirements.txt
```

### 3. Configure Settings
The application uses `settings.ini` to connect to the air alert API. You must customize this file:

`settings.ini`
```ini
[server]
# The base URL for the air alert API
url = "https://ubilling.net.ua/aerialalerts/"
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

### 🏃 Usage

To run the application:
```bash
python main.py
```

To create a standalone executable for Windows:
```bash
# Builds a single, self-contained executable
pyinstaller --onefile --noconsole main.py
```

## 🎨 Status Key

The system tray icon color visually represents the current alert status:

| Color | Meaning | Description |
| :--- | :--- | :--- |
| **🟢 Green** | **No Alert** | The monitoring system has confirmed no active alerts in the specified region. |
| **🔴 Red** | **Alert Detected** | Active air alert status has been received from the API. |
| **🟡 Yellow** | **Parsing Error** | The API responded, but the data structure was unexpected or incomplete. Manual investigation of the API is needed. |
| **⚫ Gray** | **Initial/No Data** | The application has initialized but has not yet received sufficient data to determine a status. |
| **⚫ Black** | **Connection Failure** | A persistent network issue or API connection failure occurred (e.g., DNS error, timeout). |

## 📖 Project Structure

- `main.py`: Contains the core application logic, managing polling threads and updating the tray icon.
- `settings.ini`: Configuration file for API details and region.
- `requirements.txt`: Lists all Python dependencies required for the project to run.

## 🤝 Contributing

We welcome contributions! If you find bugs or want to add features, please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/amazing-feature`).
3.  Commit your changes (`git commit -m 'feat: Add awesome feature'`).
4.  Push to the branch and open a Pull Request.


## 📄 License

This project is licensed under the [GNU GPL v3](LICENSE). See the [LICENSE](LICENSE) file for details.