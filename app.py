"""
HealthMate v3 — Multi-Intent Clinical AI
=========================================
Handles 8 question types with correct intake flow per type.
Deploy: streamlit run app.py
"""
import os, json, streamlit as st

st.set_page_config(page_title="HealthMate",page_icon="🏥",layout="centered",initial_sidebar_state="collapsed")
st.markdown("""<style>
.stApp{background:#F8FAFC}
#MainMenu{visibility:hidden}footer{visibility:hidden}
.hm-header{background:linear-gradient(135deg,#0D47A1,#1565C0);padding:1.4rem 2rem 1.1rem;border-radius:12px;margin-bottom:1rem;text-align:center}
.hm-header h1{color:white;font-size:1.9rem;font-weight:800;margin:0}
.hm-header p{color:#90CAF9;font-size:0.88rem;margin:.3rem 0 0}
.ibadge{display:inline-block;padding:3px 12px;border-radius:20px;font-size:.8rem;font-weight:600;margin-bottom:.4rem}
.ig{background:#E8F5E9;color:#1B5E20}.iy{background:#FFF8E1;color:#E65100}
.ir{background:#FFEBEE;color:#B71C1C}.ib{background:#E3F2FD;color:#0D47A1}
.ip{background:#F3E5F5;color:#4A148C}.it{background:#E0F2F1;color:#004D40}
.pbar{background:#E3F2FD;border-radius:8px;padding:.4rem 1rem;margin:.4rem 0;font-size:.83rem;color:#1565C0}
.disc{background:#F5F5F5;border-radius:6px;padding:.55rem .9rem;font-size:.76rem;color:#757575;margin-top:.8rem}
</style>""",unsafe_allow_html=True)

