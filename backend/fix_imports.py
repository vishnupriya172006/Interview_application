from pathlib import Path

root = Path('.')
patterns = [
    ('from app.', 'from app.'),
    ('import app.', 'import app.'),
    ('from app', 'from app'),
    ('import app', 'import app')
]
files = [p for p in root.rglob('*.py') if p.is_file()]
for f in files:
    if 'venv' in str(f) or 'site-packages' in str(f):
        continue
    text = f.read_text(encoding='utf-8')
    new = text
    for old, newpart in patterns:
        new = new.replace(old, newpart)
    if new != text:
        f.write_text(new, encoding='utf-8')
        print(f'updated {f}')
