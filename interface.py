import pandas as pd
import os
from tkinter import *
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from parser import parse_test_results, extract_date_from_filename
from analyzer import group_failures
from chart_representation import show_chart
from analyzer import group_failures 


class TestFailureAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("Test Failure Analyzer")
        self.root.geometry("1000x700")

        self.failure_data = pd.DataFrame(columns=['Scenario', 'Date', 'Filename'])
        self.create_widgets()

    def create_widgets(self):
        # Control Frame
        control_frame = Frame(self.root, padx=10, pady=10)
        control_frame.pack(fill=X)

        # Directory Selection
        Label(control_frame, text="Test Results Directory:").grid(row=0, column=0, sticky=W)
        self.dir_entry = Entry(control_frame, width=50)
        self.dir_entry.grid(row=0, column=1, padx=5)
        Button(control_frame, text="Browse", command=self.browse_directory).grid(row=0, column=2)

        # Parse options
        self.reverse_parse = BooleanVar(value=True)
        Checkbutton(control_frame, text="Parse from end (for large files)", variable=self.reverse_parse).grid(row=1, column=0, sticky=W)

        # Action Buttons
        Button(control_frame, text="Analyze Files", command=self.analyze_files).grid(row=2, column=0, pady=10)
        Button(control_frame, text="Export to CSV", command=self.export_to_csv).grid(row=2, column=1, pady=10)
        Button(control_frame, text="Show Chart", command=self.show_chart).grid(row=2, column=2, pady=10)
        Button(control_frame, text="Show Failure Dates", command=self.show_failure_dates).grid(row=2, column=3, pady=10)
        Button(control_frame, text="View Text Files Data", command=self.show_raw_data).grid(row=2, column=4, pady=10)
        # Results Frame
        results_frame = Frame(self.root)
        results_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Treeview for results
        self.tree = ttk.Treeview(results_frame, columns=('Scenario', 'Failures', 'First Failed', 'Last Failed'), show='headings')
        self.tree.heading('Scenario', text='Scenario')
        self.tree.heading('Failures', text='Failure Count')
        self.tree.heading('First Failed', text='First Failure Date')
        self.tree.heading('Last Failed', text='Last Failure Date')
        self.tree.column('Scenario', width=400)
        self.tree.column('Failures', width=100, anchor=CENTER)
        self.tree.column('First Failed', width=150, anchor=CENTER)
        self.tree.column('Last Failed', width=150, anchor=CENTER)

        scrollbar = ttk.Scrollbar(results_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky=NSEW)
        scrollbar.grid(row=0, column=1, sticky=NS)

        # Configure grid weights
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        # Status Bar
        self.status = StringVar()
        self.status.set("Ready")
        Label(self.root, textvariable=self.status, bd=1, relief=SUNKEN, anchor=W).pack(fill=X)

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.dir_entry.delete(0, END)
            self.dir_entry.insert(0, directory)

    def analyze_files(self):
        directory = self.dir_entry.get()
        if not directory or not os.path.exists(directory):
            messagebox.showerror("Error", "Please select a valid directory")
            return

        self.status.set("Analyzing files...")
        self.root.update()

        try:
            self.failure_data = parse_test_results(directory, self.reverse_parse.get())
            self.display_results()
            self.status.set(f"Analysis complete. Found {len(self.failure_data)} failures across {len(self.failure_data['Filename'].unique())} files")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to analyze files: {str(e)}")
            self.status.set("Error occurred during analysis")

    def display_results(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if self.failure_data.empty:
            return

        grouped = group_failures(self.failure_data)
        for scenario, row in grouped.iterrows():
            self.tree.insert('', 'end', values=(
                scenario,
                row['Failures'],
                row['First Failed'],
                row['Last Failed']
            ))


    def export_to_csv(self):
        if self.failure_data.empty:
            messagebox.showwarning("Warning", "No data to export")
            return
        
        try:
            # Get the grouped data while preserving full scenario names
            grouped_data = group_failures(self.failure_data)
            
            # Reset index to include Scenario as a column (if it's the index)
            if grouped_data.index.name == 'Scenario':
                grouped_data = grouped_data.reset_index()
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if file_path:
                # Ensure we're exporting the full scenario names
                grouped_data.to_csv(file_path, index=False)
                
                # Verify the output
                print("\nCSV Export Preview:")
                print(grouped_data.head().to_string(index=False))
                
                messagebox.showinfo("Success", f"Data exported to {file_path}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {str(e)}")

    def group_failures(self, failure_data):
        """Group the failure data while preserving full scenario names"""
        if failure_data.empty:
            return pd.DataFrame()
        
        # Group and aggregate while keeping scenario as a column
        grouped = (
            failure_data
            .groupby('Scenario', as_index=False)
            .agg(
                Failures=('Date', 'count'),
                First_Failed=('Date', 'min'),
                Last_Failed=('Date', 'max')
            )
            .sort_values('Failures', ascending=False)
        )
        
        # Rename columns to match display
        grouped = grouped.rename(columns={
            'First_Failed': 'First Failed',
            'Last_Failed': 'Last Failed'
        })
        
        return grouped

    def show_chart(self):
        show_chart(self.root, self.failure_data)

    def show_failure_dates(self):
        if self.failure_data.empty:
            messagebox.showwarning("Warning", "No failure data available")
            return

        # Create new window
        dates_window = Toplevel(self.root)
        dates_window.title("Detailed Failure Dates")
        dates_window.geometry("800x600")

        # Create frame for treeview and scrollbars
        tree_frame = Frame(dates_window)
        tree_frame.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)

        # Create treeview
        tree = ttk.Treeview(tree_frame, columns=('Scenario', 'Failure Dates'), show='headings')
        tree.heading('Scenario', text='Scenario')
        tree.heading('Failure Dates', text='Dates Failed')
        tree.column('Scenario', width=400)
        tree.column('Failure Dates', width=350)

        # Vertical scrollbar
        y_scroll = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=y_scroll.set)

        # Horizontal scrollbar
        x_scroll = ttk.Scrollbar(dates_window, orient=HORIZONTAL, command=tree.xview)
        tree.configure(xscrollcommand=x_scroll.set)

        # Grid layout
        tree.grid(row=0, column=0, sticky=NSEW)
        y_scroll.grid(row=0, column=1, sticky=NS)
        x_scroll.grid(row=1, column=0, sticky=EW)

        # Configure grid weights
        dates_window.grid_rowconfigure(0, weight=1)
        dates_window.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Group data by scenario and process dates
        grouped = self.failure_data.groupby('Scenario')['Date'].agg(list)

        # Add data to treeview
        for scenario, dates in grouped.items():
            unique_dates = sorted(set(dates))  # Remove duplicates and sort

            # Extract years from all dates
            years = set()
            date_objects = []
            for date_str in unique_dates:
                try:
                    date_obj = datetime.strptime(date_str, "%d %B %Y")
                    years.add(date_obj.year)
                    date_objects.append(date_obj)
                except ValueError:
                    # Handle unknown_date or other formats
                    pass

            if len(years) == 1 and len(date_objects) > 1:
                # All dates same year - format without repeating year
                year = years.pop()
                formatted_dates = []
                for date_obj in sorted(date_objects):
                    # Format as "Day Month" (without year)
                    formatted_dates.append(date_obj.strftime("%d %B"))
                # Add year once at the end
                date_display = ", ".join(formatted_dates) + f" {year}"
            else:
                # Mixed years or single date - show full dates
                date_display = ", ".join(unique_dates)

            tree.insert('', 'end', values=(scenario, date_display))

        # Add close button (placed below the horizontal scrollbar)
        Button(dates_window, text="Close", command=dates_window.destroy).grid(row=2, column=0, pady=10)

    def show_raw_data(self):
        if self.failure_data.empty:
            messagebox.showwarning("Warning", "No data available")
            return
        
        # Create new window
        raw_window = Toplevel(self.root)
        raw_window.title("Test Failure Data Viewer")
        raw_window.geometry("900x600")  # Adjusted width since we removed filename column
        
        # Create control frame for dropdown
        control_frame = Frame(raw_window)
        control_frame.pack(fill=X, padx=10, pady=5)
        
        # Get unique dates and sort them chronologically
        unique_dates = sorted(
            set(self.failure_data['Date']), 
            key=lambda x: datetime.strptime(x, "%d %B %Y") if x != "unknown_date" else datetime.min
        )
        unique_dates.insert(0, "All Dates")
        
        # Date selection dropdown
        Label(control_frame, text="Filter by Date:").pack(side=LEFT, padx=5)
        self.date_var = StringVar(value="All Dates")
        date_dropdown = OptionMenu(control_frame, self.date_var, *unique_dates)
        date_dropdown.pack(side=LEFT, padx=5)
        date_dropdown.config(width=15)
        
        # Create text display area
        text_frame = Frame(raw_window)
        text_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        # Add scrollbars
        y_scroll = Scrollbar(text_frame)
        x_scroll = Scrollbar(text_frame, orient=HORIZONTAL)
        
        # Create text widget with monospace font
        self.raw_data_text = Text(
            text_frame,
            wrap=NONE,
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set,
            font=('Courier', 10),
            padx=5,
            pady=5
        )
        
        # Configure scrollbars
        y_scroll.config(command=self.raw_data_text.yview)
        x_scroll.config(command=self.raw_data_text.xview)
        
        # Layout
        self.raw_data_text.grid(row=0, column=0, sticky=NSEW)
        y_scroll.grid(row=0, column=1, sticky=NS)
        x_scroll.grid(row=1, column=0, sticky=EW)
        
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)
        
        # Auto-update when dropdown changes
        self.date_var.trace_add('write', lambda *_: self.update_raw_data_view(raw_window))
        
        # Initial data load
        self.update_raw_data_view(raw_window)
        
        # Close button
        Button(raw_window, text="Close", command=raw_window.destroy).pack(pady=10)

    def update_raw_data_view(self, window):
        # Clear existing content
        self.raw_data_text.config(state=NORMAL)
        self.raw_data_text.delete(1.0, END)
        
        # Get selected date filter
        selected_date = self.date_var.get()
        
        # Filter data
        if selected_date == "All Dates":
            display_data = self.failure_data
        else:
            display_data = self.failure_data[self.failure_data['Date'] == selected_date]
        
        # Sort data by date
        try:
            sorted_data = display_data.copy()
            sorted_data['SortDate'] = pd.to_datetime(
                sorted_data['Date'], 
                errors='coerce', 
                format='%d %B %Y'
            )
            sorted_data = sorted_data.sort_values('SortDate')
        except:
            sorted_data = display_data.sort_values('Date')
        
        # Add total count at the top
        self.raw_data_text.insert(END, f"Total failure count: {len(sorted_data)}\n\n")
        
        # Add header with S.No
        self.raw_data_text.insert(END, f"{'S.No':<5} | {'Date':<20} | {'Scenario':<70}\n")
        self.raw_data_text.insert(END, "-"*100 + "\n")
        
        # Add data rows with serial numbers
        for idx, (_, row) in enumerate(sorted_data.iterrows(), start=1):
            self.raw_data_text.insert(END, f"{idx:<5} | {row['Date']:<20} | {row['Scenario']:<70}\n")
        
        # Update window title
        window.title(f"Test Failures - {selected_date} ({len(sorted_data)} failures)")
        
        # Make text read-only and scroll to top
        self.raw_data_text.config(state=DISABLED)
        self.raw_data_text.see(1.0)

if __name__ == "__main__":
    root = Tk()
    app = TestFailureAnalyzer(root)
    root.mainloop()
