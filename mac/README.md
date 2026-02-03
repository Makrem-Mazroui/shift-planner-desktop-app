# How to use the application:

**1st Method**
```
1- Download the zip file and unzip it
2- You should keep both files "Shift-Planner.app" and "shift-planner.pyc"
3- Double click "Shift-Planner.app" because I`am 'Unverified Developer' your mac will warn you about a malware (authorize or reject)
4- Create the list of members and enjoy the flexibility
```

**2nd Method**
```
1- Download the zip file and unzip it
2- You only need "shift-planner.pyc" file
3- Open your terminal and run the app as follow
$ python3 shift-planner.pyc
4- Create the list of members and enjoy the flexibility
```
**3rd Method**
```
1- Download the zip file and unzip it
2- You only need "shift-planner.pyc" file
```

**Creating the Mac App (Launch Icon)**
To allow macOS users to launch the tool without a terminal, create an App using Automator.
Steps:
1.	Open Automator (Cmd+Space, type "Automator").
2.	Choose Application → Choose.
3.	In the search bar, type Run AppleScript.
4.	Drag the Run AppleScript action into the right-side window.
5.	Delete all existing text in the box.
6.	Paste the code below exactly.
Automator Code (AppleScript)

```
AppleScript
-- 1. Find the folder where THIS app is located

tell application "Finder"
    set appFolder to (container of (path to me)) as text
    set unixFolder to POSIX path of appFolder
end tell

-- 2. Define the script path
set scriptName to "shift-planner.pyc"
set scriptPath to unixFolder & scriptName

-- 3. Check if the file actually exists
try
    do shell script "test -f " & quoted form of scriptPath
on error
    display dialog "ERROR: I cannot find '" & scriptName & "'." & return & return & "I looked in: " & unixFolder buttons {"OK"} with icon stop
    return
end try

-- 4. RUN THE APP
-- A) Put Homebrew paths FIRST (/opt/homebrew/bin) so we don't use the crashing system python.
-- B) 'cd' into the folder so the script finds your members.txt files.
set command to "export PATH=/opt/homebrew/bin:/usr/local/bin:$PATH; cd " & quoted form of unixFolder & "; nohup python3 shift-planner.pyc >/dev/null 2>&1 &"

try
    do shell script command
on error errMsg
    display dialog "Launch Error: " & errMsg buttons {"OK"} with icon stop
end try
```

Finalizing:
1.	Save the Automator file as ShiftPlanner.
2.	Move the resulting ShiftPlanner.app into the same folder as shift-plan-gui.py.
3.	Double-click to run.
