# Each session: (id, title, time, who, facilitator note, [(subtopic, [questions...])])
# Questions starting with "NOTE:" render as italic facilitator notes.
S = {}

S["1.1"] = ("Kickoff & Objectives", "Mon 10/19 · 8:00 – 8:45", "David, John, Gateworks leadership [[TBC]]",
 "Alignment, not requirements. Keep the framing on Gateworks' automation and performance and the Irvine improvements. Do NOT reference the footprint decision, any acquisition activity, or any site consolidation – that is confidential and the site teams are not briefed.",
 [("Defining success", [
   "In 12–18 months, what should Gateworks be able to do that it can't do today – and what must it NOT lose?",
   "When you say 'keep the level of automation and performance', what are the 3–5 specific things you mean?",
   "What would make this a failure in your eyes (e.g., slower floor, more manual entry, loss of traceability)?",
   "Are there metrics leadership watches – cycle time, first-pass yield, on-time ship, scrap rate, labor efficiency?"]),
  ("Decision-making and governance", [
   "Who ultimately decides the manufacturing system direction – and who is only consulted?",
   "Who is 'Jason' in terms of this effort and what are his objectives for the MES? Is there a written version?",
   "NOTE: The client email says the MES search must meet Jason's objectives – confirm role/title and whether he joins any session.",
   "Who at Gateworks will be hands-on with requirements after this week (single point of contact)?"]),
  ("Constraints and guardrails", [
   "Timing: any production peaks, shutdowns, customer audits or deliveries we should plan around?",
   "Budget or hosting guardrails already communicated for the next phase?",
   "Any vendors/solutions already ruled in or out?"]),
  ("What's top of mind", [
   "What worries you most about moving off GWTrack's way of working?",
   "What are we not asking about that we should be?",
   "What has been tried before that didn't stick?"])])

S["1.2"] = ("Gateworks Operations Walk", "Mon 10/19 · 8:45 – 10:45", "Operations/production lead, quality lead, supervisors [[TBC]]",
 "Follow one real job end to end. 'Show me, don't tell me.' Capture where people touch a screen/scanner and where they leave the system (paper, spreadsheet, whiteboard). Photos only if the site allows – and see the ITAR/CUI note in 2.2 before capturing anything.",
 [("Product and flow", [
   "What does Gateworks build, in what volumes and mix? High-mix/low-volume? Any build-to-order vs. build-to-stock?",
   "Walk us through the flow: receiving → kitting → build/assembly → test → pack/ship. Where are the queues?",
   "Which steps are most sensitive to getting the wrong material, revision, or process?"]),
  ("Work release and execution", [
   "How is a job released to the floor and who decides what runs next? What does the traveler/work instruction look like?",
   "What stops a job from starting without all material? Is that a system hard-stop or a person?",
   "How do operators start/stop/pause a job – scan, touchscreen, paper? How many seconds/clicks per transaction?",
   "How are engineering changes (BOM/routing revisions) pushed to the floor – and how do you know the floor has the right revision?"]),
  ("Materials and inventory on the floor", [
   "How is material kitted and moved – WIP locations, bins, carts? Are WIP locations tracked in the system?",
   "How are shortages found and communicated? Who expedites?",
   "How are line-side consumption and backflush handled? How accurate is inventory at the floor?"]),
  ("People and pain points", [
   "If you could fix one thing about the floor tomorrow, what would it be?",
   "What are the 'tribal knowledge' tasks only one or two people can do?",
   "Where do people work around the system today – and why?"])])

S["1.3"] = ("GWTrack Demo I – Production Execution & Traceability", "Mon 10/19 · 11:00 – 12:30", "GWTrack power users/admin, production control [[TBC]]",
 "Have them drive. Record screens/key fields as feature inventory rows in the Requirements tracker (tab 2) – one row per capability. Ask 'what does the system do automatically vs. what does a person do?' for each. Per client update: GWTrack will not be easily modified into an MES, so capture what it does today in enough detail to rationalize across NetSuite / Arena / a new MES.",
 [("Feature inventory – production", [
   "Walk the full lifecycle in GWTrack: order/job creation → release → execution → completion → close. Which parts are native GWTrack, which pull from NetSuite, which from Arena?",
   "What objects/records exist (jobs, operations, work centers, lots/serials, kits, test results)? Can we see the data model or a field list?",
   "How are routings, work instructions and documents presented to operators? Version control?",
   "What validations/hard-stops exist (wrong material, missing prior operation, expired cal/training, out-of-sequence)?"]),
  ("Material availability and issue", [
   "How does GWTrack know material is available before a job starts? Where does inventory truth live (GWTrack vs. NetSuite)?",
   "How are components issued/consumed – scan-driven, backflush, manual? How are substitutions and alternates handled?",
   "How are shortages and over/under-issue handled?"]),
  ("Traceability and genealogy", [
   "What traceability is captured (lot, serial, date code, operator, station, equipment, test data)? How is it queried – e.g., 'show everything built with lot X'?",
   "How long can a recall / containment query take today? Show us a live example.",
   "What traceability do customers or contracts require (and where is that written)?"]),
  ("Automation and performance", [
   "Which steps are fully automated (auto-completes, auto-labeling, auto-transactions, equipment integrations)?",
   "What integrations touch machines/test equipment/printers? Who built and maintains them?",
   "How fast is the system on the floor? Any known slowdowns? Peak concurrent users?",
   "Where is it brittle – what breaks, who fixes it, and how long does it take?"])])