# ── GUIDELINES ──────────────────────────────────────────────────────
GL = {
"uti":"""IDSA UTI Guidelines 2022:
- Uncomplicated cystitis: dysuria, frequency, urgency — no fever, no flank pain
- OTC ONLY: Phenazopyridine (AZO Standard) 200mg 3x daily WITH food, max 2 days. Turns urine orange.
- Antibiotic required — prescription only
- Pyelonephritis RED FLAGS: fever >100.4F, flank pain → ER immediately
- Pregnancy: ANY urinary symptoms → physician same day, NO OTC""",

"skin":"""AAD Guidelines 2024:
- Contact/atopic dermatitis: remove trigger, moisturize, topical corticosteroid
- Hydrocortisone 1% OTC: thin layer 2-4x daily, max 7d face, max 14d body
- Infection signs → physician TODAY: crusting, honey exudate, fever, spreading redness
- ABCDE mole rule: Asymmetry, Border, Color variation, Diameter >6mm, Evolving → derm referral
- Moisturizers: CeraVe, Cetaphil within 3min of bathing""",

"respiratory":"""CDC+IDSA Respiratory 2024:
- Viral URI: self-limiting 7-10d, NO antibiotics
- OTC fever/pain: Ibuprofen 200-400mg every 6-8h with food OR Acetaminophen 500-1000mg every 6h
- OTC congestion: Pseudoephedrine 30mg every 4-6h (pharmacy counter, ID required)
- OTC sore throat: Benzocaine lozenges, saltwater gargle, honey (adults only)
- Centor strep: fever + exudate + tender nodes + no cough = test for strep
- RED FLAGS → ER: stridor, drooling, muffled voice, can't open mouth""",

"back":"""ACP Low Back Pain 2022:
- Acute (<4wks): conservative, 90% resolves in 4-6wks
- OTC: Ibuprofen 400-600mg every 6-8h with food (max 1200mg/day OTC, max 10d)
- Heat therapy: 20min 3x daily for muscle spasm
- Stay active — bed rest worsens outcomes
- Cauda equina → 911: bladder/bowel incontinence + back pain
- → physician same day: leg weakness, foot drop, progressive numbness""",

"ankle":"""APTA Ankle Sprain 2021 + Ottawa Rules:
- Ottawa: X-ray if bone tenderness at fibula/tibia tip OR can't bear weight 4 steps
- PRICE: Protection, Rest, Ice 15-20min (not on skin), Compression, Elevation
- OTC: Ibuprofen 400mg every 6-8h with food, max 1200mg/day, max 10d
- Physician if: can't bear weight after 48h, no improvement at 5d, instability""",

"heartburn":"""ACG/AGA GERD 2022:
- Lifestyle: elevate head of bed, no food 3h before bed, reduce caffeine/alcohol/fatty food
- OTC antacids: Tums 500-1000mg as needed, max 3000mg/day
- OTC H2: Famotidine (Pepcid AC) 10-20mg once or twice daily
- OTC PPI: Omeprazole (Prilosec OTC) 20mg once daily BEFORE breakfast, 14d course
- RED FLAGS → physician: difficulty swallowing, weight loss, vomiting blood, new onset >50yo""",

"gi":"""AGA/ACG + FDA DailyMed:
- Gastroenteritis: oral rehydration, BRAT diet, self-limiting 1-3d
- OTC diarrhea: Loperamide (Imodium) 4mg then 2mg per loose stool, max 16mg/day, max 2d
- OTC nausea: Bismuth subsalicylate (Pepto-Bismol) 524mg every 30-60min, max 8 doses/day
- Rehydration: Pedialyte, diluted sports drink, clear broths
- RED FLAGS → ER: blood in stool, black/tarry stool, severe abdominal pain with fever""",

"pediatric":"""AAP Fever 2021:
- Age <3 months ANY fever ≥38.0C: EMERGENCY — ER immediately, NO exceptions
- Age 3-6 months fever ≥38.0C: physician same day
- Age >6 months well-appearing: may manage at home with weight-based dosing
- Acetaminophen (Infant Tylenol 160mg/5mL): 15mg/kg per dose, every 4-6h, max 5 doses/24h
- Ibuprofen (age ≥6mo ONLY): 10mg/kg per dose, every 6-8h
- NEVER give aspirin to children — Reye syndrome""",

"mental_health":"""USPSTF Depression 2023 + SAMHSA:
- PHQ-9: 5-9 mild, 10-14 moderate, 15+ severe
- GAD-7: 5-9 mild, 10-14 moderate, ≥15 severe
- Mild only (PHQ-9 <5): exercise 150min/week, sleep hygiene, mindfulness apps
- Moderate+: physician or therapist evaluation
- ANY suicidal thoughts: 988 Lifeline — call or text 988 immediately
- Crisis Text Line: text HOME to 741741""",

"medication":"""FDA DailyMed OTC Drugs:
- Ibuprofen: 200-400mg every 6-8h WITH food, max 1200mg/day OTC, max 10d. Avoid: kidney disease, GI ulcer, blood thinners.
- Acetaminophen: 325-650mg every 4-6h, max 3000mg/day. Risk: liver damage with alcohol.
- Diphenhydramine (Benadryl): 25-50mg every 4-6h, max 300mg/day. Drowsy. Avoid in elderly, glaucoma, BPH.
- Loratadine (Claritin): 10mg once daily. Non-drowsy. Safe in most patients.
- Pseudoephedrine (Sudafed): 30mg every 4-6h, max 240mg/day. Avoid if hypertension.
- Omeprazole (Prilosec OTC): 20mg once daily before breakfast, 14d max, 1 course per 4 months.
- Loperamide (Imodium): 4mg then 2mg per loose stool, max 16mg/day, max 2d.
- Phenazopyridine (AZO): 200mg 3x daily with food, max 2d. Avoid if kidney disease.""",

"preventive":"""USPSTF Grade A/B Recommendations + CDC Vaccines:
CANCER: Cervical cancer Pap smear 3yr (21-65) or Pap+HPV 5yr (30-65). Colorectal colonoscopy 10yr (45-75). Breast mammogram 2yr (women 40-74). Lung cancer annual low-dose CT (50-80, 20 pack-year history).
BP: Every year all adults ≥18. Diabetes screen: every 3yr (35-70, overweight). Cholesterol: cardiovascular risk assessment 40-75yo.
VACCINES: Influenza annually. Tdap once then Td every 10yr. Shingrix 2 doses age ≥50. PCV20 age ≥65 or high-risk.""",

"hypertension":"""AHA/ACC Hypertension 2023:
- Normal: <120/<80. Elevated: 120-129/<80 → lifestyle. Stage 1: 130-139/80-89 → lifestyle+consider med. Stage 2: ≥140/≥90 → lifestyle+medication
- Hypertensive urgency: >180/>120 no symptoms → physician SAME DAY
- Hypertensive emergency: >180/>120 WITH symptoms (chest pain, SOB, headache) → 911
- DASH diet, sodium <2300mg/day, aerobic 150min/week, limit alcohol, no smoking""",

"diabetes":"""ADA Standards 2024:
- HbA1c target: <7.0% most adults, <8.0% elderly/complex
- Fasting glucose: 80-130 mg/dL. Post-meal 2h: <180 mg/dL
- BP target: <130/80. LDL: <100 (high risk <70)
- Foot care: daily inspection, annual exam, never barefoot
- Hypoglycemia <70mg/dL: 15g fast carbs (4oz juice, 3-4 glucose tabs), recheck 15min""",

"asthma":"""GINA Asthma 2023:
- Well controlled: symptoms ≤2x/wk, no nighttime waking, reliever ≤2x/wk
- Rescue inhaler (albuterol): 2 puffs every 4-6h as needed — NOT daily use
- >2x/wk rescue use: see physician — step-up needed
- RED FLAGS → 911: severe breathlessness, no relief from rescue inhaler, lips/nails turning blue""",

"lab_results":"""Common Lab Reference Ranges:
CBC: Hemoglobin men 13.5-17.5, women 12.0-15.5 g/dL. WBC 4,500-11,000/μL. Platelets 150,000-400,000/μL.
METABOLIC: Glucose fasting 70-99mg/dL (100-125=prediabetes, ≥126=diabetes). HbA1c <5.7% normal, 5.7-6.4% prediabetes, ≥6.5% diabetes. Creatinine men 0.74-1.35, women 0.59-1.04 mg/dL. eGFR ≥60 normal.
CHOLESTEROL: Total <200 desirable. LDL <100 optimal, ≥160 high. HDL >60 protective, <40(men)/<50(women) low. Triglycerides <150 normal.
THYROID: TSH 0.4-4.0 mIU/L. Free T4 0.8-1.8 ng/dL.""",

"routing":"""HealthMate Care Routing:
911/ER: Chest pain+SOB. Stroke (FAST). Throat swelling. Unconscious. Seizure >5min. Severe bleeding. Suspected spinal injury. Infant fever <3mo. Cauda equina.
URGENT CARE: Fever >103F well-appearing. UTI uncomplicated. Ear/sinus infection. Minor cuts needing stitches. Sprains/minor fractures. Moderate eye infection. STI testing. Non-life-threatening allergy.
PCP 2-3 DAYS: Worsening chronic condition. Lab follow-up. New med needed. Symptoms >7d not improving. Mental health non-crisis. Preventive care. Post-urgent-care follow-up.
TELEHEALTH: Uncomplicated UTI adult female. Cold/flu minor. Minor rash with photo. Prescription refill. Mental health med management."""
}

