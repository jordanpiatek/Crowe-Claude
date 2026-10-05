from common import *
d = new_doc(margin=0.5)
para(d, "Ezurio", size=14, bold=True, after=0)
para(d, "Manufacturing Systems Discovery – On-Site Agenda", size=12, bold=True, after=0)
para(d, "Discussion Dates: October 19 – 21, 2026   |   DRAFT for Ezurio review", size=10, bold=True, after=6)
para(d, "Below is the agenda we propose for the in-person discovery sessions at Gateworks (San Luis Obispo) and Irvine. The goals are to (1) see the "
        "current GWTrack shop-floor system in action and capture what it would take to keep today's level of automation and performance in NetSuite or an "
        "alternative, and (2) observe current Irvine operations and identify process optimizations for the improvement backlog. Times are a starting point and "
        "will be adjusted with your team. Highlighted items are still to be confirmed.", size=9)
para(d, "Crowe attendees: Jordan Piatek, Rohit Mukherjee (San Luis Obispo); Jordan Piatek (Irvine), with the Crowe NetSuite support team joining remotely for portions of Day 3.", size=9, after=8)

widths = [0.95, 1.65, 1.6, 3.3]
for title, date, loc, rows in DAYS:
    p = para(d, f"{title}", size=12, bold=True, color=BLUE, after=0)
    para(d, f"{date}  |  {loc}", size=9, italic=True, after=3)
    grid_table(d, ["Time", "Session", "Ezurio Attendees", "Topics"],
               [(t, f"{sid + ' ' if sid else ''}{title_}", att, [("• " + x) for x in topics] if topics else "") for t, sid, title_, att, topics in rows],
               widths)
    para(d, "", after=6)

d.add_page_break()
para(d, "Helpful Items to Have Ready (Pre-Read / Data Request)", size=12, bold=True, color=BLUE, after=2)
para(d, "Sharing what already exists – even in rough form – lets us spend onsite time on understanding rather than gathering. Please send what is easy to pull by Friday, October 16; "
        "anything not available can be shown live during the sessions.", size=9, after=4)
req = [
 ("Gateworks (San Luis Obispo)", [
   "GWTrack user guide, training material or screenshots; list of modules and reports in use",
   "Overview of how GWTrack, NetSuite and Arena are used at Gateworks (diagram, if one exists) and any integrations or scheduled jobs between them",
   "Sample work order / traveler, routing and BOM for a representative product, plus a sample of quality records (defect report / heatmap, NCR, RMA)",
   "Volumes: products / SKUs, work orders per month, headcount by role, shifts, and top customers by program (no pricing needed)",
   "Customer / contract requirements that affect systems (e.g., ITAR / CUI flow-down clauses – clauses only, no technical data)",
   "Written objectives for the next manufacturing system (including any provided by Gateworks leadership)",
 ]),
 ("Irvine", [
   "Current list of open Manufacturing Mobile / WMS issues, enhancement requests and any items already in the Azure DevOps backlog",
   "Examples of: Staged Work Orders report, Actual vs. Expected pick report, and the de-kit reconciliation templates",
   "SharePoint QMS template(s) and a sample of RMA / rework / scrap logs (past 3 months)",
   "Standard cost process: who maintains it, how often, and recent exceptions",
   "Volumes: work orders per week, headcount by role and shift, number of lines / work centers",
 ]),
 ("Logistics", [
   "Site access, safety and PPE requirements; badge / escort process; any restrictions on photos, screen-sharing or recording on the floor",
   "Conference room and Wi-Fi / guest network details for each site",
   "Confirm attendees and time blocks for each session (highlighted above)",
 ]),
]
for h, items in req:
    para(d, h, size=10, bold=True, after=1)
    for it in items: bullet(d, it)
d.save("../01_Ezurio_Onsite_Discovery_Agenda_CLIENT.docx")
print("saved")
