# Tray Alerts icon
## Purpose
Small application to monitor state of air alert in Ukraine for selected region based on config file. App displays in tray icon with red color when there is alert and green when there is no alert.

| Color    | Meaning  |
| -------- | -------- | 
| Green   | No alert     | 
| Red    | Alert     | 
| Yellow | Error while parsing|
| Gray | Initial state, no alert info|
| Black | Network or API problem|


## Run application

python .\main.py 

## Build standalone app

 > pyinstaller --onefile --noconsole main.py

## Configuration file example

[server]
url = "https://ubilling.net.ua/aerialalerts/"
interval = 5

[place]
region = "м. Київ"

[settings]
notifications = True