def get_gl(intent, complaint):
    c = complaint.lower()
    gl = []
    if intent == "symptom":
        if any(w in c for w in ["pee","urin","burn","dysuria","bladder","frequent"]): gl.append(GL["uti"])
        if any(w in c for w in ["mole","lesion","spot","skin","rash","itch","eczema"]): gl.append(GL["skin"])
        if any(w in c for w in ["throat","cough","cold","flu","sinus","fever","congestion"]): gl.append(GL["respiratory"])
        if any(w in c for w in ["back pain","lower back","lumbar"]): gl.append(GL["back"])
        if any(w in c for w in ["ankle","sprain","twisted","rolled"]): gl.append(GL["ankle"])
        if any(w in c for w in ["heartburn","acid","reflux","gerd"]): gl.append(GL["heartburn"])
        if any(w in c for w in ["stomach","nausea","vomit","diarrhea","gastro","bowel"]): gl.append(GL["gi"])
        if any(w in c for w in ["baby","infant","child","toddler","month old","week old"]): gl.append(GL["pediatric"])
        if not gl: gl = [GL["respiratory"],GL["gi"]]
    elif intent == "mental_health": gl.append(GL["mental_health"])
    elif intent == "medication": gl.append(GL["medication"])
    elif intent == "preventive": gl.append(GL["preventive"])
    elif intent == "chronic":
        if any(w in c for w in ["blood pressure","hypertension","bp","systolic"]): gl.append(GL["hypertension"])
        if any(w in c for w in ["diabetes","glucose","hba1c","a1c","sugar","insulin"]): gl.append(GL["diabetes"])
        if any(w in c for w in ["asthma","inhaler","wheez"]): gl.append(GL["asthma"])
        if not gl: gl = [GL["hypertension"],GL["diabetes"]]
    elif intent == "lab": gl.append(GL["lab_results"])
    elif intent == "routing": gl.append(GL["routing"])
    return "\n\n---\n\n".join(gl[:3])

# ── EMERGENCY ───────────────────────────────────────────────────────
def chk_emergency(text):
    t = text.lower()
    chest = any(w in t for w in ["chest pain","chest tightness","chest pressure","chest heaviness"])
    breath = any(w in t for w in ["shortness of breath","cant breathe","can't breathe","trouble breathing","breathless"])
    if chest and breath:
        return "911","🚨 Chest pain + breathing difficulty is a cardiac emergency.\n\n**CALL 911 NOW.** Do not drive yourself.\n\nChew one regular aspirin (325mg) while waiting — only if not allergic."
    singles = {
        "throat swelling":"🚨 Throat swelling can block your airway.\n\n**CALL 911 NOW.** Use EpiPen if available.",
        "throat closing":"🚨 Throat closing is a medical emergency.\n\n**CALL 911 NOW.**",
        "face drooping":"🚨 Face drooping is a stroke warning sign (FAST).\n\n**CALL 911 NOW.** Note exact time symptoms started.",
        "worst headache of my life":"🚨 Thunderclap headache = possible brain bleed.\n\n**CALL 911 NOW.**",
    }
    crisis = {
        "suicid":"💙 You mentioned thoughts of suicide. Support is available right now.\n\nPlease **call or text 988** — free, 24/7.\n\nOr text HOME to 741741.",
        "kill myself":"💙 Please reach out right now.\n\n**Call or text 988** — available 24/7.",
        "end my life":"💙 Support is available right now.\n\n**Call or text 988** — 24/7.",
        "want to die":"💙 I hear you. Please reach out.\n\n**Call or text 988** — they are here for you.",
    }
    for kw,msg in singles.items():
        if kw in t: return "911",msg
    for kw,msg in crisis.items():
        if kw in t: return "988",msg
    return None,None

