import threading
import sqlite3
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from tkcalendar import DateEntry
from tkinter import messagebox

class MicroscopeUsageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Microscope Usage Tracker")
        
        # Database setup
        self.conn = sqlite3.connect('microscope_usage.db')
        self.cursor = self.conn.cursor()
        self.create_table()
        
        # Variables
        self.pi_name = tk.StringVar()
        self.user_name = tk.StringVar()
        self.department = tk.StringVar()
        self.usage_date = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.microscope_type = tk.StringVar()
        self.start_time = None
        self.end_time = None
        self.usage_duration = tk.StringVar(value="0:00:00")
        self.sample_preparation_type = tk.StringVar()
        self.sample_count = tk.IntVar(value=0)
        
        # Rates
        self.microscope_rates = {
            "SEM": 35,
            "TEM": 35,
            "LM": 30,
            "Confocal": 30,
            "Other": 30
        }
        
        self.sample_rates = {
            "SEM": 30,
            "TEM": 30,
            "LM": 30,
            "Other": 25
        }
        
        # Create the UI
        self.create_widgets()

    def create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS usage (
            id INTEGER PRIMARY KEY,
            date TEXT,
            pi TEXT,
            user TEXT,
            department TEXT,
            service_description TEXT,
            start_time TEXT,
            end_time TEXT,
            usage_duration TEXT,
            sample_count INTEGER,
            microscope_cost REAL,
            sample_cost REAL
        )''')
        self.conn.commit()

    def create_widgets(self):
        # User Information Frame
        self.user_info_frame = ttk.LabelFrame(self.root, text="User Information")
        self.user_info_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.create_user_info_widgets()
        
        # Mode Selection Frame
        selection_frame = ttk.LabelFrame(self.root, text="Select Mode")
        selection_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
    
        self.mode_var = tk.StringVar()
        self.mode_var.set("Select Mode")
        
        ttk.Radiobutton(selection_frame, text="Sample Preparation", variable=self.mode_var, value="Sample Preparation", command=self.update_mode).grid(row=0, column=0, padx=5, pady=5)
        ttk.Radiobutton(selection_frame, text="Microscope Usage", variable=self.mode_var, value="Microscope Usage", command=self.update_mode).grid(row=0, column=1, padx=5, pady=5)
        
        # Sample Preparation Frame
        self.sample_preparation_frame = ttk.LabelFrame(self.root, text="Sample Preparation")
        self.create_sample_preparation_widgets()
        
        # Microscope Usage Frame
        self.microscope_usage_frame = ttk.LabelFrame(self.root, text="Microscope Usage")
        self.create_microscope_usage_widgets()
        
        # Add Save and Enter buttons
        self.save_button = ttk.Button(self.root, text="Save", command=self.save_data)
        self.save_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        # Show the initial mode selection
        self.update_mode()

    def create_user_info_widgets(self):
        ttk.Label(self.user_info_frame, text="PI:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(self.user_info_frame, textvariable=self.pi_name).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(self.user_info_frame, text="User:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(self.user_info_frame, textvariable=self.user_name).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(self.user_info_frame, text="Department:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(self.user_info_frame, textvariable=self.department).grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(self.user_info_frame, text="Date:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        DateEntry(self.user_info_frame, textvariable=self.usage_date, date_pattern="yyyy-mm-dd").grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        
    def create_sample_preparation_widgets(self):
        ttk.Label(self.sample_preparation_frame, text="Preparation Type:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Combobox(self.sample_preparation_frame, textvariable=self.sample_preparation_type, values=list(self.sample_rates.keys())).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(self.sample_preparation_frame, text="Number of Samples:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Spinbox(self.sample_preparation_frame, from_=0, to=100, textvariable=self.sample_count).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
    
    def create_microscope_usage_widgets(self):
        ttk.Label(self.microscope_usage_frame, text="Microscope:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Combobox(self.microscope_usage_frame, textvariable=self.microscope_type, values=list(self.microscope_rates.keys())).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.start_button = ttk.Button(self.microscope_usage_frame, text="Start", command=self.start_usage)
        self.start_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        self.stop_button = ttk.Button(self.microscope_usage_frame, text="Stop", command=self.stop_usage, state="disabled")
        self.stop_button.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(self.microscope_usage_frame, text="Duration:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(self.microscope_usage_frame, textvariable=self.usage_duration).grid(row=2, column=1, padx=5, pady=5, sticky="ew")

    def update_mode(self):
        mode = self.mode_var.get()
        
        # Always show the User Information frame
        self.user_info_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        # Show/hide mode-specific frames based on the selected mode
        if mode == "Sample Preparation":
            self.sample_preparation_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
            self.microscope_usage_frame.grid_forget()
        elif mode == "Microscope Usage":
            self.microscope_usage_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
            self.sample_preparation_frame.grid_forget()
        else:
            self.sample_preparation_frame.grid_forget()
            self.microscope_usage_frame.grid_forget()

    def start_usage(self):
        if self.start_time is None:
            self.start_time = datetime.now()
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
        else:
            messagebox.showwarning("Warning", "Microscope usage already started.")

    def stop_usage(self):
        if self.start_time is not None:
            self.end_time = datetime.now()
            duration = self.end_time - self.start_time
            self.usage_duration.set(str(duration))
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
        else:
            messagebox.showwarning("Warning", "Microscope usage has not started yet.")

    def save_data(self):
        threading.Thread(target=self.save_to_db).start()
    
    def save_to_db(self):
        try:
            if self.mode_var.get() == "Sample Preparation":
                service_description = f"{self.sample_preparation_type.get()} Sample Preparation"
                microscope_cost = 0
                sample_cost = self.sample_rates[self.sample_preparation_type.get()] * self.sample_count.get()
                usage_duration = "N/A"
                start_time = "N/A"
                end_time = "N/A"
            elif self.mode_var.get() == "Microscope Usage":
                service_description = f"{self.microscope_type.get()} Microscope Usage"
                microscope_cost = self.microscope_rates[self.microscope_type.get()] * (self.end_time - self.start_time).total_seconds() / 3600
                sample_cost = 0
                usage_duration = self.usage_duration.get()
                start_time = self.start_time.strftime("%H:%M:%S")
                end_time = self.end_time.strftime("%H:%M:%S")
            else:
                return

            self.cursor.execute('''INSERT INTO usage (date, pi, user, department, service_description, start_time, end_time, usage_duration, sample_count, microscope_cost, sample_cost)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                (self.usage_date.get(), self.pi_name.get(), self.user_name.get(), self.department.get(),
                                 service_description, start_time, end_time, usage_duration, self.sample_count.get(),
                                 microscope_cost, sample_cost))
            self.conn.commit()
            
            # Update UI from main thread
            
            self.root.after(0, self.enter_new_data)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred while saving data: {e}"))


    def enter_new_data(self):
        self.pi_name.set("")
        self.user_name.set("")
        self.department.set("")
        self.usage_date.set(datetime.now().strftime("%Y-%m-%d"))
        self.microscope_type.set("")
        self.start_time = None
        self.end_time = None
        self.usage_duration.set("0:00:00")
        self.sample_preparation_type.set("")
        self.sample_count.set(0)
        self.update_mode()
        self.root.update_idletasks()

if __name__ == "__main__":
    root = tk.Tk()
    app = MicroscopeUsageApp(root)
    root.geometry("600x500")
    root.mainloop()
