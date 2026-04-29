import re
content = open('pscube_calculator.py', encoding='utf-8').read()
lines = content.splitlines()
for i, line in enumerate(lines):
    if 'からくり' in line or 'Re:ｾﾞﾛ' in line:
        # Check for non-breaking spaces or other oddities
        for char in line:
            if ord(char) > 127:
                pass # Normal for Japanese
            elif char.isspace() and char != ' ':
                print(f"Line {i+1}: Found unusual space {repr(char)} (ord {ord(char)})")
        
        # Check for multiple spaces
        if '  ' in line:
            print(f"Line {i+1}: Found double space")
            
        print(f"Line {i+1}: {repr(line)}")