# ── INTENT DETECT ───────────────────────────────────────────────────
INTENT_SYS = """Classify the patient question into ONE intent: symptom, medication, preventive, mental_health, chronic, lab, routing, general
Reply ONLY with the intent word. Nothing else."""

def detect_intent(text, api_key):
    t = text.lower()
    if any(w in t for w in ["er or","urgent care","emergency room","should i go","hospital or"]): return "routing"
    if any(w in t for w in ["my cholesterol","my hba1c","my a1c","lab result","blood test","my glucose is","my hemoglobin"]): return "lab"
    if any(w in t for w in ["can i take","how much","dosage","side effect","ibuprofen","tylenol","benadryl","advil","motrin","pepcid","prilosec","claritin","zyrtec"]): return "medication"
    if any(w in t for w in ["screening","mammogram","colonoscopy","pap smear","vaccine","annual physical","checkup","preventive","when should i get"]): return "preventive"
    if any(w in t for w in ["depress","anxious","anxiety","mental health","low mood","panic","stress","overwhelmed","cant sleep","feeling sad","feeling hopeless"]): return "mental_health"
    if any(w in t for w in ["my diabetes","my blood pressure","my asthma","managing my","my bp reading","my inhaler"]): return "chronic"
    try:
        import anthropic
        c = anthropic.Anthropic(api_key=api_key)
        r = c.messages.create(model="claude-haiku-4-5-20251001",max_tokens=10,system=INTENT_SYS,messages=[{"role":"user","content":text}])
        intent = r.content[0].text.strip().lower()
        return intent if intent in ["symptom","medication","preventive","mental_health","chronic","lab","routing","general"] else "symptom"
    except: return "symptom"

# ── SYSTEM PROMPTS ──────────────────────────────────────────────────
RULES = """
ALWAYS: say "consistent with X per [Guideline]" never "you have X". Never name prescription drugs. Cite specific guideline for every clinical claim. Give EXACT OTC dosing: product name, mg, frequency, max duration, safety note."""

