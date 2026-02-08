import folium
from folium import Element

m = folium.Map(location=[44.8, 0.6], zoom_start=12, tiles=None)
folium.TileLayer(
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr='Esri', name='Satellite'
).add_to(m)
folium.TileLayer('OpenStreetMap', name='Fond OSM').add_to(m)

# Simulate add_styled_layer_control (no Element injection now)
folium.LayerControl(collapsed=True).add_to(m)

m.save('static/cartes/_test_lc2.html')

# Simulate _postprocess_map_html
import re
with open('static/cartes/_test_lc2.html', 'r', encoding='utf-8') as f:
    html = f.read()

css_link = '<link rel="stylesheet" href="/static/css/layer-control-dark.css">'
js_link = '<script src="/static/js/layer-control-dark.js"></script>'

# Clean any existing
html = re.sub(r'\s*<link[^>]*layer-control-dark\.css[^>]*>', '', html)
html = re.sub(r'\s*<script[^>]*layer-control-dark\.js[^>]*></script>', '', html)

# CSS in <head>
if '</head>' in html:
    html = html.replace('</head>', css_link + '\n</head>')

# JS at the VERY END
html = html.rstrip() + '\n' + js_link + '\n'

with open('static/cartes/_test_lc2.html', 'w', encoding='utf-8') as f:
    f.write(html)

# Verify
with open('static/cartes/_test_lc2.html', 'r', encoding='utf-8') as f:
    h = f.read()

idx_css = h.find('layer-control-dark.css')
idx_js = h.find('layer-control-dark.js')
idx_head = h.find('</head>')
idx_body = h.find('</body>')
idx_folium_script = h.find('L.control.layers')

print(f'CSS at pos {idx_css}')
print(f'</head> at pos {idx_head}')
print(f'CSS before </head>: {idx_css < idx_head}')
print(f'')
print(f'JS at pos {idx_js}')
print(f'</body> at pos {idx_body}')
print(f'Folium L.control.layers at pos {idx_folium_script}')
print(f'JS after Folium scripts: {idx_js > idx_folium_script}')
print(f'JS at very end of file: {idx_js > len(h) - 200}')
print(f'')
print('--- Last 300 chars ---')
print(h[-300:])
