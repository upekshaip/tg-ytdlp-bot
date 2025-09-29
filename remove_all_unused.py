#!/usr/bin/env python3
import re

def remove_all_unused():
    """Remove all unused variables from logger_msg.py"""
    
    with open('CONFIG/logger_msg.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Get list of unused variables from test_count_var.py
    import subprocess
    result = subprocess.run(['python', 'test_count_var.py'], capture_output=True, text=True)
    lines = result.stdout.split('\n')
    
    unused_vars = []
    for line in lines:
        if ' 0$' in line or line.endswith(' 0'):
            var_name = line.split()[0]
            if var_name and not var_name.startswith('Переменная'):
                unused_vars.append(var_name)
    
    print(f"Found {len(unused_vars)} unused variables")
    
    # Remove unused variables
    for var in unused_vars:
        # Pattern to match the variable definition
        pattern = rf'^\s*{re.escape(var)}\s*=.*$'
        content = re.sub(pattern, '', content, flags=re.MULTILINE)
    
    # Clean up empty lines
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    
    with open('CONFIG/logger_msg.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Removed {len(unused_vars)} unused variables")

if __name__ == "__main__":
    remove_all_unused()
