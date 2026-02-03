**For new build on MAC**

```
$ cd /XXX/XXXX/python.py
$ python3 -m venv build_env
$ source build_env/bin/activate
$ pip install pyinstaller
$ pyinstaller --noconsole --onedir --windowed shift-planner.py
$ deactivate
Go to your dist folder. You can now double-click shift-planner.app and it will open correctly.
You can even move it to your desktop and remove the rest of files
```

**For new build on Windows**
```
$ cd /XXX/XXXX/python.py
$ pip install pyinstaller
$ python -m PyInstaller --noconsole --onefile shift-planner.py
Go to your dist folder. You can now double-click shift-planner.app and it will open correctly.
You can even move it to your desktop and remove the rest of files
```
