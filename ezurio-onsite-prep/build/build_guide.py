from common import *
from guide_content import S, APPS
d = new_doc(margin=0.75)
para(d, "Ezurio", size=18, bold=True, after=0)
para(d, "Manufacturing Systems Discovery – On-Site Discussion Guide", size=14, after=0)
para(d, "October 19 – 21, 2026  |  INTERNAL – DO NOT SHARE WITH CLIENT", size=11, italic=True, bold=True, color="C00000", after=4)
para(d, "Gateworks (San Luis Obispo): 3026 South Higuera Street, San Luis Obispo, CA 93401   |   Irvine: 16450 Scientific, Irvine, CA 92618", size=9, after=8)

d.add_heading("How to use this guide", 2)
para(d, "Each session is organized as Topic > Subtopic > Probing questions, matching the client-facing agenda. Lean on the questions that fit the conversation and skip what is answered organically. "
        "Items in italics are facilitator notes – not questions to ask out loud. Everything captured goes into the Requirements & Observations tracker (03_…xlsx) so it feeds the end-of-week deliverable directly.")
para(d, "Cross-cutting prompts that work in any session:", bold=True, after=2)
for x in ["\"Show me, don't tell me.\" Open the system, walk a real record, don't describe it.",
          "\"Who's the keeper of [X]?\" Identify the single person who knows the most.",
          "\"What does the system do automatically vs. what does a person do?\" – for every feature seen.",
          "\"What would happen if this went away tomorrow?\" Separates must-keep from nice-to-have.",
          "\"If you could fix one thing about [X] tomorrow, what would it be?\"",
          "\"What would the customer or an auditor ask to see?\""]:
    bullet(d, x)

d.add_heading("Ground rules for this engagement", 2)
for x in [
  "CONFIDENTIAL BACKGROUND: do not mention, hint at or discuss any acquisition/diligence activity, a possible third site, or consolidating sites. Position everything as (a) Irvine process improvements and (b) what it would take to keep Gateworks' automation and performance in a NetSuite-based or third-party solution.",
  "ITAR / CUI: until Ezurio compliance confirms otherwise, treat all Gateworks data, screens and photos as potentially controlled. No recording, no screen captures leaving the site, no sharing with non-US Crowe personnel (incl. the Y-Hire team and international staff) until cleared. See Session 2.2.",
  "Footprint-neutral: the three footprint options and the three system options (A: GWTrack, B: Manufacturing Mobile / Advanced Mfg, C: third-party MES / SuiteApp) are assessed together later. Onsite we capture facts and requirements only – no recommendations.",
  "Out of scope (per engagement letter): implementation, configuration, data migration, integration build, and non-manufacturing functional areas.",
  "Daily rhythm: 15-minute Crowe debrief after each day → update tracker → send Sohaa the end-of-day notes (once ITAR handling is confirmed for Gateworks material).",
]: bullet(d, x)

d.add_heading("Schedule at a glance", 2)
glance = []
for title, date, loc, rows in DAYS:
    for t, sid, name, att, topics in rows:
        if sid: glance.append((date.split(",")[0][:3] + " " + t, sid, name))
grid_table(d, ["When", "#", "Session"], glance, [1.6, 0.5, 4.9])

for title, date, loc, rows in DAYS:
    d.add_page_break()
    h = d.add_heading(f"{title}", 1)
    para(d, f"{date}  |  {loc}", italic=True, size=9)
    for t, sid, name, att, topics in rows:
        if not sid: continue
        title_, when, who, note, blocks = S[sid]
        banner(d, f"Session {sid}: {title_}", f"{when}  |  {who}")
        para(d, note, italic=True, size=9)
        for sub, qs in blocks:
            d.add_heading(sub, 3)
            for q in qs:
                if q.startswith("NOTE:"):
                    bullet(d, q[5:].strip(), italic=True)
                else:
                    bullet(d, q)

d.add_page_break()
d.add_heading("Appendix A – Working application inventory (to validate onsite)", 1)
para(d, "Hypotheses built from the August assessment, the Sept client update and the 2025 Irvine documentation. Validate and correct in Session 2.1 and 3.1/3.2, then convert to a current-state application map for the readout.", italic=True, size=9)
grid_table(d, ["System", "What it is", "Known / suspected role", "To validate"], APPS, [1.3, 1.5, 2.2, 2.0], size=8.5)

d.add_heading("Appendix B – Irvine process baseline (July 2025 go-live)", 1)
para(d, "Source: Irvine WMS & MFG Process Flow (Visio) and 2025 process outlines. Validate each step in Session 3.2.", italic=True, size=9)
steps = [
 ("1", "Material Handler", "Confirm component allocation; reallocate if necessary", "Lines must be fully committed before WMS pick; 'Special Order' lines need manual reallocation"),
 ("2", "Material Handler", "Pick in WMS app (only once fully allocated/committed)", "Partial pick closes the task – reverse pick needed"),
 ("3", "Material Handler", "Stage picked inventory to the appropriate staging bin; physically mark bin", "One WO per staging bin"),
 ("4", "Material Handler", "Generate Staged Work Order report for QC team", "QC highlights under-picked items"),
 ("5", "Material Handler / WH Manager", "Perform pick review of expected quantities (Actual vs. Expected)", "Warehouse manager corrects discrepancies"),
 ("6", "Material Handler / QC", "Transfer staged inventory to Production Input Bin; physically mark", "'Transfer All Bin Transfer' – 2025 outline says QC executes"),
 ("7", "Material Handler / QC", "Create Work Order Issue; ensure inventory detail accuracy; physically mark bin Issued", "Visio shows Material Handler lane; 2025 outline says QC creates – VALIDATE"),
 ("8", "Production Operator", "Process production operations in MFG Mobile", "Badge in, scan WO, pause/end time, completions; no hard control for missing material/standard cost"),
 ("9", "Production Operator", "Transfer completed assembly to Lab Input or back to warehouse", "Non-programmed variants go to Lab for programming/test WO"),
]
grid_table(d, ["#", "Role", "Step", "Notes / questions"], steps, [0.3, 1.4, 2.8, 2.5], size=8.5)

d.add_heading("Appendix C – Questions to settle for the deliverable", 1)
for x in ["Final format: the EL calls for (1) synthesized observations across both sites, (2) captured requirements for the next phase, and (3) a proposed action for a future implementation engagement. Confirm audience and depth with Grant/David.",
          "Third-party MES: the EL asks which MES applications could address requirements and which are recommended – scope this as a long-list-to-short-list screen against the tracker, not a full selection.",
          "Option scoring: use tracker tab 5 to score Options A / B / C against weighted criteria; footprint (site) options are layered on later by Crowe leadership – not discussed onsite."]:
    bullet(d, x)
d.save("../02_Ezurio_Onsite_Discussion_Guide_INTERNAL.docx")
print("saved")
