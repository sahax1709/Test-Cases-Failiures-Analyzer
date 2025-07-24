import os
import re
import chardet
import pandas as pd
from datetime import datetime

def extract_date_from_filename(filename):
    """Extract date from filename in format MMDDYYYY or DDMMYYYY and return as 'DD Month YYYY'"""
    date_match = re.search(r'(\d{2})(\d{2})(\d{4})', filename)
    if not date_match:
        return "unknown_date"
    try:
        # Try MM DD YYYY format first
        month, day, year = date_match.groups()
        date_obj = datetime.strptime(f"{month}{day}{year}", "%m%d%Y")
    except ValueError:
        try:
            # Then try DD MM YYYY format
            day, month, year = date_match.groups()
            date_obj = datetime.strptime(f"{day}{month}{year}", "%d%m%Y")
        except ValueError:
            return "unknown_date"
    return date_obj.strftime("%d %B %Y")

def detect_file_encoding(file_path):
    """Detect file encoding using chardet"""
    with open(file_path, 'rb') as f:
        rawdata = f.read(10000)
    return chardet.detect(rawdata)['encoding']

def read_last_lines(file_path, num_lines=15, encoding='utf-8'):
    """Read last N lines from a text file efficiently with encoding support"""
    with open(file_path, 'rb') as f:
        f.seek(0, os.SEEK_END)
        file_size = f.tell()

        block_size = 1024
        lines = []
        remaining_bytes = file_size

        while remaining_bytes > 0 and len(lines) < num_lines:
            seek_pos = max(0, remaining_bytes - block_size)
            f.seek(seek_pos)
            chunk = f.read(min(block_size, remaining_bytes))
            remaining_bytes -= block_size

            try:
                chunk_text = chunk.decode(encoding)
            except UnicodeDecodeError:
                chunk_text = chunk.decode(encoding, errors='replace')

            chunk_lines = chunk_text.replace('\r\n', '\n').split('\n')

            if lines and chunk_lines:
                lines[-1] = chunk_lines[-1] + lines[-1]
                chunk_lines = chunk_lines[:-1]

            lines = chunk_lines + lines

    return [line for line in lines[-num_lines:] if line.strip()]

def parse_test_results(directory, reverse_parse=True):
    failure_data = []
    failure_pattern = re.compile(r'^\s*([\w_]+\.feature:\d+.*?)\s*$', re.MULTILINE)

    for filename in os.listdir(directory):
        if not filename.endswith('.txt'):
            continue

        file_date = extract_date_from_filename(filename)
        filepath = os.path.join(directory, filename)

        try:
            encoding = detect_file_encoding(filepath)
            if not encoding:
                encoding = 'utf-8'

            if reverse_parse:
                last_lines = read_last_lines(filepath, 15, encoding)

                summary_start = None
                for i, line in enumerate(last_lines):
                    if line and line[0].isdigit() and ("features passed" in line or "scenarios passed" in line):
                        summary_start = i
                        break

                if summary_start is None:
                    continue

                with open(filepath, 'r', encoding=encoding, errors='replace') as f:
                    capture = False
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue

                        if line.startswith("Failing scenarios:"):
                            capture = True
                            continue

                        if capture:
                            if any(line == summary_line.strip() for summary_line in last_lines[summary_start:] if summary_start is not None and summary_line.strip()):
                                break

                            match = failure_pattern.match(line)
                            if match:
                                scenario = match.group(1).strip()
                                failure_data.append({
                                    'Scenario': scenario,
                                    'Date': file_date,
                                    'Filename': filename
                                })
            else:
                with open(filepath, 'r', encoding=encoding, errors='replace') as f:
                    content = f.read()
                    summary_match = re.search(r'Failing scenarios:|Failed scenarios:', content, re.IGNORECASE)
                    if not summary_match:
                        continue

                    summary_section = content[summary_match.start():]
                    failed_scenarios = failure_pattern.findall(summary_section)

                    for scenario in failed_scenarios:
                        scenario = scenario.strip()
                        if scenario:
                            failure_data.append({
                                'Scenario': scenario,
                                'Date': file_date,
                                'Filename': filename
                            })
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            continue

    return pd.DataFrame(failure_data)
