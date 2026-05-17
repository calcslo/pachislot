import re

with open('docs/ogiya/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

nav_btns = re.findall(r'class="nav-btn.*?"', html)
print(f"Number of nav-btn elements: {len(nav_btns)}")
for b in nav_btns:
    print(f" - {b}")

print(f"Number of ml-next-day-container: {html.count('ml-next-day-container')}")
