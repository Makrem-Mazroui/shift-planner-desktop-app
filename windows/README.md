**Create a Real Windows App (.exe)**
If you want a single file that works on any Windows computer (even ones without Python installed), 
you can turn your script into an .exe file. This is often cleaner than using batch files.

Open your terminal/command prompt.

Install PyInstaller: pip install pyinstaller

Navigate to your folder and run this command: pyinstaller --noconsole --onefile shift-plan-gui.py

This will create a dist folder containing shift-plan-gui.exe. You can send just that .exe file to anyone, and it will run your app.
