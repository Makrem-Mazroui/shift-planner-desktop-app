**You can copy just that .exe file to a USB drive, email it, or put it on a shared network drive, and it will run on other Windows computers even if they don't have Python installed.**

**For new build on Windows**
```
$ cd /XXX/XXXX/python.py
$ pip install pyinstaller
$ python -m PyInstaller --noconsole --onefile shift-planner.py
Go to your dist folder. You can now double-click shift-planner.app and it will open correctly.
You can even move it to your desktop and remove the rest of files
```
