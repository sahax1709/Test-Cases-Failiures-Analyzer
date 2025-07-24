import pandas as pd
import matplotlib.pyplot as plt
from tkinter import BOTH, Toplevel, Button, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def show_chart(root, failure_data):
    if failure_data.empty:
        messagebox.showwarning("Warning", "No data to visualize")
        return

    try:
        # Convert string dates to datetime objects and sort
        chart_data = failure_data.copy()
        chart_data['DateObj'] = pd.to_datetime(chart_data['Date'], errors='coerce', format='%d %B %Y')
        chart_data = chart_data.dropna(subset=['DateObj']).sort_values('DateObj')

        if chart_data.empty:
            messagebox.showwarning("Warning", "No valid dates to visualize")
            return

        # Group by date and count failures
        daily_failures = chart_data.groupby('DateObj').size()

        # Create window
        chart_window = Toplevel(root)
        chart_window.title("Failure Trend Analysis")
        chart_window.geometry("1000x700")

        # Create figure with larger size
        fig, ax = plt.subplots(figsize=(12, 6))

        # Use line plot instead of bar for better visibility
        daily_failures.plot(kind='line', ax=ax, color='red', marker='o', linestyle='-')

        # Formatting
        ax.set_title('Test Failure Trend', pad=20)
        ax.set_xlabel('Date', labelpad=10)
        ax.set_ylabel('Number of Failures', labelpad=10)
        ax.grid(True, linestyle='--', alpha=0.7)

        # Format x-axis dates
        ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%d %b %Y'))
        fig.autofmt_xdate(rotation=45)
        plt.tight_layout()

        # Add canvas to window
        canvas = FigureCanvasTkAgg(fig, master=chart_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=BOTH, expand=True)

        # Add toolbar for navigation (optional)
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        toolbar = NavigationToolbar2Tk(canvas, chart_window)
        toolbar.update()
        canvas.get_tk_widget().pack(fill=BOTH, expand=True)

        # Close button
        Button(chart_window, text="Close", command=chart_window.destroy).pack(pady=10)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to generate chart: {str(e)}")
