**For new build on MAC**

```
cd /XXX/XXXX/python.py
python3 -m venv build_env
source build_env/bin/activate
pip install pyinstaller
pyinstaller --noconsole --onedir --windowed shift-planner.py
deactivate
```

**For new build on Windows**
```
cd /XXX/XXXX/python.py
pip install pyinstaller
python -m PyInstaller --noconsole --onefile shift-planner.py
```

-Locate the App