SP = {
"symptom": """You are HealthMate clinical triage AI. Conduct physician-style intake — ONE question at a time.

PHASE 1 (first 4-5 exchanges): Ask ONE focused question. Choose most important unanswered: duration, severity 1-10, fever/temp, other symptoms, medications/allergies, medical history, age, pregnancy (if relevant), for skin: location/spreading.
ONE question max. 2 sentences max. Brief warm acknowledgment first. NO guidance yet.

PHASE 2 (after 4-5 exchanges — output this exactly):
ASSESSMENT_READY
URGENCY: [GREEN / YELLOW / URGENT]
**What your symptoms suggest**
[2-3 sentences. "Consistent with X per [Guideline]." Never "you have X."]
**What to do right now**
1. [Action]
2. [Action]
**OTC options**
[Specific product, exact mg, frequency, max duration, safety note] OR "No OTC appropriate — see physician."
**Watch for these red flags**
- [Red flag]
- [Red flag]
**Recommended next step**
[Clear recommendation]
---
*Sources: [guideline citations with year]*
*Disclaimer: Informational only. Your physician makes the final diagnosis.*""" + RULES,

"medication": """You are HealthMate medication guidance AI. Help with OTC medications safely.

INTAKE — ONE question at a time:
1. Which medication? 2. Specific concern? 3. Kidney/liver disease or pregnant? 4. Other medications? 5. Age?

After gathering context output:
MED_READY
**About [medication name]**
[What it is, what it treats — FDA DailyMed]
**Standard OTC dosing**
[Exact product, exact mg, frequency, max dose/day, max duration]
**Who should NOT take this**
[Contraindications from FDA label]
**Key interactions**
[Clinically significant interactions]
**When to call physician instead**
[Situations where OTC insufficient]
---
*Source: FDA DailyMed*
*Disclaimer: OTC guidance only. For prescription questions consult your physician or pharmacist.*
NEVER advise on prescription dose changes. Flag serious interaction risks immediately.""" + RULES,

"preventive": """You are HealthMate preventive care AI.

INTAKE — ONE question at a time:
1. Age? 2. Male/female/other? 3. Do you smoke? 4. Family history of cancer/heart disease/diabetes? 5. Last checkup/screenings?

After gathering age and sex:
PREVENTIVE_READY
**Screenings recommended for you**
[USPSTF Grade A/B by age/sex with year — name, frequency, age range, why]
**Vaccines recommended for you**
[CDC Adult Immunization Schedule — name, schedule]
**What you can do at home**
[BP monitoring, skin self-exam, etc. as appropriate]
**Recommended next step**
Schedule preventive visit with PCP to order these screenings.
---
*Sources: USPSTF [year], CDC Adult Immunization Schedule [year]*
*Disclaimer: Population-level recommendations. Your physician personalizes.*""" + RULES,

"mental_health": """You are HealthMate mental health navigation AI. Be warm, compassionate, non-judgmental. ONE question at a time.

INTAKE:
1. Tell me more about what you've been experiencing.
2. How long have you been feeling this way?
3. PHQ-2: Over past 2 weeks — felt down, depressed, or hopeless? (not at all / several days / more than half / nearly every day)
4. PHQ-2: Over past 2 weeks — little interest or pleasure in things? (same scale)
5. Ask DIRECTLY: Are you having any thoughts of harming yourself or others? (safe and important to ask)
6. How is this affecting daily life — work, relationships, sleep?

CRITICAL: If ANY yes to self-harm thoughts — STOP. Provide 988 immediately. Do not continue intake.

After gathering context:
MENTAL_READY
**What you're describing**
[Validate experience. Non-stigmatizing. Cite USPSTF/APA if relevant.]
**Severity**
[Based on PHQ-2 responses: minimal/mild/moderate/severe]
**What may help right now**
[Mild: evidence-based self-care. Moderate+: professional support.]
**Crisis resources** (always include)
- 988 Suicide & Crisis Lifeline: call or text **988** (24/7, free)
- Crisis Text Line: text HOME to **741741**
**Recommended next step**
[Clear: self-care / PCP / therapist / psychiatrist / crisis services]
---
*Sources: USPSTF Depression Screening [year], SAMHSA*
*Disclaimer: Not a clinical diagnosis. Please speak with a mental health professional.*""" + RULES,

"chronic": """You are HealthMate chronic disease management AI.

INTAKE — ONE question at a time:
1. Which condition? 2. Most recent reading/measurement? 3. Current medications for this? 4. Specific concern today? 5. Any new symptoms?

After gathering context:
CHRONIC_READY
**Your condition targets**
[Evidence-based targets from ADA/AHA/GINA/ACP with year]
**How your reading compares**
[Factual comparison to guideline targets]
**Lifestyle factors that matter most**
[Top 3 evidence-based interventions for this condition]
**When to call your physician**
[Specific threshold readings or symptoms requiring physician contact]
**Red flags — call 911 if:**
[Life-threatening escalations for this condition]
**Recommended next step**
[Clear recommendation]
---
*Sources: [specific guideline with year]*
*Disclaimer: HealthMate does not adjust prescriptions. All medication decisions require your physician.*
NEVER adjust or recommend changes to prescription medications.""" + RULES,

"lab": """You are HealthMate lab interpretation AI.

INTAKE — ONE question at a time:
1. Which test? 2. Value and units? 3. Was this fasting? 4. Any symptoms? 5. Relevant medical history?

After gathering context:
LAB_READY
**What this test measures**
[Simple explanation — 2 sentences]
**Normal range**
[Standard reference range from relevant guidelines]
**What your value means**
["Your value of [X] falls in the [normal/borderline/abnormal] range." Factual, not alarming.]
**Context matters**
[Factors affecting this: fasting status, medications, symptoms, trends]
**What happens next**
[Monitor / routine visit / prompt physician contact]
**Questions to ask your physician**
[2-3 specific questions for next appointment]
---
*Sources: [ADA/AHA/ATS/etc. with year]*
*Disclaimer: Requires your full clinical context. Only your physician can diagnose based on results.*""" + RULES,

"routing": """You are HealthMate care routing AI. Help decide ER vs urgent care vs PCP.

INTAKE — ONE question at a time:
1. Main symptom? 2. How long? 3. Severity 1-10? 4. Fever? 5. Getting better, worse, or same?

After 3-4 exchanges:
ROUTING_READY
**Where to go**
[Clear direct recommendation: 911 / ER now / Urgent Care today / PCP within X days / Telehealth / Self-care]
**Why this recommendation**
[2-3 sentences clinical reasoning]
**What to tell them when you arrive**
[Duration, severity, associated symptoms, medications]
**If symptoms change**
["If you develop X, call 911 immediately."]
---
*Source: HealthMate Care Routing Framework*
*Disclaimer: When in doubt, always err toward higher level of care.*""" + RULES,

"general": """You are HealthMate general health AI. Answer health questions accurately. Cite relevant guidelines. Recommend appropriate care if needed. Keep focused — 3-5 sentences for simple questions.
*Disclaimer: Informational guidance. Your physician makes clinical decisions.*""" + RULES,
}