S["1.4"] = ("GWTrack Demo II – Quality, Labor & Inventory", "Mon 10/19 · 1:15 – 3:15", "Quality lead, supervisors, inventory/materials [[TBC]]",
 "Compare directly to Irvine's practice (SharePoint QMS + manual RMA/rework/scrap tracking). The question for the readout is: what is the minimum quality capability that must exist in whichever system is chosen, and what else is nice to have.",
 [("Quality tracking", [
   "Show us how a defect is captured on the floor – who enters it, what fields, what codes? Where do the defect heatmaps come from and who uses them?",
   "How are NCRs, containment, rework and scrap dispositioned and costed? Is any of that integrated to inventory/NetSuite?",
   "How are inspections / in-process checks / test results recorded? Pass/fail enforcement before moving on?",
   "Where do CAPA / 8D / corrective action live – GWTrack, Arena, spreadsheets, paper?",
   "What would the customer or an auditor ask to see, and how long does it take to produce?"]),
  ("RMA and returns", [
   "How are customer returns/RMAs received, tracked, repaired/reworked and reported on?",
   "How does returned product get traced back to the original build record?"]),
  ("Labor and timekeeping", [
   "How is labor captured – per operation, per job, per shift? Clock-in/out vs. job-level time?",
   "Who uses labor data (efficiency, standard cost, payroll) and how does it flow to NetSuite / payroll?",
   "What gaps or disputes occur with labor data today? (Compare: Irvine MM timekeeping gaps.)"]),
  ("Inventory and costing touchpoints", [
   "What inventory transactions does GWTrack post to NetSuite, and how often? Any reconciliation pain?",
   "How is standard/actual cost handled for WIP and finished goods? Who owns variances?",
   "What month-end steps depend on GWTrack data (WIP, scrap, labor, variances)?"])])

S["1.5"] = ("Day 1 Wrap-up & Open Items", "Mon 10/19 · 3:30 – 4:30", "David, John, site leadership [[TBC]]",
 "Internal Crowe debrief right after (15 min): update the tracker, tag open questions by owner, and send Sohaa the end-of-day note. NOTE: if any ITAR/CUI concern is raised, stop and confirm what may be shared with non-US Crowe personnel before sending notes.",
 [("Loose ends", [
   "What did we not get to see that we need to?", "Which documents/screens should we collect (and which can't leave the site)?",
   "Who else should join Day 2?"])])

S["2.1"] = ("Systems Landscape & Integrations", "Tue 10/20 · 8:00 – 10:00", "IT/NetSuite admin, GWTrack admin, engineering (Arena) [[TBC]]",
 "Goal: a validated current-state application map for Gateworks (see Application inventory table at the end of this guide). Client update: rationalize the functions GWTrack provides across NetSuite and Arena – so for every function ask 'which system is the system of record, and which should be?' Grant is out Tue 10/20 – Rohit leads technical questions.",
 [("System of record by function", [
   "Take each capability – item master, BOM, routing, ECO/revision control, work orders, inventory, costing, quality, labor, document control, traceability, shipping – and tell us where it lives today: GWTrack, NetSuite, Arena, spreadsheets or other.",
   "Where does the same data exist in more than one place? Who reconciles and how often?",
   "What is Arena used for at Gateworks (PLM / BOM / change control / QMS)? Is it integrated to GWTrack or NetSuite?"]),
  ("Integrations and data flows", [
   "Walk the flow of an item/BOM change from engineering through to the floor. How many hand-offs? Any manual re-keying?",
   "What integrations/scripts/scheduled jobs exist between GWTrack, NetSuite and Arena? Who built/maintains each and is it documented?",
   "What would break if GWTrack were turned off tomorrow? What is business-critical?"]),
  ("Platform and ownership", [
   "How is GWTrack hosted and supported? Who built it, who maintains it now, and what is the key-person risk?",
   "What is the NetSuite footprint at Gateworks today (subsidiary/location, modules, SuiteApps)?",
   "What master data (items, customers, vendors) is shared vs. separate between Gateworks and the existing Ezurio NetSuite?"]),
  ("Reporting", [
   "Top reports/dashboards the business uses daily/weekly – where do they come from and who builds them?",
   "What can't be reported today that you wish you could?"])])

