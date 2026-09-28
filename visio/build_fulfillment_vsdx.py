"""Generates Fulfillment_Process_Flow.vsdx (swimlane flowchart) with no third-party deps."""
import zipfile
from xml.sax.saxutils import escape

TITLE_H, LABEL_W, BAND_H, GAP, STRIP_H = 0.9, 1.6, 3.7, 0.5, 0.6
LANE_HS = [2.3, 3.9, 2.2, 2.2]
LANES = ["Warehouse Operator 1\n(Picker / Packer)", "Warehouse Operator 2\n(Q/C / Shipper)", "ShipHawk\n(system)", "NetSuite\n(system)"]
LANE_FILL = ["#F3F8EC", "#FDF5E6", "#F1ECF8", "#EAF2FB"]
NSF, NSL, SHF, SHL, OPF, OPL = "#DEEAF6", "#1F4E79", "#E4DFEC", "#7030A0", "#FFF2CC", "#BF8F00"
BW, BH, COLW = 2.3, 1.7, 2.7
X0 = LABEL_W + 1.5
PW = X0 + 7 * COLW + BW / 2 + 0.4
PH = TITLE_H + BAND_H + GAP + sum(LANE_HS) + STRIP_H
FS = 0.125  # 9pt

def cx(c): return X0 + (c - 1) * COLW
def lane_top(l): return PH - TITLE_H - BAND_H - GAP - sum(LANE_HS[:l])
def cy(l): return lane_top(l) - LANE_HS[l] / 2
BAND_Y = PH - TITLE_H - BAND_H / 2

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

def box(c, l, txt, fill="#FFFFFF", line="#1F4E79", h=BH):
    shape(cx(c), cy(l), BW, h, geom_round(BW, h), txt, fill, line, size=0.08)

def label(x, y, txt, w=1.5, h=0.3):
    shape(x, y, w, h, geom_rect(w, h), txt, "#FFFFFF", size=0.115, color="#404040", nofill=True, nolines=True)

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


def box(c, y, txt, fill, line, w=BW, h=BH, x=None):
    shape(cx(c) if x is None else x, y, w, h, geom_round(w, h), txt, fill, line, size=FS)

# ---- title, band, lanes
shape(PW / 2, PH - TITLE_H / 2, PW, TITLE_H, geom_rect(PW, TITLE_H), "", "#1F4E79", "#1F4E79")
shape((PW - 10.5) / 2, PH - TITLE_H / 2, PW - 10.5, TITLE_H, geom_rect(PW - 10.5, TITLE_H),
      "Order Fulfillment Process Flow  |  NetSuite WMS + ShipHawk", "#1F4E79", size=0.26, color="#FFFFFF", bold=True, nofill=True, nolines=True)
for i, (nm, f_, l_) in enumerate([("NetSuite / NetSuite WMS", NSF, NSL), ("ShipHawk", SHF, SHL), ("Operator 2 review", OPF, OPL)]):
    lx = PW - 9.9 + i * 3.4
    shape(lx, PH - TITLE_H / 2, 0.3, 0.3, geom_rect(0.3, 0.3), "", f_, l_)
    shape(lx + 1.5, PH - TITLE_H / 2, 2.6, 0.3, geom_rect(2.6, 0.3), nm, "#FFFFFF", size=0.12, color="#FFFFFF", nofill=True, nolines=True)

shape(PW / 2, BAND_Y, PW, BAND_H, geom_rect(PW, BAND_H), "", "#EAF2FB", "#7F7F7F", lw=0.01)
shape(LABEL_W / 2, BAND_Y, LABEL_W, BAND_H, geom_rect(LABEL_W, BAND_H),
      "Order-to-Release\n(NetSuite scheduled scripts)", "#D9D9D9", "#7F7F7F", size=0.13, bold=True, lw=0.01)
for i, name in enumerate(LANES):
    shape(PW / 2, cy(i), PW, LANE_HS[i], geom_rect(PW, LANE_HS[i]), "", LANE_FILL[i], "#7F7F7F", lw=0.01)
    shape(LABEL_W / 2, cy(i), LABEL_W, LANE_HS[i], geom_rect(LABEL_W, LANE_HS[i]), name, "#D9D9D9", "#7F7F7F", size=0.115, bold=True, lw=0.01)

