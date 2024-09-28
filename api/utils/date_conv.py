import re

def remove_after_time(date_string):
    # Regular expression pattern to capture date and time
    pattern = r"^(.*\d{2}:\d{2}:\d{2})\s*(.*)$"

    match = re.match(pattern, date_string)
    if match:
        return match.group(1)
    return date_string