S["2.2"] = ("Compliance, Security & Data Requirements", "Tue 10/20 · 10:15 – 12:00", "Compliance/contracts lead, IT security [[TBC]]",
 "Crowe does not give legal advice – we are capturing requirements and who owns the answers. Establish early: which data/screens are ITAR- or CUI-controlled and which Crowe personnel may access them. The EL resource plan includes offshore/international staff and the Crowe NetSuite Y-Hire team is dialing in on Day 3 – do not share GWTrack data, screenshots or recordings with non-US persons until Ezurio compliance confirms in writing what is permitted. Keep SLO notes in the engagement's controlled storage.",
 [("ITAR / CUI scope", [
   "Which programs/customers/contracts carry ITAR or CUI obligations? Which products or data sets are in scope?",
   "Is the ITAR/CUI scope all of Gateworks or specific lines/areas? Today, how are controlled records segregated?",
   "Who is the empowered person (Empowered Official / FSO / compliance lead) we should route questions to?",
   "Are there DFARS / NIST 800-171 / CMMC requirements flowed down by customers? Current assessment status?"]),
  ("What that means for systems", [
   "Hosting/location requirements – US-only data residency? US-person-only administration/support?",
   "Does the current GWTrack/NetSuite setup restrict access by person or nationality? Who administers and from where?",
   "Could ITAR alone require Gateworks' data to stay in a separate instance/environment? Has that been discussed?",
   "NOTE: The Aug assessment flagged that confirmed ITAR requirements could be reason enough for Gateworks to stay a separate environment. Gather facts only; do not opine."]),
  ("Security, access, audit", [
   "User roles and segregation of duties on the floor and in the office – how managed?",
   "Audit trail expectations: electronic records, signatures, change history, retention periods.",
   "Customer audits (AS9100/ISO/quality system audits): what records must the system produce and how fast?"])])

S["2.3"] = ("Capabilities to Keep: Automation & Performance", "Tue 10/20 · 12:45 – 2:45", "David, John, site leadership, power users [[TBC]]",
 "This is the highest-value session for the next-phase scoping. Build a 'must not lose' list and score every capability seen in 1.3/1.4 by importance and by how hard it is to replicate. Run the capture live on a shared screen (tracker tab 2). Frame as 'what would it take' – never imply a decision has been made.",
 [("Must-not-lose list", [
   "From what we saw yesterday, which capabilities are the reason the floor runs well? Rank the top 10.",
   "For each: what happens if it disappears – slower, more errors, compliance risk, customer impact?",
   "Which automation is 'nice' vs. which one you could not run the business without?"]),
  ("Performance expectations", [
   "Transaction speed: how fast must a scan/complete/transaction respond at the station? What is unacceptable?",
   "Peak load: users, transactions per hour, lines running at once?",
   "Offline/degraded operation: what happens when the network or ERP is down?"]),
  ("MES objectives for the next phase", [
   "What is the MES/shop-floor objective list (Jason's objectives)? Walk through each and what 'done' looks like.",
   "Which objectives are about Gateworks only vs. a solution that could be used at other Ezurio sites?",
   "What would a third-party MES / SuiteApp need to do on day one vs. later?",
   "NOTE: Frame multi-site only as 'could this scale to other Ezurio entities' – no site-specific plans."]),
  ("Scalability and change", [
   "What was GWTrack not built to do that you'd need next (more users, more entities, more product lines)?",
   "What is the appetite for process change vs. replicating exactly what exists?"])])

S["2.4"] = ("Requirements Read-back & Prioritization", "Tue 10/20 · 3:00 – 4:30", "David, John, site leadership [[TBC]]",
 "Read back every requirement captured in the tracker; get explicit Must/Should/Could on each. Where there's disagreement, capture both views. End by agreeing the follow-up list and owners. The team travels to Irvine that evening.",
 [("Read-back", [
   "Read the requirement list by area – did we capture it correctly? Anything missing?",
   "Assign Must / Should / Could (MoSCoW) with the reason."]),
  ("Open items", [
   "What are we still unsure about and who can answer by when?",
   "What documents will be sent and when (see data request)?",
   "What does Ezurio want in the readout – level of detail, audience, format?"])])

