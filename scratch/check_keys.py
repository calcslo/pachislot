import re
content = open('pscube_calculator.py', encoding='utf-8').read()
lines = re.findall(r'\"([^\"]+)\": \d+\.\d+', content)
for k in lines:
    if "からくり" in k or "Re:ｾﾞﾛ" in k:
        print(f"Key: {repr(k)} | Hex: {k.encode('utf-8').hex()}")
