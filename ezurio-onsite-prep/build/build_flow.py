import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import textwrap

fig, ax = plt.subplots(figsize=(22, 9.5)); ax.set_xlim(0, 22); ax.set_ylim(0, 9.5); ax.axis("off")
NAVY = "#002060"
ax.text(0.3, 9.1, "Irvine WMS & Manufacturing Process Flow – Current State (July 2025 go-live)", fontsize=17, fontweight="bold", color=NAVY, va="center")
ax.text(0.3, 8.65, "Source: Irvine WMS & MFG Process Flow (Visio) + 2025 process outlines.  Red boxes = questions to validate onsite (Wed 10/21, Session 3.2).  INTERNAL working draft.", fontsize=10, color="#555", va="center")

lanes = [("Material\nHandler\n/ QC", 4.3, 7.9, "#EEF3FA"), ("Production\nOperator", 1.6, 4.2, "#F7F3EA")]
for name, y0, y1, col in lanes:
    ax.add_patch(plt.Rectangle((0.3, y0), 21.4, y1 - y0, fc=col, ec="#999", lw=1))
    ax.add_patch(plt.Rectangle((0.3, y0), 1.5, y1 - y0, fc=NAVY, ec="#999"))
    ax.text(1.05, (y0 + y1) / 2, name, color="white", fontsize=11, fontweight="bold", ha="center", va="center")

def box(x, y, w, h, text, fc="white", ec=NAVY, fs=9.2, bold=False, shape="round"):
    st = "round,pad=0.02,rounding_size=0.25" if shape == "round" else "round,pad=0.02,rounding_size=0.05"
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle=st, fc=fc, ec=ec, lw=1.6))
    ax.text(x, y, textwrap.fill(text, 22 if w < 2.4 else 30), ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal")

def arrow(x1, y1, x2, y2, col="#333"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14, lw=1.4, color=col, shrinkA=0, shrinkB=0))

top = 6.2
steps = [
 (2.7, "Start", "start"),
 (4.5, "1. Confirm component allocation; reallocate if necessary", None),
 (6.9, "2. Pick in WMS app (only once fully allocated / committed)", None),
 (9.3, "3. Stage picked inventory to staging bin; physically mark bin", None),
 (11.7, "4. Generate Staged Work Order report for QC team", None),
 (14.1, "5. Perform pick review of expected quantities (Actual vs. Expected)", None),
 (16.5, "6. Transfer staged inventory to Production Input Bin; physically mark", None),
 (18.9, "7. Create Work Order Issue; verify inventory detail; mark bin 'Issued'", None),
]
prev = None
for x, t, kind in steps:
    if kind == "start": box(x, top, 1.3, 0.7, "Start", fc="#DDE6F3", bold=True)
    else: box(x, top, 2.0, 1.25, t)
    if prev: arrow(prev + (0.65 if prev == 2.7 else 1.0), top, x - 1.0, top)
    prev = x
# down to operator lane
arrow(18.9, top - 0.63, 18.9, 3.65)
box(18.9, 3.0, 2.0, 1.25, "8. Process production operations in MFG Mobile (badge in, scan WO, pause / end, completions)")
box(15.5, 3.0, 2.2, 1.25, "9. Transfer completed assembly to Lab Input or back to warehouse")
box(12.4, 3.0, 1.3, 0.7, "End", fc="#DDE6F3", bold=True)
arrow(17.9, 3.0, 16.6, 3.0); arrow(14.4, 3.0, 13.05, 3.0)

def q(x, y, w, h, text, tx, ty):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.02,rounding_size=0.1", fc="#FFD9D9", ec="#C00000", lw=1.2))
    ax.text(x, y, textwrap.fill("Q: " + text, 34), ha="center", va="center", fontsize=8.3)
    arrow(x, y + (h / 2 if ty > y else -h / 2), tx, ty, col="#C00000")

q(4.5, 8.15 - 0.55, 2.7, 0.9, "How often are lines not fully committed? How are 'Special Order' lines reallocated today?", 4.5, top + 0.63)
q(6.0, 4.85, 3.0, 0.8, "How often do partial picks occur? (task closes -> reverse pick). Workarounds?", 6.9, top - 0.63)
q(9.6, 4.85, 3.2, 0.8, "Staging: is one-WO-per-bin followed? What happens when staging bins are full? Is physical marking reliable?", 9.3, top - 0.63)
q(14.1, 7.85, 3.1, 0.9, "Who runs the Actual vs. Expected review, when, and what gets corrected?", 14.1, top + 0.63)
q(19.3, 8.1 - 0.05, 3.4, 1.0, "WHO creates Transfer-All & WO Issue? Visio shows Material Handler; 2025 outline says QC. How often does it error?", 18.9, top + 0.63)
q(20.3, 0.9, 3.0, 0.95, "No hard control if material is short or standard cost is missing. How often? What is the impact?", 19.2, 2.35)
q(15.5, 0.9, 3.5, 0.95, "Timekeeping gaps vs. Ezurio requirements: pause/end, indirect, rework, multi-operator. Auto-Mark WOs Built workflow suspended 10/1 – why?", 17.9, 2.35)
q(9.0, 0.9, 3.4, 0.95, "Lab / test WO for programmed boards: who decides lab vs. warehouse, how recorded? De-kit reconciliation afterwards (templates + imports).", 12.4, 2.65)
plt.savefig("../04_Irvine_Process_Flow_Annotated.png", dpi=110, bbox_inches="tight", facecolor="white")
print("ok")
