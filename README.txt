## Build local
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pyinstaller --onefile --name cultivarte_wc_sync ^
  --hidden-import=mysql.connector.locales.eng.client_error ^
  --hidden-import=mysql.connector.locales.eng.numbers ^
  --hidden-import=mysql.connector.plugins.mysql_native_password ^
  --hidden-import=mysql.connector.plugins.caching_sha2_password ^
  sync_wc_orders.py