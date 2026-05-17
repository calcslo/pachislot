import sys
import re

with open('docs/ogiya/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Lines 1075 to 1104:
old_container_regex = r'<!-- Next Day Prediction Container -->\s*<div id="ml-next-day-container"\s*style="margin-bottom: 2rem; background: var\(--card-bg\).*?</div>\s*</div>\s*<!-- Next Day Prediction Container -->'

# Remove the first one
content = re.sub(old_container_regex, '<!-- Next Day Prediction Container -->', content, flags=re.DOTALL)

with open('docs/ogiya/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Removed duplicate")