S["3.1"] = ("Kickoff & Goals for Irvine", "Wed 10/21 · 8:00 – 8:30", "David, John, Irvine ops leadership [[TBC]]",
 "Irvine went live on NetSuite WMS + Manufacturing Mobile in July 2025 (MFG optimization UAT June 2025). Open by asking what has changed since – we haven't seen the floor since go-live. Hana/Kyle (Y-Hire) dial in from 10:15; confirm availability given India working hours.",
 [("Where things stand", [
   "What has changed since the July 2025 go-live – volumes, products, headcount, process?",
   "What are the top 3 things frustrating the floor or the back office right now?",
   "What's already on the improvement backlog (Azure DevOps) and what is stuck or deprioritized?"]),
  ("Goals", [
   "What would a great outcome from today look like for each of you?",
   "Which Irvine processes are you comfortable with being a baseline for other sites, and which aren't?"])])

S["3.2"] = ("Floor Walk & Live Process Observation", "Wed 10/21 · 8:30 – 10:00", "Warehouse operators/manager, QC, production operators [[TBC]]",
 "Use the annotated Irvine process flow (04_Irvine_Process_Flow_Annotated.png) as the spine. Watch a real WO if one is staged. Validate each step against the Visio (July 2025) and the process outlines (QC does Transfer All + WO Issue per 2025 docs; the Visio shows the Material Handler lane – confirm who actually does it).",
 [("Allocation, pick and stage", [
   "Walk a work order from creation: component allocation – how often are lines not fully committed? How are 'Special Order' lines reallocated?",
   "Pick in the WMS app: how often are partial picks needed and what happens (task closes → reverse pick)? Any workarounds?",
   "Staging: one WO per bin – is that being followed? What happens when staging bins are full?",
   "Staged Work Orders report and Actual vs. Expected pick review – who runs them, when, and what gets corrected?"]),
  ("Transfer, issue, production", [
   "Transfer to the production input bin: who performs 'Transfer All', and how long does it take?",
   "Create Work Order Issue + verify default inventory detail bin: who, where, and how often does it error? (Visio vs. QC-owned discrepancy.)",
   "Production in Manufacturing Mobile: show badge-in, scanning the WO, pause/end, completions by operation.",
   "Physically marking bins as Issued / Staged / Prod Input – is the physical marking reliable?"]),
  ("Finish and move", [
   "Completed assembly to Lab Input or back to warehouse – who decides and how is it recorded?",
   "Lab/test work order for programmed boards – walk the 'Testing Work Order' flow.",
   "NOTE: Auto-Mark WOs Built workflow was suspended 10/1 (failed on WO 2447441 – BOM not defined for assembly item). Ask how WOs are being closed/marked built now and who decided to turn it off."])])

S["3.3"] = ("Manufacturing Mobile: Process Controls & Timekeeping", "Wed 10/21 · 10:15 – 12:00", "Production manager, planner, cost accounting, QC lead [[TBC]] + Y-Hire team (dial-in)",
 "From the Aug assessment: Manufacturing Mobile has no control that prevents a run from starting without sufficient component material or an assigned standard cost, and has timekeeping gaps. Get specifics: how often it happens, what it costs, and what a control would need to do. Crowe Y-Hire team dials in – OK for Irvine content (no ITAR/CUI).",
 [("Material availability control", [
   "How often does a run start without all components? What is the impact (stoppage, expedite, scrap, cost errors)?",
   "What does a 'good' control look like – hard stop, warning, or supervisor override? Who can override?",
   "How are shortages visible to production before the WO is released/started?"]),
  ("Standard cost enforcement", [
   "How often are items missing a standard cost at the time of production? Who maintains standard cost and when?",
   "What happens in the books when a WO is built without a standard cost? How are variances found/corrected?",
   "Which cost roll-up/revaluation steps are manual today?"]),
  ("Timekeeping", [
   "Operators badge in and record time per operation – what's working and what's missing (breaks, rework time, indirect labor, multi-operator jobs)?",
   "Walk through pause vs. end time; partial quantities not exceeding the prior step – where do users get stuck?",
   "What does the business need from labor data – efficiency, costing, payroll hand-off, customer quoting?",
   "What requirements exist that Manufacturing Mobile can't meet today (the 'Ezurio requirements' for timekeeping)?"]),
  ("Fit for other sites", [
   "Which of these gaps would you also expect at any site running Manufacturing Mobile?"])])

