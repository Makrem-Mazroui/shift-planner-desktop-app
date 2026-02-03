import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import calendar
import sys
from datetime import datetime, timedelta

# --- UNIVERSAL PATH BLOCK ---
# This detects OS and sets the working directory to the folder containing the App/Exe
if getattr(sys, 'frozen', False):
    # We are running as a bundle (PyInstaller)
    if sys.platform == 'darwin':
        # MAC: The executable is deep inside .app/Contents/MacOS/
        # We go up 4 levels to find the folder holding the .app icon
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(sys.executable))))
    else:
        # WINDOWS: The executable is just a file (.exe)
        # We only need to go up 1 level (the folder containing the .exe)
        base_dir = os.path.dirname(sys.executable)
        
    os.chdir(base_dir)
else:
    # We are running as a normal python script (not packaged)
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
# ---------------------------

# --- CONSTANTS ---
FILES = {
    "members_txt": "members.txt",
    "members_json": "members.json",
    "data": "schedule_data.json",
    "html": "shift_plan.html" # Default fallback
}

# --- BACKEND LOGIC ---

# 1. Holiday Engine
def get_easter_date(year):
    """Calculates Western Easter Sunday."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return datetime(year, month, day)

def get_public_holidays(year, country_code="CZ"):
    holidays = {}
    easter = get_easter_date(year)
    
    def add(d, m, name):
        try: holidays[datetime(year, m, d)] = name
        except: pass

    def add_rel(days_offset, name):
        holidays[easter + timedelta(days=days_offset)] = name

    if country_code == "CZ":
        add(1, 1, "New Year"); add_rel(-2, "Good Friday"); add_rel(1, "Easter Monday")
        add(1, 5, "Labor Day"); add(8, 5, "Liberation Day"); add(5, 7, "Cyril/Methodius")
        add(6, 7, "Jan Hus"); add(28, 9, "St. Wenceslas"); add(28, 10, "Indep. Day")
        add(17, 11, "Freedom/Democracy"); add(24, 12, "Christmas Eve"); add(25, 12, "Christmas 1"); add(26, 12, "Christmas 2")
    elif country_code == "SK":
        add(1, 1, "Republic Day"); add(6, 1, "Epiphany"); add_rel(-2, "Good Friday"); add_rel(1, "Easter Monday")
        add(1, 5, "Labor Day"); add(8, 5, "Victory Day"); add(5, 7, "Cyril/Methodius"); add(29, 8, "SNP")
        add(1, 9, "Constitution"); add(15, 9, "Lady Sorrows"); add(1, 11, "All Saints"); add(17, 11, "Freedom")
        add(24, 12, "Christmas Eve"); add(25, 12, "Christmas 1"); add(26, 12, "Christmas 2")
    elif country_code == "DE":
        add(1, 1, "Neujahr"); add_rel(-2, "Karfreitag"); add_rel(1, "Ostermontag"); add(1, 5, "Tag der Arbeit")
        add_rel(39, "Himmelfahrt"); add_rel(50, "Pfingstmontag"); add(3, 10, "Deutsche Einheit")
        add(25, 12, "Weihnachten 1"); add(26, 12, "Weihnachten 2")
    elif country_code == "UK":
        add(1, 1, "New Year"); add_rel(-2, "Good Friday"); add_rel(1, "Easter Monday")
        add(1, 5, "May Bank Hol"); add(25, 12, "Christmas"); add(26, 12, "Boxing Day")
    elif country_code == "US":
        add(1, 1, "New Year"); add(4, 7, "Independence"); add(11, 11, "Veterans"); add(25, 12, "Christmas")
    elif country_code == "FR":
        add(1, 1, "Jour de l'an"); add_rel(1, "Pâques"); add(1, 5, "Travail"); add(8, 5, "Victoire")
        add_rel(39, "Ascension"); add_rel(50, "Pentecôte"); add(14, 7, "Nationale"); add(15, 8, "Assomption")
        add(1, 11, "Toussaint"); add(11, 11, "Armistice"); add(25, 12, "Noël")
    elif country_code == "PL":
        add(1, 1, "New Year"); add(6, 1, "Epiphany"); add_rel(1, "Easter Monday"); add(1, 5, "Labor Day")
        add(3, 5, "Constitution"); add_rel(60, "Corpus Christi"); add(15, 8, "Army Day"); add(1, 11, "All Saints")
        add(11, 11, "Independence"); add(25, 12, "Christmas"); add(26, 12, "Boxing Day")

    return holidays

def get_holidays_range(start_date, end_date, country="CZ"):
    years = range(start_date.year, end_date.year + 1)
    all_holidays = {}
    for y in years:
        all_holidays.update(get_public_holidays(y, country))
    return all_holidays

# 2. Data Management
def load_members():
    if not os.path.exists(FILES["members_json"]) and os.path.exists(FILES["members_txt"]):
        with open(FILES["members_txt"], "r") as f:
            names = [line.strip() for line in f.readlines() if line.strip()]
        members = [{"name": n, "pref": "Any", "oncall": True} for n in names]
        save_members(members)
        return members
    if not os.path.exists(FILES["members_json"]): return []
    with open(FILES["members_json"], "r") as f: return json.load(f)

def save_members(members):
    with open(FILES["members_json"], "w") as f: json.dump(members, f, indent=4)
    with open(FILES["members_txt"], "w") as f: f.write("\n".join([m["name"] for m in members]))

def load_schedule():
    if os.path.exists(FILES["data"]):
        with open(FILES["data"], "r") as f:
            data = json.load(f)
            # Safe conversion of strings back to datetime objects
            for s in data["shifts"]:
                if isinstance(s["start"], str):
                    s["start"] = datetime.strptime(s["start"], "%Y-%m-%d")
                if isinstance(s["end"], str):
                    s["end"] = datetime.strptime(s["end"], "%Y-%m-%d")
            # Ensure keys exist
            if "absences" not in data: data["absences"] = []
            if "comp_days" not in data: data["comp_days"] = [3, 4] # Default Thu/Fri
            return data
    return None

def save_schedule(shifts, year, plan_type, shift_config, times, staffing, country, absences=None, comp_days=None):
    serializable_shifts = []
    for s in shifts:
        s_copy = s.copy()
        if isinstance(s["start"], datetime):
            s_copy["start"] = s["start"].strftime("%Y-%m-%d")
        if isinstance(s["end"], datetime):
            s_copy["end"] = s["end"].strftime("%Y-%m-%d")
        serializable_shifts.append(s_copy)
    
    if absences is None: absences = []
    
    # Default Comp Days: Thursday (3) and Friday (4) if not provided
    if comp_days is None: comp_days = [3, 4]

    data = {
        "year": year, 
        "plan_type": plan_type, 
        "shift_config": shift_config,
        "times": times, 
        "staffing": staffing, 
        "country": country,
        "shifts": serializable_shifts,
        "absences": absences,
        "comp_days": comp_days
    }
    with open(FILES["data"], "w") as f: json.dump(data, f, indent=4)

def render_html(shifts, year, plan_type, shift_config, times, holidays, absences=None, comp_days=None):
    if absences is None: absences = []
    if comp_days is None: comp_days = [3, 4]
    
    is_shift_mode = plan_type in ["shift-plan", "both"]
    is_oncall_mode = plan_type in ["oncall", "both"]
    show_early = is_shift_mode and ("Early" in shift_config)
    show_central = is_shift_mode and ("Central" in shift_config)
    show_late = is_shift_mode and ("Late" in shift_config)
    show_weekend = is_shift_mode and ("Weekend" in shift_config)
    show_oncall = is_oncall_mode

    ROLE_COLORS = {
        "Early": "#fff9c4",
        "Central": "#ffe0b2",
        "Late": "#d6d6d6",
        "Weekend": "#a8e6cf",
        "On-Call": "#d63031"
    }

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; text-align: center; background-color: #f4f7f6; padding: 20px; }}
        .header-title {{ font-size: 32px; font-weight: bold; margin-bottom: 5px; color: #2c3e50; }}
        .legend-container {{ background: white; padding: 15px; margin: 0 auto 30px auto; max-width: 1000px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); display: flex; flex-direction: column; gap: 10px; align-items: center; }}
        .legend-row {{ display: flex; gap: 15px; flex-wrap: wrap; justify-content: center; }}
        .role-badge {{ font-weight: bold; padding: 4px 10px; border-radius: 4px; color: black; font-size: 13px; border: 1px solid #ccc; }}
        
        .calendar-container {{ 
            width: 100%;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        
        .month-box {{ 
            background: white; 
            margin-bottom: 40px; 
            border-radius: 8px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.1); 
            overflow: hidden;
            width: fit-content;
        }}
        
        .month-name {{ 
            background-color: #34495e; 
            color: white; 
            font-weight: bold; 
            font-size: 22px; 
            padding: 10px; 
            text-align: left; 
            padding-left: 20px; 
        }}
        
        .month-table {{ 
            border-collapse: collapse; 
            width: auto; 
            margin: 0;
            font-size: 12px; 
            table-layout: fixed; 
        }}
        
        .month-table th, .month-table td {{ 
            border: 2px solid #bdc3c7; 
            padding: 6px; 
            text-align: center; 
            vertical-align: middle; 
        }}
        
        .col-role {{ width: 60px; font-weight: bold; font-size: 11px; }}
        
        .col-names {{ 
            width: 380px; 
            text-align: left; 
            padding-left: 10px; 
            white-space: normal; 
            line-height: 1.4; 
        }}
        
        .col-week {{ 
            width: 50px; 
            font-size: 38px;
            font-weight: bold; 
            color: #d63031; 
            background: #fff5f5; 
            border-bottom: 3px solid #34495e !important; 
            vertical-align: middle !important;
        }}
        
        .col-day {{ width: 40px; }}
        
        .day-header {{ 
            background-color: #3498db; 
            font-weight: bold; 
            color: white; 
        }}
        
        .date-cell {{ color: #2d3436; font-size: 13px; }}
        .empty-cell {{ background-color: #fdfdfd; }}
        .time-label {{ display: block; font-size: 9px; color: #555; margin-top: 2px; }}
        
        .weekend-non-working {{
            background-color: #636e72 !important;
            color: #b2bec3;
        }}
        
        .oncall-row .col-role {{ background-color: #d63031 !important; color: white !important; }}
        .oncall-row .col-role .time-label {{ color: #ffcccc !important; }}
        
        .oncall-row .date-cell, .oncall-row .empty-cell {{ 
            background-color: #d63031;
            color: white;
            font-weight: bold;
            border-color: #d63031;
        }}
        
        .divider td {{ border-bottom: 3px solid #34495e !important; }}
        
        .holiday-cell {{ 
            color: #0984e3 !important;
            font-weight: bold; 
            cursor: help; 
            background-color: #eaf2f8;
        }}

        .absence-section {{
            padding: 10px 20px;
            background-color: #fff8f8;
            border-top: 2px solid #bdc3c7;
            text-align: left;
        }}
        .absence-title {{
            font-size: 14px;
            font-weight: bold;
            color: #c0392b;
            margin-bottom: 5px;
            text-transform: uppercase;
        }}
        .absence-item {{
            font-size: 13px;
            color: #555;
            margin-bottom: 3px;
            padding-left: 10px;
            border-left: 3px solid #c0392b;
        }}
    </style>
    </head>
    <body>
        <div class="header-title">Shift & On-Call Schedule {year}</div>
        
        <div class="legend-container">
            <div class="legend-row">
                {f'<span class="role-badge" style="background:{ROLE_COLORS["Early"]}">Early ({times["early_s"]}-{times["early_e"]})</span>' if show_early else ''}
                {f'<span class="role-badge" style="background:{ROLE_COLORS["Central"]}">Central ({times["central_s"]}-{times["central_e"]})</span>' if show_central else ''}
                {f'<span class="role-badge" style="background:{ROLE_COLORS["Late"]}">Late ({times["late_s"]}-{times["late_e"]})</span>' if show_late else ''}
                {f'<span class="role-badge" style="background:{ROLE_COLORS["Weekend"]}">Weekend ({times["weekend_s"]}-{times["weekend_e"]})</span>' if show_weekend else ''}
                {f'<span class="role-badge" style="background:{ROLE_COLORS["On-Call"]}; color:white;">On-Call ({times["oncall_s"]}-{times["oncall_e"]})</span>' if show_oncall else ''}
                <span class="role-badge" style="background:#eaf2f8; color:#0984e3; border:1px solid #0984e3">PH = Public Holiday</span>
                <span class="role-badge" style="background:#ff0000; color:white; border:1px solid red">VACANT = Unassigned</span>
                <span class="role-badge" style="background:#b2bec3; color:white;">OFF = Comp Day</span>
                <span class="role-badge" style="background:#ff0000; color:white; border:1px solid red">V-OFF = Vacant Comp Day</span>
            </div>
        </div>
        
        <div class="calendar-container">
    """

    months_data = {}
    for s in shifts:
        m_key = (s['start'].year, s['start'].month)
        if m_key not in months_data: months_data[m_key] = []
        months_data[m_key].append(s)

    for (y, m), m_shifts in sorted(months_data.items()):
        month_name = calendar.month_name[m]
        last_day = calendar.monthrange(y, m)[1]
        m_start_dt = datetime(y, m, 1)
        m_end_dt = datetime(y, m, last_day)
        
        month_absences = []
        for rec in absences:
            try:
                # Assuming format "d-m-Y"
                a_start = datetime.strptime(rec['start'], "%d-%m-%Y")
                a_end = datetime.strptime(rec['end'], "%d-%m-%Y")
                if a_start <= m_end_dt and a_end >= m_start_dt:
                    month_absences.append(rec)
            except: pass

        html += f"""
        <div class="month-box">
            <div class="month-name">{month_name} {y}</div>
            <table class="month-table">
                <tr class="day-header">
                    <td class="col-role">Role</td>
                    <td class="col-names">Member(s)</td>
                    <td class="col-day">Mon</td>
                    <td class="col-day">Tue</td>
                    <td class="col-day">Wed</td>
                    <td class="col-day">Thu</td>
                    <td class="col-day">Fri</td>
                    <td class="col-day">Sat</td>
                    <td class="col-day">Sun</td>
                    <td class="col-week">Week</td>
                </tr>
        """
        for s in m_shifts:
            start_day = s['start']
            wk = s['week_num']
            weekend_worker_name = s.get('weekend', "")
            
            def get_day_cells(role_type, assigned_names):
                c = ""
                for i in range(7):
                    d = start_day + timedelta(days=i)
                    is_weekend = (d.weekday() >= 5) # FIX: Use weekday() not index
                    hol_name = holidays.get(d)
                    classes = ["date-cell"]
                    cell_style = ""
                    cell_content = f"{d.day} PH" if hol_name else f"{d.day}"
                    
                    # --- COMP DAY LOGIC ---
                    if role_type in ["Early", "Central", "Late"]:
                        # Check if weekend worker is in this role
                        is_ww_in_role = False
                        if isinstance(assigned_names, list):
                            if weekend_worker_name in assigned_names: is_ww_in_role = True
                        elif assigned_names == weekend_worker_name:
                            is_ww_in_role = True
                        
                        # If this is a Holiday, it takes priority visually (standard blue)
                        if hol_name:
                            classes.append("holiday-cell")
                        elif is_weekend:
                            classes.append("weekend-non-working")
                        else:
                            # FIX: Use d.weekday() instead of loop index 'i' to correctly identify day
                            if is_ww_in_role and (d.weekday() in comp_days):
                                # Determine if covered by someone else
                                is_mixed = False
                                is_fully_covered = False
                                
                                if isinstance(assigned_names, list) and len(assigned_names) > 1:
                                    is_mixed = True
                                    is_fully_covered = True # At least one person remains
                                elif isinstance(assigned_names, list) and len(assigned_names) == 1:
                                    is_fully_covered = False
                                else:
                                    is_fully_covered = False
                                
                                if is_mixed:
                                    cell_content = f"<span style='color:#c0392b; font-weight:bold; font-size:11px;'>{weekend_worker_name}<br>OFF</span>"
                                elif is_fully_covered:
                                    classes.append("weekend-non-working")
                                    cell_content = "OFF"
                                else:
                                    # Vacant because WW is off and no one else is there
                                    cell_style = "background-color: #ff0000; color: white; font-weight: bold;"
                                    cell_content = "V-OFF"

                    elif role_type == "Weekend":
                        if not is_weekend: 
                            classes.append("empty-cell") 
                        else:
                            cell_style = f"background-color: {ROLE_COLORS['Weekend']};"
                            if hol_name: classes.append("holiday-cell")
                    
                    class_str = " ".join(classes)
                    title_attr = f"title='{hol_name}'" if hol_name else ""
                    style_attr = f"style='{cell_style}'" if cell_style else ""

                    c += f"<td class='{class_str}' {style_attr} {title_attr}>{cell_content}</td>"
                return c

            visible_rows = [r for r in [show_early, show_central, show_late, show_weekend, show_oncall] if r]
            rowspan = len(visible_rows)
            first_row = True
            
            last_visible_role = ""
            if show_oncall: last_visible_role = "On-Call"
            elif show_weekend: last_visible_role = "Weekend"
            elif show_late: last_visible_role = "Late"
            elif show_central: last_visible_role = "Central"
            elif show_early: last_visible_role = "Early"

            def render_row(label, name_val, is_list=False, time_str=""):
                nonlocal first_row
                classes = []
                if label == last_visible_role: classes.append("divider")
                if label == "On-Call": classes.append("oncall-row")
                class_str = f"class='{' '.join(classes)}'" if classes else ""
                
                role_bg = ROLE_COLORS.get(label, "#ffffff")
                style_role = f"background-color: {role_bg};" if label != "On-Call" else ""
                
                h = f"<tr {class_str}>"
                h += f"<td class='col-role' style='{style_role}'>{label}<br><span class='time-label'>{time_str}</span></td>"
                
                if is_list and isinstance(name_val, list):
                    val_display = ", ".join(name_val)
                elif isinstance(name_val, list): 
                    val_display = ", ".join(name_val)
                else:
                    val_display = str(name_val)

                if not val_display: val_display = "VACANT"
                
                style_name = f"background-color: {role_bg}; color: #333;"
                if label == "On-Call":
                    style_name = "background-color: #d63031; color: white; font-weight: bold; border-color: #d63031;"
                
                if "VACANT" in val_display:
                     style_name = "background-color: #ff0000; color: white; font-weight: bold; font-size: 14px;"

                h += f"<td class='col-names' style='{style_name}'>{val_display}</td>"
                h += get_day_cells(label, name_val)
                
                if first_row:
                    h += f"<td rowspan='{rowspan}' class='col-week'>{wk}</td>"
                    first_row = False
                h += "</tr>"
                return h

            if show_early:
                e = s.get('early', 'VACANT')
                if not e: e = "VACANT"
                html += render_row("Early", e, isinstance(e, list), f"{times['early_s']}-{times['early_e']}")
            if show_central:
                c = s.get('central', [])
                if not c: c = "VACANT" 
                html += render_row("Central", c, True, f"{times['central_s']}-{times['central_e']}")
            if show_late:
                l = s.get('late', 'VACANT')
                if not l: l = "VACANT"
                html += render_row("Late", l, isinstance(l, list), f"{times['late_s']}-{times['late_e']}")
            if show_weekend:
                w = s.get('weekend', 'VACANT')
                if not w: w = "VACANT"
                html += render_row("Weekend", w, isinstance(w, list), f"{times['weekend_s']}-{times['weekend_e']}")
            if show_oncall:
                o = s.get('oncall', 'VACANT')
                if not o: o = "VACANT"
                html += render_row("On-Call", o, False, f"{times['oncall_s']}-{times['oncall_e']}")

        html += "</table>"
        
        if month_absences:
            html += """<div class="absence-section"><div class="absence-title">Notes / Absences:</div>"""
            for rec in month_absences:
                html += f"""<div class="absence-item"><b>{rec['name']}</b>: {rec['start']} to {rec['end']} ({rec['reason']})</div>"""
            html += "</div>"
            
        html += "</div>" 

    html += "</div></body></html>"
    filename = f"shift_plan_{year}.html"
    with open(filename, "w") as f: f.write(html)
    return filename

