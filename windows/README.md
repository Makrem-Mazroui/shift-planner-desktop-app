**Create a file named Run_Windows.bat inside the same folder**

1- Download the "shift-planner.pyc" file
2- In the same directory create a file "Run_Windows.bat"
3- Open "Shift-Planner.bat" with Notepad (or your code editor), paste this code, and save it as "Shift-Planner.bat"
```
Code snippet
@echo off
:: 1. Move to the folder where this script is located
cd /d "%~dp0"

:: 2. Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python from python.org and check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b
)

:: 3. Run the GUI script
:: "start /b" runs it in the same window
:: "pythonw" (with a 'w') runs it without keeping a black console window open in the background
start "" pythonw shift-planner.pyc

exit
```

How it works for Windows Users:
1.	Double-Click: "Shift-Planner.bat"
2.	Auto-Check: It quickly checks if they have Python installed.
o	If NO: It pauses and tells them to install Python.
o	If YES: It launches your GUI immediately.
3.	Invisible Console: By using pythonw (instead of just python), the black command prompt window will close instantly, leaving only your nice GUI app open.
