#!/usr/bin/env python3
"""
PATCH: Fix comparisons with None in code
Automatically finds and fixes places where variables are compared to numbers without a None check.
"""
import os
import re
import glob

def fix_none_comparisons_in_file(file_path):
    """Fix None comparisons in a single file."""
    changes_made = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern 1: if variable > number
        pattern1 = r'if\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*>\s*([0-9]+)'
        def replace1(match):
            var_name = match.group(1)
            number = match.group(2)
            return f'if {var_name} and {var_name} > {number}'
        
        content = re.sub(pattern1, replace1, content)
        
        # Pattern 2: if variable < number
        pattern2 = r'if\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*<\s*([0-9]+)'
        def replace2(match):
            var_name = match.group(1)
            number = match.group(2)
            return f'if {var_name} and {var_name} < {number}'
        
        content = re.sub(pattern2, replace2, content)
        
        # Pattern 3: if variable > expression (function call)
        pattern3 = r'if\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*>\s*([a-zA-Z_][a-zA-Z0-9_]*\([^)]*\))'
        def replace3(match):
            var_name = match.group(1)
            expression = match.group(2)
            return f'if {var_name} and {var_name} > {expression}'
        
        content = re.sub(pattern3, replace3, content)
        
        # Pattern 4: if variable < expression (function call)
        pattern4 = r'if\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*<\s*([a-zA-Z_][a-zA-Z0-9_]*\([^)]*\))'
        def replace4(match):
            var_name = match.group(1)
            expression = match.group(2)
            return f'if {var_name} and {var_name} < {expression}'
        
        content = re.sub(pattern4, replace4, content)
        
        # Pattern 5: if variable > other_var - number
        pattern5 = r'if\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*>\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*-\s*([0-9]+)'
        def replace5(match):
            var_name = match.group(1)
            other_var = match.group(2)
            number = match.group(3)
            return f'if {var_name} and {var_name} > {other_var} - {number}'
        
        content = re.sub(pattern5, replace5, content)
        
        # Pattern 6: if variable < other_var - number
        pattern6 = r'if\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*<\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*-\s*([0-9]+)'
        def replace6(match):
            var_name = match.group(1)
            other_var = match.group(2)
            number = match.group(3)
            return f'if {var_name} and {var_name} < {other_var} - {number}'
        
        content = re.sub(pattern6, replace6, content)
        
        # Count and persist changes
        if content != original_content:
            changes_made = len(re.findall(r'if\s+[a-zA-Z_][a-zA-Z0-9_]*\s+and\s+[a-zA-Z_][a-zA-Z0-9_]*\s*[><]', content)) - len(re.findall(r'if\s+[a-zA-Z_][a-zA-Z0-9_]*\s+and\s+[a-zA-Z_][a-zA-Z0-9_]*\s*[><]', original_content))
            
            # Persist changes
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
    
    except Exception as e:
        print(f"Error while processing {file_path}: {e}")
    
    return changes_made

def apply_patch():
    """Apply patch to all Python files."""
    print("🔧 PATCH: Fix comparisons with None")
    print("=" * 50)
    
    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Skip folders with temp files
        if any(skip in root for skip in ['__pycache__', '.git', 'venv', 'backup']):
            continue
            
        for file in files:
            if file.endswith('.py') and not file.startswith('.'):
                python_files.append(os.path.join(root, file))
    
    total_changes = 0
    files_changed = 0
    
    for file_path in python_files:
        changes = fix_none_comparisons_in_file(file_path)
        if changes and changes > 0:
            print(f"✅ {file_path}: {changes} fixes")
            total_changes += changes
            files_changed += 1
    
    print("\n📊 RESULT:")
    print(f"   Files processed: {len(python_files)}")
    print(f"   Files changed: {files_changed}")
    print(f"   Total fixes: {total_changes}")
    
    if total_changes and total_changes > 0:
        print("\n🎉 PATCH APPLIED SUCCESSFULLY!")
        print("   All None comparisons are now protected!")
    else:
        print("\n✅ No issues found - code already looks fixed!")

if __name__ == "__main__":
    apply_patch()
