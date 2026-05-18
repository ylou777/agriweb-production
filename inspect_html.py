import re
with open('test_send_23096.html', encoding='utf-8') as f:
    c = f.read()
b64 = re.findall('data:image/[^;]+;base64,', c)
print('data URIs:', len(b64))
links = re.findall('href="(https?[^"]+)"', c)
for l in links:
    print('LIEN:', l)
plan = c.lower().find('plan interac')
print('plan interactif present:', plan >= 0)
imgs = re.findall('<img[^>]+src="([^"]+)"', c)
for i in imgs:
    print('IMG src:', i[:80])
