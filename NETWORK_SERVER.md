# Network Server Quick Start Guide

## 1. How to run the server
Run the following in PowerShell:
```powershell
cd "c:\Users\SaadSayyed\Desktop\report (1)\report_base\report\"
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

This will start the server at http://192.168.18.55:8005/

## 2. Access from other devices
- From this computer: http://127.0.0.1:8005/ or http://localhost:8005/
- From other devices on network: http://192.168.18.55:8005/

## 3. Troubleshooting
If you have issues connecting:

1. Make sure your Windows firewall allows Django to accept incoming connections
   - Check Windows Security > Firewall & network protection > Allow an app through firewall
   - Make sure Python is allowed on Private networks

2. Verify network connectivity
   - From another device, try: ping 192.168.18.55
   
3. If you get "DisallowedHost" errors:
   - The ALLOWED_HOSTS setting in settings.py has been updated to allow connections
   - If still seeing errors, you might need to restart the server

4. To make the server use a different IP address:
   - Update Start.txt with the new IP address
   - Update the ALLOWED_HOSTS in oracle_db_project/settings.py