# ---- band: steps 1-3 + example timeline
TW, TH_, AH = 3.7, 3.2, 0.9
tx0 = LABEL_W + 0.3
shape(tx0 + 0.95, BAND_Y, 1.9, AH, geom_round(1.9, AH, 0.4), "Trigger:\nSupply Required By Date <= Today", "#FFFFFF", NSL, size=0.11, bold=True)
x1 = tx0 + 1.9 + 0.45 + TW / 2
x2, x3 = x1 + TW + 0.45, x1 + 2 * (TW + 0.45)
box(0, BAND_Y, "1. Automated Lot Assignment  (every 2 hrs)\nRuns on order lines where Supply Required By Date (SRD) <= Today. SRD is set at the subsidiary level via a custom field on the subsidiary record (US: 14 days prior to Customer Wanted Date).\nPriority: DPAS > Order Priority > earliest Customer Wanted Date > Spec Count > transaction/order sequence.\nLot selection: customer designation / spec requirements, then FEFO (earliest expiration).\nOccurs before commitment and warehouse release.", NSF, NSL, w=TW, h=TH_, x=x1)
box(0, BAND_Y, "2. Inventory Allocation & Commitment  (every hour)\nRuns for eligible SO/TO demand.\nLot-numbered items: lot must be assigned in Step 1 first, so committed qty = lot-assigned qty.\nNon-lot items follow the configured allocation rules.", NSF, NSL, w=TW, h=TH_, x=x2)
box(0, BAND_Y, "3. Wave Release  (every 2 hrs)\nReleases committed orders to WMS when Customer Wanted Date is within 8 days (Subsidiary 4 = US) or 4 days (all other subsidiaries).\nMust be committed, lots assigned, and pass hold / release / status / credit criteria.\nShip Complete = True: also needs Complete to Release = True.\nShip Complete = False: eligible committed qty proceeds without waiting for the full order.\nManual wave generation is also available.", NSF, NSL, w=TW, h=TH_, x=x3)
ex_l = x3 + TW / 2 + 0.45; ex_w = PW - 0.3 - ex_l
box(0, BAND_Y, "Example: Customer Wanted Date = Oct 15\n\nLot Assignment: triggered by the line's Supply Required By Date, not directly by Oct 15. If SRD = Oct 8, eligible Oct 8, evaluated on the next 2-hr run.\n\nCommitment: after lot assignment and allocation criteria are met, next hourly run.\n\nWave Release: Subsidiary 4 (US) eligible from Oct 7 (8 days); other subsidiaries from Oct 11 (4 days). Released on next 2-hr wave run once all other requirements are met.", "#FFFFFF", "#7F7F7F", w=ex_w, h=TH_, x=ex_l + ex_w / 2)
arrow([(tx0 + 1.9, BAND_Y), (x1 - TW / 2, BAND_Y)])
arrow([(x1 + TW / 2, BAND_Y), (x2 - TW / 2, BAND_Y)])
arrow([(x2 + TW / 2, BAND_Y), (x3 - TW / 2, BAND_Y)])

# ---- swimlane steps
Y1, Y2, Y3, Y4 = cy(0), cy(1), cy(2), cy(3)
YS, YU = Y2 + 1.0, Y2 - 1.0
box(1, Y1, "4. Pick Order  [NetSuite WMS]\nOperator 1 picks using individual device login. Picker captured (prints on Packing Slip header). Shipment/item images captured and associated with the fulfillment.", NSF, NSL)
box(2, Y1, "5. Pack Order  [ShipHawk Smart Pack]\nOperator 1 (same operator who picked) packs the order in ShipHawk.", SHF, SHL)
box(0, Y3, "Order syncs\nNetSuite > ShipHawk", SHF, SHL, w=1.7, h=1.0, x=(cx(1) + cx(2)) / 2)
box(3, Y2, "6. Quality Control (Q/C)\nOperator 2 reviews packed shipment and WMS pick images; confirms ready for carrier booking.", OPF, OPL)
DW, DH = 2.3, 1.7
shape(cx(4), Y2, DW, DH, geom_diamond(DW, DH), "7. Book & Ship\nOperator 2\nCarrier supported by ShipHawk?", OPF, OPL, size=FS)
box(5, YS, "Supported Carrier  [ShipHawk]\nOperator 2 processes and marks the shipment as Shipped directly in ShipHawk.", SHF, SHL)
box(5, YU, "Unsupported Carrier  [ShipHawk]\nOperator 2 processes as External Shipment in ShipHawk, books on the external carrier site, and updates ShipHawk.", SHF, SHL)
box(6, Y3, "ShipHawk writes shipment info back to NetSuite (incl. shipper email / user ID)", SHF, SHL)
box(7, Y4, "8. Complete Fulfillment  [NetSuite]\nItem Fulfillment = Shipped. Picker = WMS picker; Q/C = shipping user with signature. Packing Slip can be printed.", NSF, NSL)
box(8, Y4, "9. Print Final Shipping Docs  [NetSuite]\nPacking Slip\nBOL (CMR)\nCommercial Invoice", NSF, NSL)

# ---- connectors
gy = PH - TITLE_H - BAND_H - GAP / 2
arrow([(x3, BAND_Y - TH_ / 2), (x3, gy), (cx(1), gy), (cx(1), Y1 + BH / 2)])
label(cx(1) + 2.6, gy + 0.18, "Released to WMS for picking", w=3.0, h=0.28)
arrow(elbow(0, 0, cx(1), Y1, cx(2), Y1))
arrow([(cx(1), Y1 - BH / 2), (cx(1), Y3), (cx(1.5) - 0.85, Y3)])
arrow([(cx(1.5) + 0.85, Y3), (cx(2), Y3), (cx(2), Y1 - BH / 2)])
arrow(elbow(0, 0, cx(2), Y1, cx(3), Y2))
arrow([(cx(3) + BW / 2, Y2), (cx(4) - DW / 2, Y2)])
arrow([(cx(4), Y2 + DH / 2), (cx(4), YS), (cx(5) - BW / 2, YS)])
label(cx(4) + 0.35, Y2 + DH / 2 + 0.2, "Yes", w=0.5, h=0.28)
arrow([(cx(4), Y2 - DH / 2), (cx(4), YU), (cx(5) - BW / 2, YU)])
label(cx(4) + 0.35, Y2 - DH / 2 - 0.2, "No", w=0.5, h=0.28)
arrow(elbow(0, 0, cx(5), YS, cx(6), Y3))
arrow(elbow(0, 0, cx(5), YU, cx(6), Y3))
arrow(elbow(0, 0, cx(6), Y3, cx(7), Y4))
arrow(elbow(0, 0, cx(7), Y4, cx(8), Y4))

shape(PW / 2, STRIP_H / 2, PW - 2, 0.35, geom_rect(PW - 2, 0.35),
      "Overall: Supply Required By Date reached > Lot Assignment (2 hrs) > Commitment (1 hr) > Customer Wanted Date release window reached > Wave Release (2 hrs) > WMS Picking",
      "#FFFFFF", size=0.125, bold=True, nofill=True, nolines=True)

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
