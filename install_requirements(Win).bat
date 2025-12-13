@echo off
echo Installing project requirements...
echo.

python -m pip install --upgrade pip
python -m pip install customtkinter Pillow reportlab geopy

echo.
echo All requirements installed successfully.
pause
