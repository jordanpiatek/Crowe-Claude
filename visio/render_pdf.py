"""Renders Fulfillment_Process_Flow.vsdx to PDF (independent of Visio) by reading the shape data."""
import zipfile, textwrap
import xml.etree.ElementTree as ET
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
ns = {'v': 'http://schemas.microsoft.com/office/visio/2012/main'}
z = zipfile.ZipFile('Fulfillment_Process_Flow.vsdx')
c = lambda e, n: e.find(f"v:Cell[@N='{n}']", ns)
ps = ET.fromstring(z.read('visio/pages/pages.xml')).find('.//v:PageSheet', ns)
pw, ph = float(c(ps, 'PageWidth').get('V')), float(c(ps, 'PageHeight').get('V'))
fig = plt.figure(figsize=(pw, ph)); ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, pw); ax.set_ylim(0, ph); ax.axis('off')
for s in ET.fromstring(z.read('visio/pages/page1.xml')).iter('{%s}Shape' % ns['v']):
    g = lambda n: float(c(s, n).get('V'))
    px, py, lx, ly, w = g('PinX'), g('PinY'), g('LocPinX'), g('LocPinY'), g('Width')
    pts = [(px - lx + float(r.find("v:Cell[@N='X']", ns).get('V')), py - ly + float(r.find("v:Cell[@N='Y']", ns).get('V')))
           for r in s.findall("v:Section[@N='Geometry']/v:Row", ns)]
    t = s.find('v:Text', ns); t = t.text if t is not None else ''
    if c(s, 'EndArrow') is not None:
        ax.plot(*zip(*pts[:-1]), color='#404040', lw=1.2)
        ax.annotate('', xy=pts[-1], xytext=pts[-2], arrowprops=dict(arrowstyle='-|>', color='#404040', lw=1.2))
        continue
    nf = c(s, 'FillPattern').get('V') == '0'
    if not (nf and c(s, 'LinePattern').get('V') == '0'):
        ax.add_patch(Polygon(pts, closed=True, fc='none' if nf else c(s, 'FillForegnd').get('V'), ec=c(s, 'LineColor').get('V')))
    if t:
        size = float(s.find("v:Section[@N='Character']/v:Row/v:Cell[@N='Size']", ns).get('V')) * 72
        cpl = max(int((w - 0.2) / (size * 0.0075)), 10)
        t = '\n'.join('\n'.join(textwrap.wrap(l, cpl)) or ' ' for l in t.split('\n'))
        ax.text(px, py, t, ha='center', va='center', fontsize=size,
                color=s.find("v:Section[@N='Character']/v:Row/v:Cell[@N='Color']", ns).get('V'),
                fontweight='bold' if s.find("v:Section[@N='Character']/v:Row/v:Cell[@N='Style']", ns).get('V') == '1' else 'normal')
fig.savefig('Fulfillment_Process_Flow.pdf')
fig.savefig('/tmp/claude-0/prev3.png', dpi=50)
