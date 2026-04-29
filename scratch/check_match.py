import re

content = open('pscube_calculator.py', encoding='utf-8').read()

# Extract all keys from BORDER_DICT manually
# Find BORDER_DICT block
border_match = re.search(r'BORDER_DICT = \{(.+?)\}', content, re.DOTALL)
st_match = re.search(r'ST_CONFIG = \{', content)

border_keys = re.findall(r'"([^"]+)": \d+\.\d+', border_match.group(1))

# Site names as confirmed by browser (exact UTF-8):
site_names = [
    "eF.からくりｻｰｶｽ2 R",
    "e Re:ｾﾞﾛ season2 M13",
]

print("=== BORDER_DICT keys matching からくり or Re: ===")
for k in border_keys:
    if "からくり" in k or "Re:ｾﾞﾛ" in k:
        print(f"  BORDER key: {repr(k)}")
        print(f"  BORDER hex: {k.encode('utf-8').hex()}")

print()
print("=== Site names (as confirmed by browser) ===")
for s in site_names:
    print(f"  Site name: {repr(s)}")
    print(f"  Site hex:  {s.encode('utf-8').hex()}")

print()
print("=== Match test ===")
for s in site_names:
    match = s in border_keys
    print(f"  '{s}' in BORDER_DICT: {match}")

# Also check ST_CONFIG keys
print()
st_keys = re.findall(r'"([^"]+)": \{', content)
print("=== ST_CONFIG keys matching からくり or Re: ===")
for k in st_keys:
    if "からくり" in k or "Re:ｾﾞﾛ" in k:
        print(f"  ST key: {repr(k)}")
        print(f"  ST hex: {k.encode('utf-8').hex()}")

# get_machine_config uses == comparison
print()
print("=== get_machine_config match test ===")
for s in site_names:
    for k in st_keys:
        if k == s:
            print(f"  FOUND: '{s}' == '{k}'")
