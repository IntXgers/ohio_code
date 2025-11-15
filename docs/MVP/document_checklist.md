# Legal Data Coverage - AI-Powered Citation Graph Platform

## 🎯 Ship-Ready Status: 80% Complete for MVP

**What makes this different:** Citation graph architecture - trace legal reasoning chains across statutes, regulations, and case law. Westlaw shows you documents; we show you how they connect.

---

## TIER 1: SHIP WITH THIS (Month 1) ⚡

### ✅ COMPLETE - Ready to Ship (4 corpuses)
```
✅ Ohio Revised Code (ORC) - 23,644 sections with citation graphs
✅ Ohio Administrative Code (OAC) - State regulations
✅ Ohio Constitution - Foundational law
✅ Ohio Case Law - 22,245 cases from all reporters
```

### 🚧 IN PROGRESS - Complete Before Launch (3 corpuses)
```
⏳ U.S. Code (USC) - Federal statutes (Ohio law cites these constantly)
⏳ U.S. Supreme Court Cases - Binding precedent (~35k cases)
⏳ 6th Circuit Court of Appeals - Ohio appeals go here (~80k cases)
```

**Why these 7 corpuses = viable product:**
- Core Ohio law with complete citation graphs ✅
- Federal law that Ohio constantly references
- Creates 35 LMDB databases (5 per corpus × 7)
- Enables AI agents to trace legal reasoning chains
- Competitive moat: Citation graphs, not just document retrieval

**Total when complete: 7 corpuses = 35 LMDB databases**

---

