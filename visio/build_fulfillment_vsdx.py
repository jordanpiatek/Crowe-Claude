"""Generates Fulfillment_Process_Flow.vsdx (swimlane flowchart) with no third-party deps."""
import zipfile
from xml.sax.saxutils import escape

LANE_H, TITLE_H, LABEL_W = 2.3, 0.9, 1.6
LANES = ["NetSuite", "Warehouse Operator 1\n(Picker / Packer)", "Warehouse Operator 2\n(Q/C / Shipper)", "ShipHawk"]
LANE_FILL = ["#EAF2FB", "#F3F8EC", "#FDF5E6", "#F1ECF8"]
NCOL, COLW, X0 = 11, 2.45, LABEL_W + 1.5
PW = X0 + (NCOL - 1) * COLW + 1.9
PH = TITLE_H + LANE_H * len(LANES)
BW, BH = 2.05, 1.5

def cx(c): return X0 + (c - 1) * COLW
def cy(l): return PH - TITLE_H - LANE_H * (l + 0.5)

shapes, sid = [], [0]

def cell(n, v, f=None):
    return f"<Cell N='{n}' V='{v}'" + (f" F='{f}'" if f else "") + "/>"

def add(xml):
    sid[0] += 1
    shapes.append(xml.replace("@ID@", str(sid[0])))

def text_sec(txt, size=0.1, color="#000000", bold=False):
    style = "1" if bold else "0"
    return (f"<Section N='Character'><Row IX='0'>{cell('Size', size)}{cell('Color', color)}{cell('Style', style)}</Row></Section>"
            f"<Text>{escape(txt)}</Text>")

def geom_rect(w, h):
    return ("<Section N='Geometry' IX='0'>"
            f"<Row T='MoveTo' IX='1'>{cell('X',0)}{cell('Y',0)}</Row>"
            f"<Row T='LineTo' IX='2'>{cell('X',w)}{cell('Y',0)}</Row>"
            f"<Row T='LineTo' IX='3'>{cell('X',w)}{cell('Y',h)}</Row>"
            f"<Row T='LineTo' IX='4'>{cell('X',0)}{cell('Y',h)}</Row>"
            f"<Row T='LineTo' IX='5'>{cell('X',0)}{cell('Y',0)}</Row></Section>")

def geom_round(w, h, r=0.12):
    return ("<Section N='Geometry' IX='0'>"
            f"<Row T='MoveTo' IX='1'>{cell('X',r)}{cell('Y',0)}</Row>"
            f"<Row T='LineTo' IX='2'>{cell('X',w-r)}{cell('Y',0)}</Row>"
            f"<Row T='ArcTo' IX='3'>{cell('X',w)}{cell('Y',r)}{cell('A',-r*0.4142)}</Row>"
            f"<Row T='LineTo' IX='4'>{cell('X',w)}{cell('Y',h-r)}</Row>"
            f"<Row T='ArcTo' IX='5'>{cell('X',w-r)}{cell('Y',h)}{cell('A',-r*0.4142)}</Row>"
            f"<Row T='LineTo' IX='6'>{cell('X',r)}{cell('Y',h)}</Row>"
            f"<Row T='ArcTo' IX='7'>{cell('X',0)}{cell('Y',h-r)}{cell('A',-r*0.4142)}</Row>"
            f"<Row T='LineTo' IX='8'>{cell('X',0)}{cell('Y',r)}</Row>"
            f"<Row T='ArcTo' IX='9'>{cell('X',r)}{cell('Y',0)}{cell('A',-r*0.4142)}</Row></Section>")

def geom_diamond(w, h):
    return ("<Section N='Geometry' IX='0'>"
            f"<Row T='MoveTo' IX='1'>{cell('X',w/2)}{cell('Y',0)}</Row>"
            f"<Row T='LineTo' IX='2'>{cell('X',w)}{cell('Y',h/2)}</Row>"
            f"<Row T='LineTo' IX='3'>{cell('X',w/2)}{cell('Y',h)}</Row>"
            f"<Row T='LineTo' IX='4'>{cell('X',0)}{cell('Y',h/2)}</Row>"
            f"<Row T='LineTo' IX='5'>{cell('X',w/2)}{cell('Y',0)}</Row></Section>")