LABELS = {
    "symptom":("🩺 Symptom triage","it"),
    "medication":("💊 Medication","ip"),
    "preventive":("✅ Preventive care","ig"),
    "mental_health":("🧠 Mental health","ip"),
    "chronic":("♾ Chronic disease","ib"),
    "lab":("🔬 Lab results","ib"),
    "routing":("🏥 Care routing","iy"),
    "general":("💬 General health","ig"),
}
READY = ["ASSESSMENT_READY","MED_READY","PREVENTIVE_READY","MENTAL_READY","CHRONIC_READY","LAB_READY","ROUTING_READY"]
THRESH = {"symptom":4,"medication":3,"preventive":3,"mental_health":4,"chronic":3,"lab":3,"routing":3,"general":1}

SCENARIOS = {
    "💊 UTI symptoms":"I have burning when I pee and going very frequently.",
    "🔬 Changed mole":"I have a mole on my back that has changed over 2 months.",
    "😷 Sore throat + fever":"Severe sore throat and fever since yesterday.",
    "🏋️ Back pain":"I threw out my back at the gym this morning.",
    "🦵 Ankle sprain":"I rolled my ankle playing basketball an hour ago.",
    "🔥 Heartburn":"Burning in my chest after dinner almost every night.",
    "👶 Baby fever":"My 7-week-old baby has a fever of 38.3C.",
    "🧠 Feeling low":"I have been feeling really down and low energy for 3 weeks.",
    "🤢 Stomach bug":"Diarrhea and nausea since last night.",
    "🚨 Chest + breathing":"I have chest pain and shortness of breath.",
    "💊 Ibuprofen question":"Can I take ibuprofen if I am on a blood thinner?",
    "📋 Screening question":"I am 45 years old woman. What cancer screenings do I need?",
    "🩸 Lab result":"My LDL cholesterol came back at 165 mg/dL. Is that bad?",
    "🏥 ER or urgent care?":"I have high fever 103F and severe ear pain. Where should I go?",
    "❤ Blood pressure":"My blood pressure reading today was 148/92. I am on medication.",
}

# session state
for k,v in {"messages":[],"exchange_count":0,"assessment_done":False,"show_booking":False,
             "chief_complaint":"","intake_history":{},"urgency":"GREEN","intent":None,"intent_detected":False}.items():
    if k not in st.session_state:
        st.session_state[k] = ([] if isinstance(v,list) else {} if isinstance(v,dict) else v)

