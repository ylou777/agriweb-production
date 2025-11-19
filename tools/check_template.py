import sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError

root = Path(__file__).resolve().parents[1]
templates_dir = root / 'templates'

env = Environment(loader=FileSystemLoader(str(templates_dir)))
try:
    # Parse phase
    tmpl = env.get_template('rapport_commune_complet.html')
    # Minimal render to catch runtime issues won't be needed; parse error is enough
    print('OK: Template parsed successfully')
except TemplateSyntaxError as e:
    print(f'TemplateSyntaxError: {e.message} at line {e.lineno}')
    # Show context lines
    try:
        lines = (templates_dir / 'rapport_commune_complet.html').read_text(encoding='utf-8').splitlines()
        start = max(0, e.lineno - 4)
        end = min(len(lines), e.lineno + 3)
        snippet = '\n'.join(f"{i+1:4}: {lines[i]}" for i in range(start, end))
        print('--- Context ---')
        print(snippet)
    except Exception:
        pass
    sys.exit(1)
except Exception as e:
    print(f'Unexpected error: {e.__class__.__name__}: {e}')
    sys.exit(2)
