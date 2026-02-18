import re

fp = r'd:\Btrac\garage-management\templates\accounts\signup.html'
with open(fp, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and fix the problematic lines
for i, line in enumerate(lines):
    if '{%' in line and 'form_data' in line:
        print(f'Before line {i+1}: {line.strip()[:120]}')

# Replace the Customer radio line
for i, line in enumerate(lines):
    if "CUSTOMER" in line and "hidden peer" in line and "{%" in line:
        lines[i] = '                            <input type="radio" name="role" value="CUSTOMER" class="hidden peer" {{ customer_checked }}>\r\n'
        print(f'Fixed line {i+1}')
    elif "MECHANIC" in line and "hidden peer" in line and "{%" in line:
        lines[i] = '                            <input type="radio" name="role" value="MECHANIC" class="hidden peer" {{ mechanic_checked }}>\r\n'
        print(f'Fixed line {i+1}')

with open(fp, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('File written')

# Test
import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()
from django.template.loader import get_template
try:
    t = get_template('accounts/signup.html')
    # Simulate default context
    r = t.render({'customer_checked': 'checked', 'mechanic_checked': ''})
    print(f'Template renders OK, length: {len(r)}')
except Exception as e:
    print(f'Error: {e}')