## OHIO STATE LAW (Current Coverage)
### Ohio Court Rules
```
❓ Ohio Rules of Civil Procedure (Civ.R. 1-86)
❓ Ohio Rules of Criminal Procedure (Crim.R. 1-57)
❓ Ohio Rules of Appellate Procedure (App.R. 1-47)
❓ Ohio Rules of Juvenile Procedure (Juv.R. 1-48)
❓ Ohio Rules of Evidence (Evid.R. 101-1103)
❓ Ohio Traffic Rules (Traf.R. 1-25)
❓ Ohio Rules of Superintendence (Sup.R. 1-99) - Court administration
❓ Ohio Rules for the Government of the Bar
❓ Ohio Rules for the Government of the Judiciary
❓ Ohio Supreme Court Rules of Practice
❓ Local Court Rules (each county/court has its own)
```
### Specialty Court Rules
```
❓ Ohio Rules of Practice of the Court of Claims
❓ Ohio Magistrate Rules
❓ Ohio Rules for Electronic Filing
❓ Uniform Domestic Relations Forms
❓ Uniform Juvenile Court Forms
❓ Probate Court Rules (varies by county)
```
### Administrative/Agency Materials
```
❌ Ohio Attorney General Opinions
❌ Ohio Board of Tax Appeals Decisions
❌ Ohio Industrial Commission Decisions
❌ Ohio Civil Rights Commission Decisions
❌ Ohio Public Utilities Commission Orders
❌ Ohio Environmental Review Appeals Commission
```
### Legislative Materials
```
❌ Ohio Bill Status & Tracking
❌ Ohio Legislative Service Commission Analysis
❌ Ohio Committee Reports
```
### FEDERAL LAW
#### Primary Law
```
❌ U.S. Constitution
❌ U.S. Code (USC) - Federal statutes (53 titles)
❌ Code of Federal Regulations (CFR) - Federal regulations
❌ Federal Case Law:

❌ U.S. Supreme Court (~35k cases)
❌ 6th Circuit Court of Appeals (~80k cases)
❌ All Circuit Courts (~500k cases)
❌ N.D. Ohio District Court
❌ S.D. Ohio District Court
❌ All District Courts (~400k cases)
```
### Federal Court Rules
```
❌ Federal Rules of Civil Procedure (FRCP)
❌ Federal Rules of Criminal Procedure (FRCrP)
❌ Federal Rules of Appellate Procedure (FRAP)
❌ Federal Rules of Evidence (FRE)
❌ Federal Rules of Bankruptcy Procedure
❌ Supreme Court Rules
❌ 6th Circuit Local Rules
❌ N.D. Ohio Local Rules
❌ S.D. Ohio Local Rules
```
### Federal Administrative
```
❌ Presidential Executive Orders
❌ Federal Agency Decisions:

❌ NLRB (National Labor Relations Board)
❌ SEC (Securities & Exchange Commission)
❌ FTC (Federal Trade Commission)
❌ EPA Administrative Decisions
❌ EEOC Decisions
❌ SSA (Social Security) Decisions
❌ DOL (Department of Labor) Decisions
❌ IRS Revenue Rulings & Procedures
❌ Patent & Trademark decisions
```
### SPECIALIZED COURT SYSTEMS
#### Ohio Specialty Courts
```
❓ Common Pleas Court Rules (general jurisdiction)
❓ Municipal Court Rules (varies by city)
❓ County Court Rules
❓ Mayor's Court Rules (varies by municipality)
❓ Probate Court - Guardianship Forms
❓ Probate Court - Estate Administration Forms
❓ Domestic Relations Court Forms
❓ Juvenile Court - Delinquency Forms
❓ Juvenile Court - Dependency Forms
```
### Federal Specialty Courts
```
❌ Bankruptcy Court Rules & Forms
❌ Tax Court Rules
❌ Court of International Trade
❌ Court of Federal Claims
❌ Veterans Appeals Court
```
### PRACTICE-AREA SPECIFIC
#### Family Law
```
❓ Ohio Uniform Domestic Relations Forms
❓ Child Support Guidelines & Worksheets
❓ Parenting Time/Visitation Schedules
❓ Ohio Marriage Laws & Forms
❓ Ohio Dissolution/Divorce Forms
```
### Criminal Law
```
❓ Ohio Sentencing Guidelines
❓ Ohio Criminal Jury Instructions
❓ Ohio Bail Schedules (by county)
```
### Probate/Estate
```
❓ Ohio Probate Forms
❓ Will/Trust Templates (if public domain)
❓ Power of Attorney Forms
❓ Living Will/Healthcare Directive Forms
```
### Business/Corporate
```
❌ Ohio Secretary of State Business Forms
❌ Ohio LLC Operating Agreement Guidelines
❌ Ohio Corporate Documents Requirements
```
### Real Estate
```
❌ Ohio Conveyance Forms
❌ Ohio Title Standards
❌ Ohio Landlord-Tenant Forms
```
### REFERENCE MATERIALS
#### Model Codes & Restatements (Copyrighted - Cannot Scrape)
```
❌ Restatements (Contracts, Torts, Property, etc.)
❌ Uniform Commercial Code (UCC) Official Text
❌ Model Penal Code
❌ Uniform Probate Code
```
### Court Forms & Instructions
```
❓ Supreme Court of Ohio Standard Forms
❓ Self-Help Legal Forms (public domain)
❓ Pro Se Litigant Guides
```
### Jury Instructions
```
❌ Ohio Jury Instructions - Civil
❌ Ohio Jury Instructions - Criminal
❌ Federal Jury Instructions
```
---

## TIER 2: ADD POST-LAUNCH (Month 3+) 🔸

**Wait for attorney feedback before building these.**

### Court Rules (Procedural - Not Citation-Heavy)
```
⏸️ Ohio Rules of Civil Procedure (Civ.R. 1-86)
⏸️ Ohio Rules of Criminal Procedure (Crim.R. 1-57)
⏸️ Ohio Rules of Evidence (Evid.R. 101-1103)
⏸️ Federal Rules of Civil Procedure (FRCP)
⏸️ Federal Rules of Criminal Procedure (FRCrP)
⏸️ Federal Rules of Evidence (FRE)
```