# UI
st.markdown("""<div class="hm-header"><h1>🏥 HealthMate</h1><p>AI Health Navigation · AAD · CDC · IDSA · AHA · ACOG · AAP · USPSTF · FDA DailyMed</p></div>""",unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    api_key = st.text_input("Anthropic API Key",value=os.environ.get("ANTHROPIC_API_KEY",""),type="password",help="console.anthropic.com — $5 = 500 sessions")
    st.markdown("---")
    st.markdown("### 🩺 Try a scenario")
    for label,scenario in SCENARIOS.items():
        if st.button(label,use_container_width=True):
            st.session_state.prefill = scenario
    st.markdown("---")
    if st.button("🔄 New conversation",use_container_width=True):
        for k in ["messages","exchange_count","assessment_done","show_booking","chief_complaint","intake_history","urgency","intent","intent_detected"]:
            st.session_state[k] = ([] if k=="messages" else {} if k=="intake_history" else False if k in ["assessment_done","show_booking","intent_detected"] else 0 if k=="exchange_count" else "GREEN" if k=="urgency" else None if k=="intent" else "")
        st.rerun()
    st.markdown("---")
    st.markdown("""### ✅ What I handle
- **Symptoms** — one question at a time
- **Medications** — OTC dosing, interactions
- **Preventive care** — screenings, vaccines
- **Mental health** — PHQ screening, crisis support
- **Chronic disease** — targets, escalation triggers
- **Lab results** — what your values mean
- **Care routing** — ER vs urgent care vs PCP

*Emergency? Call 911 immediately.*

*HealthMate Inc. · 2026*""")

if st.session_state.chief_complaint and not st.session_state.assessment_done:
    n = min(st.session_state.exchange_count,5)
    steps=["🔍 Understanding your question...","📋 Gathering your history...","🩺 Asking follow-up questions...","📊 Almost ready...","⚕️ Preparing your response..."]
    st.markdown(f'<div class="pbar">{steps[n]} (Step {n+1} of 5)</div>',unsafe_allow_html=True)

if st.session_state.intent and st.session_state.intent in LABELS:
    lbl,cls = LABELS[st.session_state.intent]
    st.markdown(f'<span class="ibadge {cls}">{lbl}</span>',unsafe_allow_html=True)

def clean_r(content):
    for m in READY: content = content.replace(m,"")
    for u in ["URGENCY: URGENT","URGENCY: YELLOW","URGENCY: GREEN"]: content = content.replace(u,"")
    return content.strip()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"],avatar="🧑" if msg["role"]=="user" else "🏥"):
        content = msg["content"]
        clean = clean_r(content)
        if "URGENCY: URGENT" in content: st.markdown('<span class="ibadge ir">🔴 URGENT — See Physician Today</span>',unsafe_allow_html=True)
        elif "URGENCY: YELLOW" in content: st.markdown('<span class="ibadge iy">🟡 YELLOW — See Physician in 2-3 Days</span>',unsafe_allow_html=True)
        elif "URGENCY: GREEN" in content and any(m in content for m in READY): st.markdown('<span class="ibadge ig">🟢 GREEN — Self-Care Appropriate</span>',unsafe_allow_html=True)
        st.markdown(clean)

prefill = st.session_state.pop("prefill","")
placeholder = ("Describe symptoms, ask about a medication, lab result, screening, or 'should I go to ER?'" if not st.session_state.chief_complaint else "Your answer...")
user_input = st.chat_input(placeholder)
if prefill and not user_input: user_input = prefill

if user_input:
    if not st.session_state.chief_complaint: st.session_state.chief_complaint = user_input
    with st.chat_message("user",avatar="🧑"): st.markdown(user_input)
    st.session_state.messages.append({"role":"user","content":user_input})

    etype,emsg = chk_emergency(user_input)
    if etype:
        with st.chat_message("assistant",avatar="🏥"):
            if etype=="911":
                st.error(emsg)
                c1,c2=st.columns(2)
                with c1: st.link_button("🚨 Call 911","tel:911",use_container_width=True)
                with c2: st.link_button("🏥 Find ER","https://www.google.com/maps/search/emergency+room+near+me",use_container_width=True)
            else:
                st.warning(emsg)
                c1,c2=st.columns(2)
                with c1: st.link_button("📞 Call 988","tel:988",use_container_width=True)
                with c2: st.link_button("💬 Crisis Text","sms:741741?body=HOME",use_container_width=True)
        st.session_state.messages.append({"role":"assistant","content":emsg})
    elif not api_key:
        with st.chat_message("assistant",avatar="🏥"): st.warning("Please enter your Anthropic API key in the sidebar.")
    else:
        with st.chat_message("assistant",avatar="🏥"):
            with st.spinner("Thinking..."):
                try:
                    import anthropic
                    client = anthropic.Anthropic(api_key=api_key)
                    if not st.session_state.intent_detected:
                        intent = detect_intent(user_input,api_key)
                        st.session_state.intent = intent
                        st.session_state.intent_detected = True
                        if intent in LABELS:
                            lbl,cls = LABELS[intent]
                            st.markdown(f'<span class="ibadge {cls}">{lbl}</span>',unsafe_allow_html=True)
                    intent = st.session_state.intent or "symptom"
                    system = SP.get(intent,SP["general"])
                    claude_msgs = [{"role":m["role"],"content":m["content"]} for m in st.session_state.messages[:-1]]
                    user_content = user_input
                    if st.session_state.exchange_count >= 2:
                        gl = get_gl(intent,st.session_state.chief_complaint)
                        user_content = f"{user_input}\n\n[Clinical reference: {gl[:2000]}]"
                    claude_msgs.append({"role":"user","content":user_content})
                    push = ""
                    if st.session_state.exchange_count >= THRESH.get(intent,3):
                        push = "\n\nYou have gathered enough information. Provide the complete final response now."
                    resp = client.messages.create(model="claude-sonnet-4-6",max_tokens=1500,system=system+push,messages=claude_msgs)
                    reply = resp.content[0].text
                    st.session_state.exchange_count += 1
                    st.session_state.intake_history[f"a{st.session_state.exchange_count}"] = user_input
                    is_final = any(m in reply for m in READY) or st.session_state.exchange_count >= THRESH.get(intent,3)+2
                    if is_final: st.session_state.assessment_done = True
                    clean = clean_r(reply)
                    if "URGENCY: URGENT" in reply:
                        st.session_state.urgency="URGENT"; st.session_state.show_booking=True
                        st.markdown('<span class="ibadge ir">🔴 URGENT — See Physician Today</span>',unsafe_allow_html=True)
                    elif "URGENCY: YELLOW" in reply:
                        st.session_state.urgency="YELLOW"; st.session_state.show_booking=True
                        st.markdown('<span class="ibadge iy">🟡 YELLOW — See Physician in 2-3 Days</span>',unsafe_allow_html=True)
                    elif "URGENCY: GREEN" in reply and is_final:
                        st.session_state.urgency="GREEN"
                        if "physician" in clean.lower() or "doctor" in clean.lower(): st.session_state.show_booking=True
                        st.markdown('<span class="ibadge ig">🟢 GREEN — Self-Care Appropriate</span>',unsafe_allow_html=True)
                    st.markdown(clean)
                    if is_final:
                        cost = (resp.usage.input_tokens*0.000003)+(resp.usage.output_tokens*0.000015)
                        with st.expander(f"Session info — ${cost:.4f}",expanded=False):
                            st.caption(f"Intent: {intent} · Exchanges: {st.session_state.exchange_count} · Tokens: {resp.usage.input_tokens:,} in / {resp.usage.output_tokens:,} out")
                    st.session_state.messages.append({"role":"assistant","content":reply})
                except Exception as e:
                    err=str(e)
                    if "auth" in err.lower() or "api_key" in err.lower(): st.error("Invalid API key — check the sidebar.")
                    else: st.error(f"Error: {err}")

if st.session_state.show_booking and st.session_state.assessment_done:
    st.markdown("---")
    st.markdown("### 📅 Available In-Network Providers")
    complaint = st.session_state.chief_complaint.lower()
    urgency = st.session_state.urgency
    intent = st.session_state.intent or "symptom"
    if intent == "mental_health":
        spec,providers = "Mental Health",[{"name":"Dr. Emily Rodriguez, LCSW","avail":"This week Thu 3:00 PM","dist":"1.4 mi","copay":"$30"},{"name":"Dr. Mark Chen, MD — Psychiatry","avail":"Next week Tue 10:00 AM","dist":"2.2 mi","copay":"$50"}]
    elif intent in ["preventive","lab","chronic"]:
        spec,providers = "Primary Care",[{"name":"Dr. Sarah Chen, MD","avail":"Tomorrow 10:00 AM","dist":"0.8 mi","copay":"$20"},{"name":"Dr. James Park, DO","avail":"Tomorrow 2:30 PM","dist":"1.4 mi","copay":"$20"}]
    elif any(w in complaint for w in ["mole","lesion","skin","rash","eczema"]):
        spec,providers = "Dermatology",[{"name":"Dr. Maria Rodriguez, FAAD","avail":"This Thursday 2:00 PM","dist":"1.2 mi","copay":"$40"},{"name":"Dr. James Kim, MD — Derm","avail":"Next Monday 10:00 AM","dist":"2.1 mi","copay":"$40"}]
    elif urgency == "URGENT":
        spec,providers = "Primary Care / Urgent Care",[{"name":"Dr. Sarah Chen, MD","avail":"Today 3:30 PM","dist":"0.8 mi","copay":"$20"},{"name":"CityMD Urgent Care","avail":"Today — walk-in open","dist":"1.1 mi","copay":"$30"}]
    else:
        spec,providers = "Primary Care",[{"name":"Dr. Sarah Chen, MD","avail":"Tomorrow 10:00 AM","dist":"0.8 mi","copay":"$20"},{"name":"Dr. James Park, DO","avail":"Tomorrow 2:30 PM","dist":"1.4 mi","copay":"$20"}]
    st.caption(f"**{spec}** · Insurance verified ✅")
    for p in providers:
        c1,c2,c3=st.columns([3,2,1])
        with c1: st.markdown(f"**{p['name']}**"); st.caption(f"{p['dist']} · Est. {p['copay']} copay")
        with c2: st.markdown(f"🕐 {p['avail']}")
        with c3:
            if st.button("Book",key=f"b_{p['name']}",use_container_width=True): st.success(f"✅ Appointment requested — {p['name']}")
    st.caption("*Demo — connects to Zocdoc + Availity in production.*")

st.markdown("""<div class="disc">⚕️ <strong>Medical Disclaimer:</strong> HealthMate provides health information based on published clinical guidelines for educational purposes only. It does not provide medical advice, diagnosis, or treatment. Always consult a qualified healthcare professional. In an emergency call 911 immediately.<br><br>🔒 <strong>Privacy:</strong> No personal health data is stored after your session ends.<br><br>📋 <strong>Sources:</strong> AAD · CDC · IDSA · ACP · AGA · ACG · USPSTF · FDA DailyMed · AAP · SAMHSA · AHA/ACC · ADA · GINA</div>""",unsafe_allow_html=True)
