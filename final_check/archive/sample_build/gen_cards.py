import json
g=json.load(open('graph.json'))
seen=[]
out=['"""Card template code, copied unchanged from the request (templateCode of each card)."""',
'from card_templates.runtime import CardError, coerce_value, iso, round_half_up, to_number, view','']
for n in g['nodes']:
    if n['templateCode'] in seen: continue
    seen.append(n['templateCode'])
    out.append(n['templateCode'].strip('\n')); out.append(''); out.append('')
open('generated/cards.py','w',encoding='utf-8').write('\n'.join(out))