S["3.4"] = ("Quality, Rework/RMA/Scrap & Post-Production Reconciliation", "Wed 10/21 · 12:45 – 2:00", "QC lead, warehouse manager, production manager [[TBC]]",
 "Compare with the Gateworks answers from 1.4 – same questions, different tools. Capture what the SharePoint QMS holds vs. what is manual spreadsheet. Dekit reconciliation (Actual vs. Expected, IA for scrap, bin transfer for return) is template/import-driven – quantify the effort.",
 [("Quality tracking", [
   "How is a defect or nonconformance recorded today (SharePoint QMS form, spreadsheet, paper)? Who looks at it and when?",
   "How are rework, scrap and RMA recorded and costed? How do they tie back to the work order or lot?",
   "What quality reports are produced? Anything like a defect heatmap that you wish existed?"]),
  ("De-kit and reconciliation", [
   "After production, how are leftover/issued components reconciled – the Prod Dekit and CM Dekit templates? How long per WO / per week?",
   "How often do adjustments go through the 4250 Variances account? Who reviews the Overage/Excess report?",
   "Where does inventory accuracy break down and how do you find out?"]),
  ("Contract manufacturer receipts", [
   "How are CM receipts and component reconciliation handled? Pain points?"])])

S["3.5"] = ("Optimization Workshop & Backlog", "Wed 10/21 · 2:15 – 3:45", "Irvine leads [[TBC]] + Y-Hire (as available)",
 "Working session: sort everything heard so far into the Optimization Backlog (tracker tab 4) with a quick value/effort score, then propose what goes into the Azure DevOps backlog vs. what feeds the future-state recommendation. Pull the existing ADO backlog first (see ADO note) to avoid duplicates.",
 [("Ideas and quick wins", [
   "Which 3 fixes would make the biggest difference to the floor in the next 90 days?",
   "Which ideas are config/saved-search/report changes vs. customization vs. process change?",
   "What should be stopped being done manually?"]),
  ("Prioritization", [
   "Rank by value and effort; who owns each? Dependencies on the future-state systems decision?",
   "Which items should wait for a bigger decision rather than be built now?"])])

S["3.6"] = ("Week Wrap-up & Next Steps", "Wed 10/21 · 3:45 – 4:30", "David, John [[TBC]]",
 "Recap, confirm what the readout will contain and timing. Note: Jordan is on PTO Oct 23 – Nov 2; confirm who distributes the draft if it is ready before then (Grant/Rohit).",
 [("Recap and next steps", [
   "Play back top observations from Gateworks and Irvine – does that match your read?",
   "Open items and owners; when will pending documents arrive?",
   "Readout: audience, format, and date; any decisions that need to happen first?"])])

APPS = [
 ("GWTrack", "Gateworks shop-floor / MES / quality system", "Work execution, traceability, quality (defect heatmaps), labor, material at the floor", "Hosting, vendor/builder, support, extensibility, ITAR/CUI controls?"),
 ("NetSuite (Ezurio)", "ERP", "Items, BOM, WO, inventory, costing, financials; Irvine WMS + Manufacturing Mobile", "Is Gateworks in this instance/subsidiary? What flows from GWTrack?"),
 ("Arena", "Engineering/PLM (to confirm)", "BOM/change control; possibly quality/doc control", "What does it hold for Gateworks vs. Irvine? Integrated to anything?"),
 ("Manufacturing Mobile (MM)", "NetSuite SuiteApp – Irvine shop floor", "Operator time/completions, operation tracking", "Known gaps: material availability control, standard cost enforcement, timekeeping"),
 ("WMS app (NetSuite)", "Irvine warehouse – pick, stage, transfer", "WO picking by committed qty; bin transfers", "Partial-pick / reverse-pick behavior; staging process"),
 ("SharePoint QMS", "Irvine quality records", "Quality forms/logs; manual RMA, rework, scrap tracking", "Volume, ownership, link to WO/lot?"),
 ("Saved searches / templates", "Irvine reporting", "Open WO Pick Tasks, Staged Work Orders, Actual vs. Expected, Overage/Excess, Dekit templates", "Which are heavily used? Who maintains?"),
 ("Auto-Mark WOs Built workflow", "NetSuite workflow (Crowe-built)", "Marks WOs built automatically", "Suspended Oct 1; last error: BOM not defined for assembly item"),
 ("Azure DevOps (Crowe)", "Ezurio improvement backlog", "Work items for Irvine optimizations", "Pull current backlog before 3.5 (needs ADO access)"),
]