def shape(x, y, w, h, geom, txt, fill, line="#1F4E79", size=0.1, color="#000000", bold=False, lw=0.014, nofill=False, nolines=False):
    add(f"<Shape ID='@ID@' Type='Shape'>{cell('PinX',x)}{cell('PinY',y)}{cell('Width',w)}{cell('Height',h)}"
        f"{cell('LocPinX',w/2)}{cell('LocPinY',h/2)}"
        f"{cell('FillForegnd',fill)}{cell('FillPattern', 0 if nofill else 1)}{cell('LineColor',line)}{cell('LineWeight',lw)}"
        f"{cell('LinePattern', 0 if nolines else 1)}"
        f"{cell('TxtWidth',w-0.1)}{cell('TxtHeight',h)}{cell('TxtPinX',w/2)}{cell('TxtPinY',h/2)}{cell('TxtLocPinX',(w-0.1)/2)}{cell('TxtLocPinY',h/2)}"
        f"{cell('VerticalAlign',1)}{geom}{text_sec(txt,size,color,bold)}</Shape>")

def box(c, l, txt, fill="#FFFFFF", line="#1F4E79"):
    shape(cx(c), cy(l), BW, BH, geom_round(BW, BH), txt, fill, line, size=0.085)

def label(x, y, txt, w=1.5, h=0.3):
    shape(x, y, w, h, geom_rect(w, h), txt, "#FFFFFF", size=0.085, color="#595959", nofill=True, nolines=True)

def arrow(pts, dash=False):
    """Polyline connector through absolute page points, arrowhead at the end."""
    minx, miny = min(p[0] for p in pts), min(p[1] for p in pts)
    w = max(max(p[0] for p in pts) - minx, 0.01); h = max(max(p[1] for p in pts) - miny, 0.01)
    rows = "".join(f"<Row T='{'MoveTo' if i==0 else 'LineTo'}' IX='{i+1}'>{cell('X',p[0]-minx)}{cell('Y',p[1]-miny)}</Row>"
                   for i, p in enumerate(pts))
    add(f"<Shape ID='@ID@' Type='Shape'>{cell('PinX',minx)}{cell('PinY',miny)}{cell('Width',w)}{cell('Height',h)}"
        f"{cell('LocPinX',0)}{cell('LocPinY',0)}{cell('LineColor','#404040')}{cell('LineWeight',0.016)}"
        f"{cell('EndArrow',5)}{cell('EndArrowSize',2)}{cell('LinePattern', 2 if dash else 1)}{cell('FillPattern',0)}"
        f"<Section N='Geometry' IX='0'>{cell('NoFill',1)}{rows}</Section></Shape>")

def elbow(a, b, ax, ay, bx, by):
    """right side of box at (ax,ay) -> left side of box at (bx,by) with a vertical jog midway"""
    x1, x2 = ax + BW / 2, bx - BW / 2
    if abs(ay - by) < 0.01: return [(x1, ay), (x2, by)]
    m = (x1 + x2) / 2
    return [(x1, ay), (m, ay), (m, by), (x2, by)]

# ---- lanes & title
shape(PW / 2, PH - TITLE_H / 2, PW, TITLE_H, geom_rect(PW, TITLE_H),
      "Order Fulfillment Process Flow  |  NetSuite WMS + ShipHawk", "#1F4E79", "#1F4E79", size=0.2, color="#FFFFFF", bold=True)
for i, name in enumerate(LANES):
    y = cy(i)
    shape(PW / 2, y, PW, LANE_H, geom_rect(PW, LANE_H), "", LANE_FILL[i], "#7F7F7F", lw=0.01)
    shape(LABEL_W / 2, y, LABEL_W, LANE_H, geom_rect(LABEL_W, LANE_H), name, "#D9D9D9", "#7F7F7F", size=0.12, bold=True, lw=0.01)

# ---- steps
box(1, 0, "1. Lot Assignment\nLot assigned to the Sales Order per inventory allocation rules")
box(2, 0, "2. Inventory Commitment\nInventory committed to the Sales Order")
box(3, 0, "3. Wave Release\nAutomatic wave release\nor Manual wave generation")
box(4, 1, "4. Pick Order (NetSuite WMS)\nIndividual device login; Picker captured (prints on Packing Slip); shipment/item images captured", "#E2F0D9", "#548235")
box(5, 1, "5. Pack Order\nShipHawk Smart Pack\nSame operator who picked", "#E2F0D9", "#548235")
box(6, 2, "6. Quality Control (Q/C)\nReview packed shipment and WMS pick images; confirm ready for carrier booking", "#FFF2CC", "#BF8F00")
# decision
DW, DH = 2.1, 1.4
shape(cx(7), cy(2), DW, DH, geom_diamond(DW, DH), "7. Book & Ship\nCarrier supported by ShipHawk?", "#FFF2CC", "#BF8F00", size=0.085)
box(8, 2, "Unsupported Carrier\nProcess as External Shipment in ShipHawk; book on external carrier site; update ShipHawk", "#FFF2CC", "#BF8F00")
box(8, 3, "Supported Carrier\nProcess and mark shipment as Shipped in ShipHawk", "#E4DFEC", "#7030A0")
box(9, 3, "ShipHawk writes shipment info back to NetSuite\n(incl. shipper email / user ID)", "#E4DFEC", "#7030A0")
box(10, 0, "8. Complete Fulfillment\nItem Fulfillment = Shipped; Picker = WMS picker; Q/C = shipping user with signature; Packing Slip printable", "#DEEAF6", "#1F4E79")
box(11, 0, "9. Print Final Shipping Docs\nPacking Slip\nBOL (CRM)\nCommercial Invoice", "#DEEAF6", "#1F4E79")