**Why wait:**
- Attorneys memorize these or use cheat sheets
- Not citation-heavy (won't benefit from graph architecture)
- Procedural reference, not substantive law
- Add only if attorneys specifically request

### Federal Regulations
```
⏸️ Code of Federal Regulations (CFR)
```

**Why wait:**
- Less critical than US Code (statutes cite each other more than regulations)
- Large corpus, lower ROI
- Wait until attorneys ask

### Agency Opinions/Decisions (Non-Binding)
```
⏸️ Ohio Attorney General Opinions
⏸️ Ohio Board of Tax Appeals Decisions
⏸️ Ohio Industrial Commission Decisions
⏸️ Federal Agency Decisions (NLRB, SEC, FTC, EPA, EEOC, etc.)
```

**Why wait:**
- Not binding law (persuasive only)
- Nice-to-have for specific practice areas
- Add when you have revenue to justify the work

---

## TIER 3: DIFFERENT PRODUCT CATEGORY 🔹

**These are document automation, not legal research. Skip for now.**

### Forms & Templates
```
🚫 Ohio Uniform Domestic Relations Forms
🚫 Ohio Probate Forms
🚫 Ohio Business/Corporate Forms
🚫 Federal Court Forms
🚫 Self-Help Legal Forms
```

**Why skip:**
- This is document assembly, not citation-based research
- Different product entirely
- Doesn't leverage your citation graph architecture

### Jury Instructions
```
🚫 Ohio Jury Instructions - Civil (copyrighted)
🚫 Ohio Jury Instructions - Criminal (copyrighted)
🚫 Federal Jury Instructions (copyrighted)
```

**Why skip:**
- Copyrighted by bar associations
- Can't legally scrape
- Not feasible

### Legislative History
```
🚫 Ohio Bill Status & Tracking
🚫 Ohio Legislative Service Commission Analysis
🚫 Ohio Committee Reports
```

**Why skip:**
- Only matters for statutory interpretation disputes
- Niche use case
- Complex data sources
- Wait until attorneys ask

---

## TIER 4: OUT OF SCOPE 💎

**Don't even consider these until you have market validation.**

```
🚫 All Circuit Courts (~500k cases)
🚫 All District Courts (~400k cases)
🚫 Model Codes & Restatements (copyrighted)
🚫 Ohio title standards
🚫 Specialty court systems (Tax Court, Veterans Appeals, etc.)
```

**Why out of scope:**
- Massive data volume with unclear ROI
- Not specific to Ohio
- Let attorneys tell you if they need these

---

## 🎯 THE AGENT-FIRST TEST

**Ask: "Will an AI agent doing legal research NEED this to trace citation chains and build legal arguments?"**

| Data Source | Agent Needs It? | Why/Why Not |
|-------------|-----------------|-------------|
| ORC/OAC/Constitution/Case Law | ✅ YES | Core Ohio law |
| US Code/SCOTUS/6th Circuit | ✅ YES | Ohio law constantly cites federal |
| Court Rules | ❌ NO | Procedural reference, not citation-heavy |
| Forms/Templates | ❌ NO | Different product (document assembly) |
| Agency Opinions | ⚠️ MAYBE | Not binding law, add later if requested |
| Jury Instructions | ❌ NO | Copyrighted, can't scrape |
| Legislative History | ❌ NO | Niche use case, wait for demand |

---

## 📅 3-MONTH ROADMAP

### Month 1: Ship What You Have
- **Status:** 80% ready
- **Action:** Complete Ohio data (4 corpuses = 20 LMDB databases)
- **Deploy:** Get paying attorneys using it
- **Outcome:** Validate product-market fit

### Month 2: Add Federal Core
- **Action:** US Code + SCOTUS + 6th Circuit (3 corpuses = 15 LMDB databases)
- **Total:** 7 corpuses = 35 LMDB databases
- **Outcome:** Complete citation graph for Ohio + binding federal law

### Month 3: Collect Feedback
- **Action:** Let attorneys tell you what's missing
- **Prioritize:** Based on actual usage patterns
- **Outcome:** Data-driven roadmap for Tier 2

**Don't build Westlaw. Build what agents need that Westlaw CAN'T provide.**

Your competitive moat is the citation graph, not document volume.

---
### Download Sources
###### Confirmed Sources:
 - Ohio Case Law: ✅ case.law (done)
- Ohio Statutes/Admin/Constitution: ✅ (you have)
- Ohio Court Rules: supremecourt.ohio.gov
- Federal Cases: courtlistener.com
- U.S. Code: github.com/usgpo/uscode
- CFR: ecfr.gov
- Federal Rules: uscourts.gov
###### Unknown Sources (Need Research):
- Ohio AG Opinions
- Ohio agency decisions
- Ohio local court rules
- Federal agency decisions