# --- FRONTEND (GUI) ---

class ShiftPlannerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Shift Planner & OnCall Manager (v1.0)")
        self.geometry("950x950")
        self.members = load_members()
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=(10, 0))
        
        self.tab_members = ttk.Frame(self.notebook)
        self.tab_gen = ttk.Frame(self.notebook)
        self.tab_swap = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_members, text="1. Members")
        self.notebook.add(self.tab_gen, text="2. Generate Plan")
        self.notebook.add(self.tab_swap, text="3. Swap / Edit")
        
        self.setup_members_tab()
        self.setup_generate_tab()
        self.setup_swap_tab()
        
        self.load_initial_config()

        sig_frame = ttk.Frame(self)
        sig_frame.pack(side="bottom", fill="x", padx=15, pady=8)
        lbl_sig = tk.Label(sig_frame, text="E-mail: makremmazroui@gmail.com | Developer: Makrem Mazroui", 
                           font=("Arial", 9, "italic"), fg="#777")
        lbl_sig.pack(side="right")

    def load_initial_config(self):
        data = load_schedule()
        if not data: return
        
        if "country" in data:
            self.combo_country.set(data["country"])
        
        if "staffing" in data:
            if "early" in data["staffing"]:
                self.spin_early_count.set(data["staffing"]["early"])
            if "late" in data["staffing"]:
                self.spin_late_count.set(data["staffing"]["late"])
        
        if "plan_type" in data:
            self.var_type.set(data["plan_type"])
        
        if "shift_config" in data:
            self.combo_shifts.set(data["shift_config"])
        
        if "comp_days" in data and len(data["comp_days"]) == 2:
            d1, d2 = data["comp_days"]
            days_map_inv = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday"}
            self.combo_comp1.set(days_map_inv.get(d1, "Thursday"))
            self.combo_comp2.set(days_map_inv.get(d2, "Friday"))

        self.update_visibility()

    # --- TAB 1: MEMBERS ---
    def setup_members_tab(self):
        frame = ttk.LabelFrame(self.tab_members, text="Manage Team Members", padding=20)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.lst_members = tk.Listbox(frame, height=15, font=("Arial", 10))
        self.lst_members.pack(fill="both", expand=True, pady=5)
        self.lst_members.bind('<<ListboxSelect>>', self.on_member_select)
        
        self.refresh_member_list()
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=5)
        self.entry_name = ttk.Entry(btn_frame)
        self.entry_name.pack(side="left", fill="x", expand=True, padx=5)
        
        ttk.Button(btn_frame, text="Add", command=self.add_member).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Update / Rename", command=self.rename_member).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Remove", command=self.remove_member).pack(side="left", padx=2)

    def refresh_member_list(self):
        self.lst_members.delete(0, tk.END)
        for m in self.members: self.lst_members.insert(tk.END, m["name"])

    def on_member_select(self, event):
        sel = self.lst_members.curselection()
        if sel:
            idx = sel[0]
            name = self.members[idx]["name"]
            self.entry_name.delete(0, tk.END)
            self.entry_name.insert(0, name)

    def add_member(self):
        name = self.entry_name.get().strip()
        if name:
            self.members.append({"name": name, "pref": "Any", "oncall": True})
            save_members(self.members)
            self.refresh_member_list()
            self.refresh_pref_table()
            self.entry_name.delete(0, tk.END)
            
            if os.path.exists(FILES["data"]):
                data = load_schedule()
                if not data: return
                vacant_count = 0
                for s in data["shifts"]:
                    for r in ['early', 'late', 'central', 'oncall', 'weekend']:
                        val = s.get(r)
                        if val == "VACANT": vacant_count += 1
                        elif isinstance(val, list) and "VACANT" in val: vacant_count += 1
                
                if vacant_count > 0:
                    if messagebox.askyesno("Update Schedule", 
                                           f"Added '{name}'. Found {vacant_count} VACANT slots.\nAssign new member to fill them?"):
                        for s in data["shifts"]:
                            for r in ['early', 'late', 'central', 'oncall', 'weekend']:
                                val = s.get(r)
                                if val == "VACANT":
                                    s[r] = name
                                elif isinstance(val, list) and "VACANT" in val:
                                    val.remove("VACANT")
                                    val.append(name)
                                    s[r] = val
                        
                        holidays = get_holidays_range(data["shifts"][0]["start"], data["shifts"][-1]["end"], data.get("country", "CZ"))
                        # FIX: Pass comp_days
                        save_schedule(data["shifts"], data["year"], data["plan_type"], data["shift_config"], data["times"], data.get("staffing"), data.get("country", "CZ"), data.get("absences", []), data.get("comp_days"))
                        render_html(data["shifts"], data["year"], data["plan_type"], data["shift_config"], data["times"], holidays, data.get("absences", []), data.get("comp_days"))
                        messagebox.showinfo("Success", f"Assigned '{name}' to {vacant_count} slots.")

    def rename_member(self):
        sel = self.lst_members.curselection()
        if not sel: return
        old_name = self.members[sel[0]]["name"]
        new_name = self.entry_name.get().strip()
        
        if not new_name or new_name == old_name: return
        self.members[sel[0]]["name"] = new_name
        save_members(self.members)
        self.refresh_member_list()
        self.refresh_pref_table()
        
        if os.path.exists(FILES["data"]):
            ans = messagebox.askyesno("Update Schedule?", f"Rename '{old_name}' to '{new_name}' in current schedule?")
            if ans:
                data = load_schedule()
                if data:
                    def replace_val(val):
                        if isinstance(val, list):
                            return [new_name if x == old_name else x for x in val]
                        return new_name if val == old_name else val

                    for s in data["shifts"]:
                        for r in ['early', 'late', 'central', 'oncall', 'weekend']:
                            if s.get(r): s[r] = replace_val(s[r])
                    
                    holidays = get_holidays_range(data["shifts"][0]["start"], data["shifts"][-1]["end"], data.get("country", "CZ"))
                    # FIX: Pass comp_days
                    save_schedule(data["shifts"], data["year"], data["plan_type"], data["shift_config"], data["times"], data.get("staffing"), data.get("country", "CZ"), data.get("absences", []), data.get("comp_days"))
                    render_html(data["shifts"], data["year"], data["plan_type"], data["shift_config"], data["times"], holidays, data.get("absences", []), data.get("comp_days"))
                    messagebox.showinfo("Success", "Renamed.")

    def remove_member(self):
        sel = self.lst_members.curselection()
        if not sel: return
        name_to_remove = self.members[sel[0]]["name"]
        
        if not messagebox.askyesno("Confirm", f"Remove '{name_to_remove}'?"):
            return

        self.members.pop(sel[0])
        save_members(self.members)
        self.refresh_member_list()
        self.refresh_pref_table()
        self.entry_name.delete(0, tk.END)

        if os.path.exists(FILES["data"]):
            data = load_schedule()
            if not data: return
            
            if messagebox.askyesno("Update Schedule", f"Mark '{name_to_remove}' slots as VACANT in current plan?"):
                for s in data["shifts"]:
                    for r in ['early', 'late', 'central', 'oncall', 'weekend']:
                        val = s.get(r)
                        if not val: continue
                        if isinstance(val, list):
                            if name_to_remove in val:
                                val.remove(name_to_remove)
                                s[r] = val
                        else:
                            if val == name_to_remove:
                                s[r] = "VACANT"
                
                holidays = get_holidays_range(data["shifts"][0]["start"], data["shifts"][-1]["end"], data.get("country", "CZ"))
                # FIX: Pass comp_days
                save_schedule(data["shifts"], data["year"], data["plan_type"], data["shift_config"], data["times"], data.get("staffing"), data.get("country", "CZ"), data.get("absences", []), data.get("comp_days"))
                render_html(data["shifts"], data["year"], data["plan_type"], data["shift_config"], data["times"], holidays, data.get("absences", []), data.get("comp_days"))
                messagebox.showinfo("Done", "Removed and marked VACANT.")

    # --- TAB 2: GENERATE ---
    def setup_generate_tab(self):
        main_scroll = ttk.Frame(self.tab_gen)
        main_scroll.pack(fill="both", expand=True)
        
        self.config_frame = ttk.LabelFrame(main_scroll, text="1. Configuration", padding=10)
        self.config_frame.pack(fill="x", padx=10, pady=5)
        
        f1 = ttk.Frame(self.config_frame)
        f1.pack(fill="x", pady=2)
        ttk.Label(f1, text="Plan Type:").pack(side="left")
        self.var_type = tk.StringVar(value="both")
        ttk.Radiobutton(f1, text="Both", variable=self.var_type, value="both", command=self.update_visibility).pack(side="left", padx=5)
        ttk.Radiobutton(f1, text="Shift Only", variable=self.var_type, value="shift-plan", command=self.update_visibility).pack(side="left", padx=5)
        ttk.Radiobutton(f1, text="On-Call Only", variable=self.var_type, value="oncall", command=self.update_visibility).pack(side="left", padx=5)
        
        f2 = ttk.Frame(self.config_frame)
        f2.pack(fill="x", pady=2)
        self.lbl_combo = ttk.Label(f2, text="Shift Combo:")
        self.lbl_combo.pack(side="left")
        self.combo_shifts = ttk.Combobox(f2, state="readonly", width=40)
        self.combo_shifts['values'] = [
            "Early + Central + Late", 
            "Early + Central + Late + Weekend",
            "Early + Central", 
            "Early + Late", 
            "Central + Late",
            "Central Only"
        ]
        self.combo_shifts.current(0)
        self.combo_shifts.pack(side="left", padx=5)
        self.combo_shifts.bind("<<ComboboxSelected>>", lambda e: self.update_visibility())

        f3 = ttk.Frame(self.config_frame)
        f3.pack(fill="x", pady=2)
        ttk.Label(f3, text="Start (01Feb2026):").pack(side="left")
        self.entry_date = ttk.Entry(f3, width=12)
        self.entry_date.insert(0, datetime.now().strftime("%d%b%Y"))
        self.entry_date.pack(side="left", padx=5)
        ttk.Label(f3, text="Months:").pack(side="left")
        self.spin_duration = ttk.Spinbox(f3, from_=1, to=12, width=3)
        self.spin_duration.set(6)
        self.spin_duration.pack(side="left", padx=5)
        
        ttk.Label(f3, text="Country:").pack(side="left", padx=(15, 5))
        self.combo_country = ttk.Combobox(f3, state="readonly", width=5)
        self.combo_country['values'] = ["CZ", "SK", "DE", "UK", "US", "FR", "PL"]
        self.combo_country.set("CZ")
        self.combo_country.pack(side="left")

        self.comp_container = ttk.Frame(main_scroll)
        self.comp_container.pack(fill="x", padx=10, pady=0)
        
        self.comp_frame = ttk.LabelFrame(self.comp_container, text="Weekend Worker Comp Off (Days to Rest)", padding=5)
        
        ttk.Label(self.comp_frame, text="Day 1:").pack(side="left")
        self.combo_comp1 = ttk.Combobox(self.comp_frame, state="readonly", width=12, values=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        self.combo_comp1.set("Thursday")
        self.combo_comp1.pack(side="left", padx=5)
        
        ttk.Label(self.comp_frame, text="Day 2:").pack(side="left")
        self.combo_comp2 = ttk.Combobox(self.comp_frame, state="readonly", width=12, values=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        self.combo_comp2.set("Friday")
        self.combo_comp2.pack(side="left", padx=5)

        self.pref_frame = ttk.LabelFrame(main_scroll, text="2. Member Preferences & Availability", padding=10)
        self.pref_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        canvas = tk.Canvas(self.pref_frame)
        scrollbar = ttk.Scrollbar(self.pref_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.refresh_pref_table()

        bottom_frame = ttk.Frame(main_scroll)
        bottom_frame.pack(fill="x", padx=10, pady=5)
        
        self.staff_frame = ttk.LabelFrame(bottom_frame, text="3. Staffing Counts", padding=5)
        self.staff_frame.pack(fill="x", pady=5)
        self.lbl_early = ttk.Label(self.staff_frame, text="Early:")
        self.lbl_early.pack(side="left")
        self.spin_early_count = ttk.Spinbox(self.staff_frame, from_=0, to=10, width=3)
        self.spin_early_count.set(1)
        self.spin_early_count.pack(side="left", padx=5)
        
        self.lbl_late = ttk.Label(self.staff_frame, text="Late:")
        self.lbl_late.pack(side="left")
        self.spin_late_count = ttk.Spinbox(self.staff_frame, from_=0, to=10, width=3)
        self.spin_late_count.set(1)
        self.spin_late_count.pack(side="left", padx=5)
        self.lbl_remainder = ttk.Label(self.staff_frame, text="(Remainder -> Central)", foreground="gray")
        self.lbl_remainder.pack(side="left", padx=10)

        self.time_frame = ttk.LabelFrame(bottom_frame, text="4. Timings", padding=5)
        self.time_frame.pack(fill="x", pady=5)
        self.time_rows = {}
        def add_time_row(key, c_idx, label, def_s, def_e):
            f = ttk.Frame(self.time_frame)
            f.grid(row=0, column=c_idx, padx=10)
            widgets = []
            l = ttk.Label(f, text=label)
            l.pack(side="left")
            widgets.append(l)
            e_s = ttk.Entry(f, width=5)
            e_s.insert(0, def_s)
            e_s.pack(side="left")
            widgets.append(e_s)
            ttk.Label(f, text="-").pack(side="left")
            e_e = ttk.Entry(f, width=5)
            e_e.insert(0, def_e)
            e_e.pack(side="left")
            widgets.append(e_e)
            self.time_rows[key] = f
            return e_s, e_e

        self.t_early_s, self.t_early_e = add_time_row("early", 0, "Early", "07:00", "15:30")
        self.t_central_s, self.t_central_e = add_time_row("central", 1, "Central", "09:00", "17:30")
        self.t_late_s, self.t_late_e = add_time_row("late", 2, "Late", "10:30", "19:00")
        self.t_weekend_s, self.t_weekend_e = add_time_row("weekend", 3, "Weekend", "09:00", "17:00")
        self.t_oncall_s, self.t_oncall_e = add_time_row("oncall", 4, "On-Call", "17:30", "08:00")

        ttk.Button(bottom_frame, text="GENERATE DASHBOARD", command=self.generate_plan).pack(fill="x", pady=10)
        self.update_visibility()

    def refresh_pref_table(self):
        if hasattr(self, 'pref_widgets'): self.save_current_prefs()
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()
        mode = self.var_type.get()
        combo = self.combo_shifts.get()
        
        show_shifts = mode != "oncall"
        show_oncall = mode != "shift-plan"
        
        col = 0
        ttk.Label(self.scrollable_frame, text="Name", font=("Arial", 10, "bold")).grid(row=0, column=col, padx=5, sticky="w")
        col += 1
        if show_shifts:
            ttk.Label(self.scrollable_frame, text="Preferred Shift", font=("Arial", 10, "bold")).grid(row=0, column=col, padx=5, sticky="w")
            col += 1
        if show_oncall:
            ttk.Label(self.scrollable_frame, text="Can do On-Call?", font=("Arial", 10, "bold")).grid(row=0, column=col, padx=5)

        self.pref_widgets = [] 
        
        shift_options = ["Any", "Early Only", "Central Only", "Late Only"]
        if "Weekend" in combo:
            shift_options.append("Weekend")

        for i, m in enumerate(self.members):
            row = i + 1
            c = 0
            ttk.Label(self.scrollable_frame, text=m["name"]).grid(row=row, column=c, padx=5, pady=2, sticky="w")
            c += 1
            cb, var_oc = None, None
            if show_shifts:
                cb = ttk.Combobox(self.scrollable_frame, values=shift_options, state="readonly", width=15)
                current_pref = m.get("pref", "Any")
                cb.set(current_pref)
                cb.grid(row=row, column=c, padx=5, pady=2)
                c += 1
            if show_oncall:
                var_oc = tk.BooleanVar(value=m.get("oncall", True))
                chk = ttk.Checkbutton(self.scrollable_frame, variable=var_oc)
                chk.grid(row=row, column=c, padx=5, pady=2)
            self.pref_widgets.append({"name": m["name"], "cb": cb, "var_oc": var_oc})

    def save_current_prefs(self):
        if not hasattr(self, 'pref_widgets'): return
        for w in self.pref_widgets:
            for m in self.members:
                if m["name"] == w["name"]:
                    if w["cb"]: m["pref"] = w["cb"].get()
                    if w["var_oc"]: m["oncall"] = w["var_oc"].get()
        save_members(self.members)

    def update_visibility(self):
        mode = self.var_type.get()
        combo = self.combo_shifts.get()
        self.refresh_pref_table()
        if mode == "oncall":
            self.lbl_combo.pack_forget()
            self.combo_shifts.pack_forget()
            self.staff_frame.pack_forget()
        else:
            self.lbl_combo.pack(side="left")
            self.combo_shifts.pack(side="left", padx=5)
            self.staff_frame.pack(fill="x", pady=5)

        needs_early = "Early" in combo and mode != "oncall"
        needs_late = "Late" in combo and mode != "oncall"
        needs_weekend = "Weekend" in combo and mode != "oncall"
        
        if needs_weekend:
            self.comp_frame.pack(fill="x", pady=5)
        else:
            self.comp_frame.pack_forget()

        def toggle(w, show, **kw):
            if show: w.pack(**kw)
            else: w.pack_forget()
        toggle(self.lbl_early, needs_early, side="left")
        toggle(self.spin_early_count, needs_early, side="left", padx=5)
        toggle(self.lbl_late, needs_late, side="left")
        toggle(self.spin_late_count, needs_late, side="left", padx=5)
        
        def row_vis(k, v):
            if v: self.time_rows[k].grid()
            else: self.time_rows[k].grid_remove()
        row_vis("early", "Early" in combo and mode != "oncall")
        row_vis("central", "Central" in combo and mode != "oncall")
        row_vis("late", "Late" in combo and mode != "oncall")
        row_vis("weekend", needs_weekend)
        row_vis("oncall", mode in ["both", "oncall"])

    def generate_plan(self):
        self.save_current_prefs()
        if len(self.members) < 2:
            messagebox.showerror("Error", "Need at least 2 members.")
            return
        
        try:
            start_date = datetime.strptime(self.entry_date.get(), "%d%b%Y")
        except ValueError:
            messagebox.showerror("Error", "Date Format Error. Use e.g. 01Feb2026")
            return

        months = int(self.spin_duration.get())
        plan_type = self.var_type.get()
        shift_combo = self.combo_shifts.get()
        country_code = self.combo_country.get()
        
        day_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4}
        comp_days = [day_map.get(self.combo_comp1.get(), 3), day_map.get(self.combo_comp2.get(), 4)]
        
        try:
            n_early_req = int(self.spin_early_count.get())
            n_late_req = int(self.spin_late_count.get())
        except: n_early_req, n_late_req = 1, 1

        times = {
            "early_s": self.t_early_s.get(), "early_e": self.t_early_e.get(),
            "central_s": self.t_central_s.get(), "central_e": self.t_central_e.get(),
            "late_s": self.t_late_s.get(), "late_e": self.t_late_e.get(),
            "weekend_s": self.t_weekend_s.get(), "weekend_e": self.t_weekend_e.get(),
            "oncall_s": self.t_oncall_s.get(), "oncall_e": self.t_oncall_e.get(),
        }

        existing_absences = []
        if os.path.exists(FILES["data"]):
            old_data = load_schedule()
            if old_data:
                existing_absences = old_data.get("absences", [])

        cutoff_year = start_date.year
        cutoff_month = start_date.month + months
        while cutoff_month > 12:
            cutoff_month -= 12
            cutoff_year += 1
        cutoff_date = datetime(cutoff_year, cutoff_month, 1)
        
        holidays_map = get_holidays_range(start_date, cutoff_date, country_code)

        shifts = []
        current_date = start_date
        week_idx = 0
        
        oncall_pool = [m["name"] for m in self.members if m.get("oncall", True)]
        
        while current_date < cutoff_date:
            week_num = current_date.isocalendar()[1]
            end_of_week = current_date + timedelta(days=6)
            s_data = {"week_num": week_num, "start": current_date, "end": end_of_week}
            
            # 1. On-Call
            oncall_person = None
            if plan_type in ["oncall", "both"] and oncall_pool:
                oncall_person = oncall_pool[week_idx % len(oncall_pool)]
                s_data["oncall"] = oncall_person
            
            # 2. Shift Plan
            if plan_type in ["shift-plan", "both"]:
                needs_early = "Early" in shift_combo
                needs_late = "Late" in shift_combo
                needs_central = "Central" in shift_combo
                needs_weekend = "Weekend" in shift_combo
                
                req_early = n_early_req if needs_early else 0
                req_late = n_late_req if needs_late else 0
                
                full_names = [m["name"] for m in self.members]
                
                candidates = []
                if oncall_person:
                    candidates.append(oncall_person)
                    start_i = full_names.index(oncall_person)
                    rest = full_names[start_i+1:] + full_names[:start_i]
                    candidates.extend(rest)
                else:
                    pivot = week_idx % len(full_names)
                    candidates = full_names[pivot:] + full_names[:pivot]
                
                # --- WEEKEND ---
                weekend_worker = None
                if needs_weekend and candidates:
                    weekend_worker = candidates[-1] 
                    s_data["weekend"] = weekend_worker

                def can_do(name, role):
                    m = next((x for x in self.members if x["name"] == name), None)
                    if not m: return True
                    p = m.get("pref", "Any")
                    if p == "Any": return True
                    if p == "Early Only" and role == "early": return True
                    if p == "Late Only" and role == "late": return True
                    if p == "Central Only" and role == "central": return True
                    if p == "Weekend": return True 
                    
                    return False

                assigned_early = []
                assigned_late = []
                remaining_candidates = []
                
                for p in candidates:
                    if len(assigned_early) < req_early and can_do(p, "early"):
                        assigned_early.append(p)
                    else:
                        remaining_candidates.append(p)
                
                candidates_after_early = []
                for p in remaining_candidates:
                    if len(assigned_late) < req_late and can_do(p, "late"):
                        assigned_late.append(p)
                    else:
                        candidates_after_early.append(p)
                
                assigned_central = candidates_after_early
                
                if assigned_early: s_data["early"] = assigned_early[0] if len(assigned_early)==1 else assigned_early
                if assigned_late: s_data["late"] = assigned_late[0] if len(assigned_late)==1 else assigned_late
                if assigned_central and needs_central: s_data["central"] = assigned_central

            shifts.append(s_data)
            current_date += timedelta(days=7)
            week_idx += 1
        
        save_schedule(shifts, start_date.year, plan_type, shift_combo, times, 
                      {"early": n_early_req, "late": n_late_req}, 
                      country_code, 
                      existing_absences, comp_days) 
        
        out_file = render_html(shifts, start_date.year, plan_type, shift_combo, times, holidays_map, existing_absences, comp_days)
        messagebox.showinfo("Success", f"Dashboard Generated!\nFile: {out_file}")

    # --- TAB 3: SWAP / EDIT ---
    def setup_swap_tab(self):
        self.swap_notebook = ttk.Notebook(self.tab_swap)
        self.swap_notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        frame_a = ttk.Frame(self.swap_notebook)
        self.swap_notebook.add(frame_a, text="Swap On-Call")
        f_in = ttk.Frame(frame_a)
        f_in.pack(pady=20)
        ttk.Label(f_in, text="Week A:").grid(row=0, column=0)
        self.sw_w1 = ttk.Entry(f_in, width=5)
        self.sw_w1.grid(row=0, column=1, padx=5)
        ttk.Label(f_in, text="Week B:").grid(row=0, column=2)
        self.sw_w2 = ttk.Entry(f_in, width=5)
        self.sw_w2.grid(row=0, column=3, padx=5)
        ttk.Button(frame_a, text="Swap On-Call", command=self.do_swap_oncall).pack(pady=10)
        
        frame_b = ttk.Frame(self.swap_notebook)
        self.swap_notebook.add(frame_b, text="Swap Shifts (Same Week)")
        f_load = ttk.Frame(frame_b)
        f_load.pack(pady=20)
        ttk.Label(f_load, text="Week Num:").pack(side="left")
        self.entry_week_shift = ttk.Entry(f_load, width=5)
        self.entry_week_shift.pack(side="left", padx=5)
        ttk.Button(f_load, text="Load Members", command=self.load_week_for_swap).pack(side="left")
        self.lbl_shift_info = ttk.Label(frame_b, text="Current: (Load a week first)", foreground="gray")
        self.lbl_shift_info.pack(pady=5)
        f_sel = ttk.Frame(frame_b)
        f_sel.pack(pady=10)
        ttk.Label(f_sel, text="Person A:").grid(row=0, column=0)
        self.combo_m1 = ttk.Combobox(f_sel, state="readonly")
        self.combo_m1.grid(row=0, column=1, padx=5)
        ttk.Label(f_sel, text="Person B:").grid(row=1, column=0)
        self.combo_m2 = ttk.Combobox(f_sel, state="readonly")
        self.combo_m2.grid(row=1, column=1, padx=5)
        ttk.Button(frame_b, text="Swap Shifts", command=self.do_swap_same_week).pack(pady=20)

        frame_c = ttk.Frame(self.swap_notebook)
        self.swap_notebook.add(frame_c, text="Absence / Leave")
        f_abs_load = ttk.Frame(frame_c)
        f_abs_load.pack(pady=20)
        
        ttk.Label(f_abs_load, text="From (DD-MM-YYYY):").pack(side="left")
        self.entry_abs_start = ttk.Entry(f_abs_load, width=12)
        self.entry_abs_start.pack(side="left", padx=5)
        
        ttk.Label(f_abs_load, text="To:").pack(side="left")
        self.entry_abs_end = ttk.Entry(f_abs_load, width=12)
        self.entry_abs_end.pack(side="left", padx=5)
        
        ttk.Button(f_abs_load, text="Load Range", command=self.load_week_for_absence).pack(side="left")
        
        self.lbl_abs_info = ttk.Label(frame_c, text="(Enter range & Load)", foreground="gray")
        self.lbl_abs_info.pack(pady=5)
        
        f_abs_sel = ttk.Frame(frame_c)
        f_abs_sel.pack(pady=10)
        
        ttk.Label(f_abs_sel, text="Absent Member:").grid(row=0, column=0, sticky="e")
        self.combo_absent = ttk.Combobox(f_abs_sel, state="readonly")
        self.combo_absent.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(f_abs_sel, text="Replacement shift only:").grid(row=1, column=0, sticky="e")
        self.combo_repl_shift = ttk.Combobox(f_abs_sel, state="readonly")
        self.combo_repl_shift.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(f_abs_sel, text="Replacement oncall only:").grid(row=2, column=0, sticky="e")
        self.combo_repl_oncall = ttk.Combobox(f_abs_sel, state="readonly")
        self.combo_repl_oncall.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(f_abs_sel, text="Reason:").grid(row=3, column=0, sticky="e")
        self.entry_reason = ttk.Entry(f_abs_sel)
        self.entry_reason.grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Button(frame_c, text="Process Leave & Update", command=self.do_process_absence).pack(pady=20)
        
        ttk.Separator(frame_c, orient='horizontal').pack(fill='x', pady=10)
        ttk.Button(frame_c, text="Clear All Absences / Notes", command=self.do_clear_absences).pack(pady=5)

        frame_d = ttk.Frame(self.swap_notebook)
        self.swap_notebook.add(frame_d, text="Backfill Vacancies")
        
        f_bf_load = ttk.Frame(frame_d)
        f_bf_load.pack(pady=20)
        
        ttk.Label(f_bf_load, text="From (DD-MM-YYYY):").pack(side="left")
        self.entry_bf_start = ttk.Entry(f_bf_load, width=12)
        self.entry_bf_start.pack(side="left", padx=5)
        
        ttk.Label(f_bf_load, text="To:").pack(side="left")
        self.entry_bf_end = ttk.Entry(f_bf_load, width=12)
        self.entry_bf_end.pack(side="left", padx=5)
        
        f_bf_sel = ttk.Frame(frame_d)
        f_bf_sel.pack(pady=10)
        
        ttk.Label(f_bf_sel, text="Replacement shift only:").grid(row=0, column=0, sticky="e")
        self.combo_bf_shift = ttk.Combobox(f_bf_sel, state="readonly", postcommand=self.refresh_backfill_combo)
        self.combo_bf_shift.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(f_bf_sel, text="Replacement oncall only:").grid(row=1, column=0, sticky="e")
        self.combo_bf_oncall = ttk.Combobox(f_bf_sel, state="readonly", postcommand=self.refresh_backfill_combo)
        self.combo_bf_oncall.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Button(frame_d, text="Apply Change", command=self.do_apply_backfill_changes).pack(pady=20)

    def refresh_backfill_combo(self):
        m_list = [m["name"] for m in self.members]
        self.combo_bf_shift['values'] = m_list
        self.combo_bf_oncall['values'] = m_list

    # SWAP LOGIC
    def do_swap_oncall(self):
        if not os.path.exists(FILES["data"]): return
        # FIX: Use load_schedule to ensure datetime objects and comp_days
        data = load_schedule()
        if not data: return

        try:
            w1, w2 = int(self.sw_w1.get()), int(self.sw_w2.get())
            s1 = next((s for s in data["shifts"] if s["week_num"] == w1), None)
            s2 = next((s for s in data["shifts"] if s["week_num"] == w2), None)
            if s1 and s2:
                s1['oncall'], s2['oncall'] = s2['oncall'], s1['oncall']
                holidays = get_holidays_range(data["shifts"][0]["start"], data["shifts"][-1]["end"], data.get("country", "CZ"))
                # FIX: Pass comp_days
                save_schedule(data["shifts"], data["year"], data["plan_type"], data["shift_config"], data["times"], data.get("staffing"), data.get("country", "CZ"), data.get("absences", []), data.get("comp_days"))
                render_html(data["shifts"], data["year"], data["plan_type"], data["shift_config"], data["times"], holidays, data.get("absences", []), data.get("comp_days"))
                
                messagebox.showinfo("Done", "On-Call duties swapped.")
                self.sw_w1.delete(0, tk.END)
                self.sw_w2.delete(0, tk.END)
                
            else: messagebox.showerror("Error", "Week not found.")
        except Exception as e: messagebox.showerror("Error", str(e))

    def load_week_for_swap(self):
        data = load_schedule()
        if not data: return
        try:
            w = int(self.entry_week_shift.get())
            s = next((s for s in data["shifts"] if s["week_num"] == w), None)
            if s:
                def get_names(key):
                    val = s.get(key)
                    if isinstance(val, list): return val
                    return [val] if val else []
                all_in_week = []
                all_in_week.extend(get_names('early'))
                all_in_week.extend(get_names('central'))
                all_in_week.extend(get_names('late'))
                all_in_week.extend(get_names('weekend'))
                if s.get('oncall'): all_in_week.append(s['oncall'])
                unique = sorted(list(set(all_in_week)))
                self.combo_m1['values'] = unique
                self.combo_m2['values'] = unique
                self.lbl_shift_info.config(text=f"Loaded Week {w}. Select two people.", foreground="green")
            else: self.lbl_shift_info.config(text="Week not found", foreground="red")
        except: pass

    def do_swap_same_week(self):
        data = load_schedule()
        if not data: return
        try:
            w = int(self.entry_week_shift.get())
            s = next((s for s in data["shifts"] if s["week_num"] == w), None)
            p1, p2 = self.combo_m1.get(), self.combo_m2.get()
            if not s or not p1 or not p2: return
            for key in ['early', 'central', 'late', 'oncall', 'weekend']:
                val = s.get(key)
                if val:
                    if isinstance(val, list):
                        new_list = []
                        for m in val:
                            if m == p1: new_list.append(p2)
                            elif m == p2: new_list.append(p1)
                            else: new_list.append(m)
                        s[key] = new_list
                    else:
                        if val == p1: s[key] = p2
                        elif val == p2: s[key] = p1
            holidays = get_holidays_range(data["shifts"][0]["start"], data["shifts"][-1]["end"], data.get("country", "CZ"))
            # FIX: Pass comp_days
            save_schedule(data["shifts"], data["year"], data["plan_type"], data["shift_config"], data["times"], data.get("staffing"), data.get("country", "CZ"), data.get("absences", []), data.get("comp_days"))
            render_html(data["shifts"], data["year"], data["plan_type"], data["shift_config"], data["times"], holidays, data.get("absences", []), data.get("comp_days"))
            
            messagebox.showinfo("Success", f"Swapped {p1} and {p2}")
            self.entry_week_shift.delete(0, tk.END)
            self.combo_m1.set('')
            self.combo_m1['values'] = []
            self.combo_m2.set('')
            self.combo_m2['values'] = []
            self.lbl_shift_info.config(text="Current: (Load a week first)", foreground="gray")

        except Exception as e: messagebox.showerror("Error", str(e))

    def load_week_for_absence(self):
        data = load_schedule()
        if not data: return
        try:
            start_dt = datetime.strptime(self.entry_abs_start.get(), "%d-%m-%Y")
            end_dt = datetime.strptime(self.entry_abs_end.get(), "%d-%m-%Y")
            
            found_members = set()
            count = 0
            for s in data["shifts"]:
                if not (s['end'] < start_dt or s['start'] > end_dt):
                    count += 1
                    for k in ['early', 'central', 'late', 'oncall', 'weekend']:
                        val = s.get(k)
                        if val and val != "VACANT":
                            if isinstance(val, list):
                                real_members = [x for x in val if x != "VACANT"]
                                found_members.update(real_members)
                            else:
                                found_members.add(val)
            
            if count > 0:
                self.combo_absent['values'] = sorted(list(found_members))
                all_mems = [m["name"] for m in self.members]
                self.combo_repl_shift['values'] = all_mems
                self.combo_repl_oncall['values'] = all_mems
                self.lbl_abs_info.config(text=f"Found {count} overlapping weeks.", foreground="green")
            else:
                self.lbl_abs_info.config(text="No weeks found in range.", foreground="red")
        except ValueError:
            messagebox.showerror("Error", "Invalid Date Format. Use DD-MM-YYYY")

    def do_clear_absences(self):
        data = load_schedule()
        if not data: return

        if not data.get("absences"):
            messagebox.showinfo("Info", "No absences to clear.")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to delete ALL absence notes?"):
            data["absences"] = []

            holidays = get_holidays_range(data["shifts"][0]["start"], data["shifts"][-1]["end"], data.get("country", "CZ"))
            # FIX: Pass comp_days
            save_schedule(data["shifts"], data["year"], data["plan_type"], data["shift_config"], data["times"], data.get("staffing"), data.get("country", "CZ"), [], data.get("comp_days")) 
            render_html(data["shifts"], data["year"], data["plan_type"], data["shift_config"], data["times"], holidays, [], data.get("comp_days")) 

            messagebox.showinfo("Success", "All notes/absences cleared.")

    def do_process_absence(self):
        data = load_schedule()
        if not data: return
        try:
            start_dt = datetime.strptime(self.entry_abs_start.get(), "%d-%m-%Y")
            end_dt = datetime.strptime(self.entry_abs_end.get(), "%d-%m-%Y")
        except ValueError:
             messagebox.showerror("Error", "Invalid Date. Use DD-MM-YYYY")
             return

        absent = self.combo_absent.get()
        repl_shift = self.combo_repl_shift.get()
        repl_oncall = self.combo_repl_oncall.get()
        reason = self.entry_reason.get().strip() or "Unspecified"
        
        if not absent: return
        
        updates = 0
        
        def remove_person_from_roles(shift_dict, person_name):
            removed_roles = []
            for key in ['early', 'central', 'late', 'weekend']:
                val = shift_dict.get(key)
                if not val: continue
                if isinstance(val, list):
                    if person_name in val:
                        val.remove(person_name)
                        shift_dict[key] = val
                        removed_roles.append(key)
                else:
                    if val == person_name:
                        shift_dict[key] = "" 
                        removed_roles.append(key)
            return removed_roles

        for s in data["shifts"]:
            if not (s['end'] < start_dt or s['start'] > end_dt):
                roles_vacated = remove_person_from_roles(s, absent)
                if roles_vacated: updates += 1
                
                if repl_shift and repl_shift != "VACANT":
                    old_shift_roles = remove_person_from_roles(s, repl_shift)
                    for old_r in old_shift_roles:
                        if not s.get(old_r): s[old_r] = "VACANT"
                    
                    for r in roles_vacated:
                        val = s.get(r)
                        if isinstance(val, list): val.append(repl_shift)
                        else: s[r] = repl_shift
                else:
                    for r in roles_vacated:
                        if not s.get(r): s[r] = "VACANT"

                if s.get('oncall') == absent:
                    s['oncall'] = "VACANT"
                    updates += 1
                    if repl_oncall and repl_oncall != "VACANT":
                        s['oncall'] = repl_oncall

        if updates > 0:
            new_record = {
                "name": absent,
                "start": self.entry_abs_start.get(),
                "end": self.entry_abs_end.get(),
                "reason": reason
            }
            if "absences" not in data: data["absences"] = []
            data["absences"].append(new_record)

            holidays = get_holidays_range(data["shifts"][0]["start"], data["shifts"][-1]["end"], data.get("country", "CZ"))
            # FIX: Pass comp_days
            save_schedule(data["shifts"], data["year"], data["plan_type"], data["shift_config"], data["times"], data.get("staffing"), data.get("country", "CZ"), data.get("absences", []), data.get("comp_days"))
            render_html(data["shifts"], data["year"], data["plan_type"], data["shift_config"], data["times"], holidays, data.get("absences", []), data.get("comp_days"))
            
            messagebox.showinfo("Success", f"Processed absence for {absent} in {updates} weeks.\nReason: {reason}")
            
            self.entry_abs_start.delete(0, tk.END)
            self.entry_abs_end.delete(0, tk.END)
            self.combo_absent.set('')
            self.combo_absent['values'] = []
            self.combo_repl_shift.set('')
            self.combo_repl_oncall.set('')
            self.entry_reason.delete(0, tk.END)
            self.lbl_abs_info.config(text="(Enter range & Load)", foreground="gray")
            
        else:
            messagebox.showinfo("Info", "No shifts found for this person in that range.")

    def do_apply_backfill_changes(self):
        data = load_schedule()
        if not data: return
        try:
            start_dt = datetime.strptime(self.entry_bf_start.get(), "%d-%m-%Y")
            end_dt = datetime.strptime(self.entry_bf_end.get(), "%d-%m-%Y")
        except ValueError:
            messagebox.showerror("Error", "Invalid Date. Use DD-MM-YYYY")
            return

        repl_shift = self.combo_bf_shift.get()
        repl_oncall = self.combo_bf_oncall.get()
        
        if not repl_shift and not repl_oncall: 
            messagebox.showerror("Error", "Select at least one replacement.")
            return
        
        updates = 0
        for s in data["shifts"]:
            if not (s['end'] < start_dt or s['start'] > end_dt):
                if repl_shift:
                    for key in ['early', 'central', 'late', 'weekend']:
                        val = s.get(key)
                        if val == "VACANT":
                            s[key] = repl_shift
                            updates += 1
                        elif val == "" or val is None:
                            s[key] = repl_shift
                            updates += 1
                        elif isinstance(val, list) and "VACANT" in val:
                            val.remove("VACANT")
                            val.append(repl_shift)
                            s[key] = val
                            updates += 1
                
                if repl_oncall:
                    if s.get('oncall') != repl_oncall:
                        s['oncall'] = repl_oncall
                        updates += 1
        
        if updates > 0:
            holidays = get_holidays_range(data["shifts"][0]["start"], data["shifts"][-1]["end"], data.get("country", "CZ"))
            # FIX: Pass comp_days
            save_schedule(data["shifts"], data["year"], data["plan_type"], data["shift_config"], data["times"], data.get("staffing"), data.get("country", "CZ"), data.get("absences", []), data.get("comp_days"))
            render_html(data["shifts"], data["year"], data["plan_type"], data["shift_config"], data["times"], holidays, data.get("absences", []), data.get("comp_days"))
            
            messagebox.showinfo("Success", f"Applied changes to {updates} slots/weeks.")
            self.entry_bf_start.delete(0, tk.END)
            self.entry_bf_end.delete(0, tk.END)
            self.combo_bf_shift.set('')
            self.combo_bf_oncall.set('')
        else:
            messagebox.showinfo("Info", "No matching weeks/slots found in this range.")

if __name__ == "__main__":
    app = ShiftPlannerApp()
    app.mainloop()