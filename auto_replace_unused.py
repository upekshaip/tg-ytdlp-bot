#!/usr/bin/env python3
import os
import re
import subprocess

def get_unused_variables():
    """Get list of unused variables from test_count_var.py"""
    result = subprocess.run(['python', 'test_count_var.py'], capture_output=True, text=True)
    lines = result.stdout.split('\n')
    
    unused_vars = []
    for line in lines:
        if ' 0$' in line or line.endswith(' 0'):
            var_name = line.split()[0]
            if var_name and not var_name.startswith('Переменная'):
                unused_vars.append(var_name)
    
    return unused_vars

def get_variable_text(var_name, config_file):
    """Get the text content of a variable from config file"""
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the variable definition
    pattern = rf'^\s*{re.escape(var_name)}\s*=\s*["\'](.*?)["\']'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    
    if match:
        return match.group(1)
    return None

def find_and_replace_in_files(var_name, original_text, replacement):
    """Find and replace text in all Python files"""
    if not original_text:
        return 0
    
    # Escape special regex characters in the original text
    escaped_text = re.escape(original_text)
    
    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Skip backup directories
        if any(d.startswith('_') for d in dirs):
            dirs[:] = [d for d in dirs if not d.startswith('_')]
        
        for file in files:
            if file.endswith('.py') and not file.startswith('_'):
                python_files.append(os.path.join(root, file))
    
    replacements_made = 0
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count occurrences
            occurrences = content.count(original_text)
            if occurrences > 0:
                print(f"Found {occurrences} occurrences in {file_path}")
                
                # Replace the text
                new_content = content.replace(original_text, replacement)
                
                # Write back if changed
                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    replacements_made += occurrences
                    print(f"  -> Replaced {occurrences} occurrences with {replacement}")
        
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    return replacements_made

def main():
    print("Getting unused variables...")
    unused_vars = get_unused_variables()
    
    if not unused_vars:
        print("No unused variables found!")
        return
    
    print(f"Found {len(unused_vars)} unused variables")
    
    total_replacements = 0
    
    for var_name in unused_vars:
        print(f"\nProcessing {var_name}...")
        
        # Try to get text from logger_msg.py first
        original_text = get_variable_text(var_name, 'CONFIG/logger_msg.py')
        if not original_text:
            # Try messages.py
            original_text = get_variable_text(var_name, 'CONFIG/messages.py')
        
        if original_text:
            print(f"  Original text: {repr(original_text)}")
            
            # Create replacement string
            if var_name.startswith('LOGGER_'):
                replacement = f"LoggerMsg.{var_name}"
            else:
                replacement = f"Messages.{var_name}"
            
            print(f"  Replacement: {replacement}")
            
            # Find and replace
            replacements = find_and_replace_in_files(var_name, original_text, replacement)
            total_replacements += replacements
            
            if replacements > 0:
                print(f"  -> Made {replacements} replacements")
            else:
                print(f"  -> No replacements made")
        else:
            print(f"  -> Could not find text for {var_name}")
    
    print(f"\nTotal replacements made: {total_replacements}")

if __name__ == "__main__":
    main()
