@echo off
python -m venv venv
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.
echo Python packages installed.
echo IMPORTANT: Install Tesseract OCR and Poppler separately, then add them to PATH.
echo Run run_windows.bat after that.
pause
