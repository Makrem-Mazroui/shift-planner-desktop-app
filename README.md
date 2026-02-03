# Shift Planner & On-Call Manager

A robust, offline desktop application built with Python and Tkinter for managing team shifts, on-call rotations, and weekend coverage. It generates a zero-dependency HTML dashboard that is easy to share and view on any device.

## 🚀 Key Features

* **Flexible Planning Modes:** Generate plans for **Shifts Only**, **On-Call Only**, or **Both** simultaneously.
* **Smart "Comp Day" Logic:** Automatically handles rest days (Comp Off) for weekend workers (defaulting to Thu/Fri, but customizable).
* **Integrated Holiday Engine:** Built-in public holiday calculation for **CZ, SK, DE, UK, US, FR, and PL**.
* **Conflict Resolution:** Tools to swap shifts, manage sick leave/absences, and backfill vacancies without breaking the schedule.
* **Portable HTML Output:** Generates a standalone `shift_plan.html` file that requires no special software to view.
* **Zero Dependencies:** Runs as a standalone executable on Windows and macOS.

## 🛠️ Installation & Building

You can run this tool as a raw Python script or build it into a standalone application.

For Mac check MAC README.md
For Windows check MAC README.md

## 📖 How to Use

### 1. Manage Members

* Add team members in the **Members** tab.
* Define preferences (e.g., "Early Only", "No On-Call") which the generator will respect.
* Data is saved locally to `members.json`.

### 2. Generate Plan

* Select your **Plan Type** and **Shift Configuration** (e.g., Early + Central + Late + Weekend).
* Choose the **Country** for holiday logic.
* Set staffing requirements (how many people needed per shift).
* Click **Generate Dashboard** to create the HTML schedule.

### 3. Swap / Edit

Real life happens. Use the third tab to:

* **Swap On-Call** duties between two weeks.
* **Swap Shifts** between two people in the same week.
* **Process Absences:** Mark a member as absent for a date range and assign replacements for their specific roles.
* **Backfill Vacancies:** Quickly fill open slots across a specific date range.

---

## 📂 Project Structure

* For Mac`shift-planner.app` and For Windows `shift-planner.exe`: The main application source code.
* `members.json`: Database of team members and preferences.
* `schedule_data.json`: Stores the current state of the generated schedule (allows for saving/loading).
* `shift_plan.html`: The visual output file generated for users.

## 👨‍💻 Developer

**Makrem Mazroui**

* **Contact:** makremmazroui@gmail.com

---
