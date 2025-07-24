# Test Failure Analyzer


A GUI application for analyzing and visualizing test failure reports from Selenium test results.
The application searches multiple large text files to extract the final results of the test automation.
The programme looks for the strink "Failing Scenarios" to identify the list of failes test cases.

## Features

- 📊 Interactive failure trend analysis
- 📅 Date-based filtering of test failures
- 🔍 Multiple view modes (tree, raw data, charts)
- 📈 Visualizations with Matplotlib
- 📤 CSV export functionality
- 🗓️ Smart date formatting and sorting
- 📂 Handles large test result files efficiently

Install dependencies:

pip install -r requirements.txt

## Requirements

- Python 3.7+
- Required packages:

  pandas
  matplotlib
  tkcalendar (optional for date picker)
  chardet


## Usage

1. Run the application:

python interface.py

2. Use the interface:
- Click "Browse" to select test results directory
- Analyze failures using different view options
- Export data to CSV when needed