# ---- connectors
arrow(elbow(0, 0, cx(1), cy(0), cx(2), cy(0)))
arrow(elbow(0, 0, cx(2), cy(0), cx(3), cy(0)))
arrow(elbow(0, 0, cx(3), cy(0), cx(4), cy(1)))
arrow(elbow(0, 0, cx(4), cy(1), cx(5), cy(1)))
label((cx(4) + cx(5)) / 2, cy(1) + BH / 2 + 0.22, "Order syncs NetSuite → ShipHawk", w=3.0, h=0.3)
arrow(elbow(0, 0, cx(5), cy(1), cx(6), cy(2)))
arrow([(cx(6) + BW / 2, cy(2)), (cx(7) - DW / 2, cy(2))])
arrow([(cx(7) + DW / 2, cy(2)), (cx(8) - BW / 2, cy(2))])
label(cx(7) + DW / 2 + 0.15, cy(2) + 0.2, "No", w=0.4, h=0.25)
arrow([(cx(7), cy(2) - DH / 2), (cx(7), cy(3)), (cx(8) - BW / 2, cy(3))])
label(cx(7) + 0.3, cy(2) - DH / 2 - 0.2, "Yes", w=0.4, h=0.25)
arrow(elbow(0, 0, cx(8), cy(2), cx(9), cy(3)))
arrow(elbow(0, 0, cx(8), cy(3), cx(9), cy(3)))
arrow(elbow(0, 0, cx(9), cy(3), cx(10), cy(0)))
arrow(elbow(0, 0, cx(10), cy(0), cx(11), cy(0)))

# ---- package
NS = "http://schemas.microsoft.com/office/visio/2012/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
page = f"<?xml version='1.0' encoding='utf-8'?><PageContents xmlns='{NS}' xmlns:r='{R}' xml:space='preserve'><Shapes>{''.join(shapes)}</Shapes></PageContents>"
files = {
"[Content_Types].xml": "<?xml version='1.0' encoding='utf-8'?><Types xmlns='http://schemas.openxmlformats.org/package/2006/content-types'>"
 "<Default Extension='rels' ContentType='application/vnd.openxmlformats-package.relationships+xml'/><Default Extension='xml' ContentType='application/xml'/>"
 "<Override PartName='/visio/document.xml' ContentType='application/vnd.ms-visio.drawing.main+xml'/>"
 "<Override PartName='/visio/pages/pages.xml' ContentType='application/vnd.ms-visio.pages+xml'/>"
 "<Override PartName='/visio/pages/page1.xml' ContentType='application/vnd.ms-visio.page+xml'/></Types>",
"_rels/.rels": f"<?xml version='1.0' encoding='utf-8'?><Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'><Relationship Id='rId1' Type='http://schemas.microsoft.com/visio/2010/relationships/document' Target='visio/document.xml'/></Relationships>",
"visio/document.xml": f"<?xml version='1.0' encoding='utf-8'?><VisioDocument xmlns='{NS}' xmlns:r='{R}' xml:space='preserve'><DocumentSettings/></VisioDocument>",
"visio/_rels/document.xml.rels": "<?xml version='1.0' encoding='utf-8'?><Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'><Relationship Id='rId1' Type='http://schemas.microsoft.com/visio/2010/relationships/pages' Target='pages/pages.xml'/></Relationships>",
"visio/pages/pages.xml": f"<?xml version='1.0' encoding='utf-8'?><Pages xmlns='{NS}' xmlns:r='{R}' xml:space='preserve'><Page ID='0' Name='Fulfillment Flow' NameU='Fulfillment Flow'><PageSheet>{cell('PageWidth',PW)}{cell('PageHeight',PH)}{cell('PageScale',1)}{cell('DrawingScale',1)}</PageSheet><Rel r:id='rId1'/></Page></Pages>",
"visio/pages/_rels/pages.xml.rels": "<?xml version='1.0' encoding='utf-8'?><Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'><Relationship Id='rId1' Type='http://schemas.microsoft.com/visio/2010/relationships/page' Target='page1.xml'/></Relationships>",
"visio/pages/page1.xml": page,
}
out = "/home/user/Crowe-Claude/visio/Fulfillment_Process_Flow.vsdx"
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for k, v in files.items(): z.writestr(k, v)
print("wrote", out)
