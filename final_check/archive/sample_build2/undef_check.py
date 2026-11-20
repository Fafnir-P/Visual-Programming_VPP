import ast, builtins, json, sys
data = json.load(open('sample_build2/templates.json', encoding='utf8'))
import card_templates.runtime as rt
bad = {}
for title, t in data.items():
    code = '\n\n'.join([h['source'] for h in t.get('helpers', [])] + [t['source']])
    tree = ast.parse(code)
    defined = set(dir(builtins)) | set(t['runtime'])
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)): defined.add(n.name)
        elif isinstance(n, ast.arg): defined.add(n.arg)
        elif isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)): defined.add(n.id)
        elif isinstance(n, ast.ExceptHandler) and n.name: defined.add(n.name)
        elif isinstance(n, (ast.Import, ast.ImportFrom)): defined.update((a.asname or a.name).split('.')[0] for a in n.names)
    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    miss = sorted(used - defined)
    if miss: bad[title] = miss
print(len(data), 'cards;', len(bad), 'with undefined names')
for k, v in bad.items(): print(k, v)
