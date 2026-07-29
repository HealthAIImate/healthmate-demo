"""
HealthMate — Web Demo App
=========================
User-friendly Streamlit interface for physician validation
and early user testing.

Deploy to Streamlit Cloud (free):
1. Push this file to GitHub
2. Go to share.streamlit.io
3. Connect your GitHub repo
4. Set ANTHROPIC_API_KEY in Streamlit secrets

Run locally:
    streamlit run app.py
"""

import os
import sys
import json
import time
import streamlit as st

# ── PAGE CONFIG ───────────────────────────────────────────────────
st.set_page_config(
    page_title="HealthMate — AI Health Navigation",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── STYLING ───────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #F8FAFC; }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Header */
    .hm-header {
        background: linear-gradient(135deg, #0D47A1 0%, #1E88E5 100%);
        padding: 2rem 2rem 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    .hm-header h1 {
        color: white;
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .hm-header p {
        color: #90CAF9;
        font-size: 1rem;
        margin: 0.5rem 0 0 0;
    }

    /* Urgency badges */
    .badge-green {
        background: #E8F5E9; color: #1B5E20;
        padding: 4px 14px; border-radius: 20px;
        font-weight: 700; font-size: 0.85rem;
        display: inline-block;
    }
    .badge-yellow {
        background: #FFF8E1; color: #E65100;
        padding: 4px 14px; border-radius: 20px;
        font-weight: 700; font-size: 0.85rem;
        display: inline-block;
    }
    .badge-red {
        background: #FFEBEE; color: #B71C1C;
        padding: 4px 14px; border-radius: 20px;
        font-weight: 700; font-size: 0.85rem;
        display: inline-block;
    }

    /* Response box */
    .response-box {
        background: white;
        border: 1px solid #E3F2FD;
        border-left: 4px solid #1565C0;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
    }

    /* Emergency box */
    .emergency-box {
        background: #FFEBEE;
        border: 2px solid #B71C1C;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
    }

    /* Provider card */
    .provider-card {
        background: white;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }

    /* Disclaimer */
    .disclaimer {
        background: #F5F5F5;
        border-radius: 6px;
        padding: 0.75rem 1rem;
        font-size: 0.8rem;
        color: #757575;
        margin-top: 1rem;
    }

    /* Step indicator */
    .step-indicator {
        background: #E3F2FD;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-size: 0.85rem;
        color: #1565C0;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ── CLINICAL SYSTEM PROMPT ────────────────────────────────────────
SYSTEM_PROMPT = """You are HealthMate's clinical triage AI. You assist users in understanding their symptoms and navigating to the right care. You are NOT a doctor and you do NOT provide medical diagnoses.

CRITICAL LANGUAGE RULES — follow every rule on every response:
1. NEVER say "you have [condition]". ALWAYS say "your symptoms are consistent with [condition] per [guideline source]"
2. NEVER name a prescription drug. If a prescription is needed, say "a physician will prescribe the appropriate medication"
3. ALWAYS cite the specific clinical guideline source for every clinical claim
4. ALWAYS include urgency tier as the FIRST line: URGENCY: GREEN, URGENCY: YELLOW, or URGENCY: URGENT
5. ALWAYS end with: "Disclaimer: This is informational guidance only. Your physician makes the final diagnosis."
6. When recommending OTC medication: give EXACT product name, exact dose, exact frequency, exact max duration
7. NEVER suggest antibiotics — route all suspected bacterial infections to physician booking immediately
8. Be DIRECT and CLINICALLY PRECISE. Not vague.

RESPONSE FORMAT — use exactly this structure:
URGENCY: [GREEN/YELLOW/URGENT]

**What Your Symptoms Suggest**
[Clinical assessment — guideline cited]

**What To Do Right Now**
[Numbered action steps]

**OTC Options While You Wait**
[Specific product, exact dose, frequency, max duration — or "None appropriate — see physician"]

**Watch For These Red Flags**
[Symptoms that require immediate escalation]

**Recommended Next Step**
[Self-care plan OR physician booking recommendation]

---
*Sources: [specific guideline citations]*
Disclaimer: This is informational guidance only. Your physician makes the final diagnosis and treatment decisions."""

# ── GUIDELINE CONTEXT ─────────────────────────────────────────────
GUIDELINES = {
    "uti": """IDSA Uncomplicated UTI Guidelines 2022:
- Uncomplicated cystitis: dysuria, frequency, urgency without systemic symptoms
- OTC symptomatic relief: Phenazopyridine (AZO Standard) 200mg 3x daily with food — max 2 days
- Antibiotic required (prescription): physician must prescribe
- Pyelonephritis red flags: fever >100.4°F, flank pain, nausea/vomiting → ER immediately
- Pregnancy: ANY UTI → immediate physician evaluation, no OTC management
FDA DailyMed Phenazopyridine: 2 tablets (190mg) 3x daily with food, max 2 days, turns urine orange""",

    "skin": """AAD Clinical Guidelines 2023 — Atopic Dermatitis & Contact Dermatitis:
- Mild-moderate: topical corticosteroids + emollients first-line
- Hydrocortisone 1% cream: thin layer twice daily, max 7 days face, max 14 days body
- Trigger removal: fragrances, wool, hot water
- Moisturizer within 3 minutes of bathing
- Infection signs requiring physician: crusting, honey-colored exudate, fever, spreading redness
AAD ABCDE Melanoma Rule: Asymmetry, Border, Color variation, Diameter >6mm, Evolving → derm referral
FDA DailyMed Hydrocortisone 1%: apply thin film 2-4x daily, max 7 days face, max 14 days body""",

    "respiratory": """CDC Respiratory Guidelines + IDSA Pharyngitis Guidelines 2022:
- Viral URI (cold/flu): self-limiting 5-7 days, no antibiotics
- Centor criteria for strep: fever, tonsillar exudate, tender nodes, no cough (3-4 = test for strep)
- OTC fever/pain: Ibuprofen 200-400mg every 6-8h with food OR Acetaminophen 500-1000mg every 6h
- OTC congestion: Pseudoephedrine 30mg every 4-6h (behind pharmacy counter)
- Epiglottitis red flags: stridor, drooling, high fever, unable to swallow → call 911
- Peritonsillar abscess: muffled voice, drooling, trismus → ER immediately""",

    "musculoskeletal": """ACP Low Back Pain Guidelines 2022:
- Acute (<4 weeks): conservative treatment, most resolves in 4-6 weeks
- OTC: Ibuprofen 400-600mg every 6-8h with food (max 1200mg/day OTC), heat therapy
- Ottawa Ankle Rules: X-ray if bone tenderness at fibula/tibia tip OR unable to bear weight 4 steps
- PRICE protocol for sprains: Protection, Rest, Ice 15-20min, Compression, Elevation
- Cauda equina RED FLAGS: bladder/bowel loss + back pain → 911 immediately
- Ibuprofen OTC: 400mg every 6-8h with food, max 1200mg/day, max 10 days""",

    "gi": """AGA/ACG Guidelines + FDA DailyMed:
- Heartburn/GERD: lifestyle first (elevate HOB, avoid triggers), OTC PPIs for frequent symptoms
- Omeprazole (Prilosec OTC): 20mg once daily before breakfast, 14-day course, max every 4 months
- Famotidine (Pepcid AC): 10-20mg once or twice daily, max 2 weeks
- GI bleed RED FLAGS: black/tarry stool, vomiting blood → ER immediately
- Appendicitis RED FLAGS: fever + severe right lower quadrant pain → ER immediately
- Ibuprofen OTC for GI pain: use with caution, take with food""",

    "pediatric": """AAP Fever Management Guidelines 2021:
- Age <3 months ANY fever >=38.0°C: EMERGENCY — ER immediately, no exceptions
- Age 3-36 months fever >=39°C: physician same day
- Acetaminophen (Infant Tylenol 160mg/5mL): 15mg/kg per dose every 4-6h, max 5 doses/24h
- Ibuprofen (Children's Motrin 100mg/5mL, age >=6mo): 10mg/kg per dose every 6-8h
- NEVER give aspirin to children (Reye syndrome)
- NEVER give ibuprofen to infants under 6 months
- Weight-based dosing always — never age-based alone""",

    "mental_health": """USPSTF Depression Screening 2023 + SAMHSA 988 Protocol:
- PHQ-2 positive (score >=3): proceed to full PHQ-9 assessment
- PHQ-9 5-9: mild, watchful waiting + counseling
- PHQ-9 10-14: moderate, treatment plan needed
- PHQ-9 >=15: severe, immediate treatment + psychiatry referral
- GAD-7 >=10: moderate anxiety, treatment indicated
- ANY suicidal ideation: 988 Lifeline immediately (call or text 988)
- OTC/self-care (PHQ-9 <5 only): exercise 150min/week, sleep hygiene, mindfulness apps
- Evidence-based apps: Headspace, Calm (RCT evidence for mild anxiety)""",
}

def get_guidelines(symptoms: str) -> str:
    """Route symptoms to relevant guideline context."""
    s = symptoms.lower()
    contexts = []
    if any(w in s for w in ["pee", "urin", "burn", "bladder", "dysuria"]):
        contexts.append(GUIDELINES["uti"])
    if any(w in s for w in ["rash", "skin", "itch", "mole", "eczema", "lesion", "spot"]):
        contexts.append(GUIDELINES["skin"])
    if any(w in s for w in ["throat", "cough", "cold", "flu", "sinus", "sneez", "congestion", "breath"]):
        contexts.append(GUIDELINES["respiratory"])
    if any(w in s for w in ["back", "ankle", "knee", "joint", "sprain", "muscle", "neck"]):
        contexts.append(GUIDELINES["musculoskeletal"])
    if any(w in s for w in ["stomach", "nausea", "heartburn", "acid", "reflux", "bowel", "diarrhea", "constipat"]):
        contexts.append(GUIDELINES["gi"])
    if any(w in s for w in ["baby", "infant", "child", "toddler", "month old", "week old", "year old", "fever"]):
        contexts.append(GUIDELINES["pediatric"])
    if any(w in s for w in ["depress", "anxious", "anxiety", "mood", "sad", "mental", "stress", "sleep", "worry"]):
        contexts.append(GUIDELINES["mental_health"])
    if not contexts:
        # Return all as fallback
        contexts = list(GUIDELINES.values())
    return "\n\n---\n\n".join(contexts)

# ── EMERGENCY DETECTION ───────────────────────────────────────────
EMERGENCY_KEYWORDS = {
    "chest pain": ("chest pain", "Chest pain requires immediate evaluation.", "CARDIAC"),
    "chest tightness": ("chest tightness and breathing difficulty", "Chest tightness may indicate a cardiac emergency.", "CARDIAC"),
    "cant breathe": ("difficulty breathing", "Difficulty breathing requires immediate evaluation.", "RESPIRATORY"),
    "can't breathe": ("difficulty breathing", "Difficulty breathing requires immediate evaluation.", "RESPIRATORY"),
    "stroke": ("stroke symptoms", "Stroke symptoms require immediate 911 call.", "STROKE"),
    "face drooping": ("facial drooping + arm weakness", "These are stroke warning signs — call 911 immediately.", "STROKE"),
    "throat closing": ("throat swelling", "Throat swelling can block your airway — call 911 now.", "ANAPHYLAXIS"),
    "throat swelling": ("throat swelling", "Throat swelling is a medical emergency — call 911.", "ANAPHYLAXIS"),
    "suicid": ("suicidal thoughts", "Please reach out for support right now.", "CRISIS"),
    "kill myself": ("suicidal ideation", "You don't have to face this alone. Help is available now.", "CRISIS"),
    "end my life": ("suicidal ideation", "Please reach out — support is available right now.", "CRISIS"),
}

def check_emergency(text: str):
    """Check for emergency keywords. Returns (is_emergency, message, type) or None."""
    text_lower = text.lower()
    for keyword, (symptom, message, etype) in EMERGENCY_KEYWORDS.items():
        if keyword in text_lower:
            return True, message, etype
    return False, None, None

# ── BOOKING SIMULATION ────────────────────────────────────────────
PROVIDERS = {
    "urgent": [
        {"name": "Dr. Sarah Chen, MD", "specialty": "Primary Care", "distance": "0.8 mi",
         "available": "Today 3:30 PM", "network": "In-Network", "copay": "$20"},
        {"name": "CityMD Urgent Care", "specialty": "Urgent Care", "distance": "1.1 mi",
         "available": "Today, walk-in", "network": "In-Network", "copay": "$30"},
    ],
    "dermatology": [
        {"name": "Dr. Maria Rodriguez, FAAD", "specialty": "Dermatology", "distance": "1.2 mi",
         "available": "This week Thu 2 PM", "network": "In-Network", "copay": "$40"},
        {"name": "Dr. James Kim, MD", "specialty": "Dermatology", "distance": "2.1 mi",
         "available": "Next week Mon 10 AM", "network": "In-Network", "copay": "$40"},
    ],
    "primary": [
        {"name": "Dr. Sarah Chen, MD", "specialty": "Primary Care", "distance": "0.8 mi",
         "available": "Tomorrow 10:00 AM", "network": "In-Network", "copay": "$20"},
        {"name": "Dr. James Park, DO", "specialty": "Primary Care", "distance": "1.4 mi",
         "available": "Tomorrow 2:30 PM", "network": "In-Network", "copay": "$20"},
    ],
}

def get_providers(response_text: str, symptoms: str) -> list:
    """Pick appropriate providers based on response and symptoms."""
    s = symptoms.lower() + response_text.lower()
    if "urgent" in response_text.upper() or "today" in response_text.lower():
        return PROVIDERS["urgent"]
    if any(w in s for w in ["derm", "mole", "skin", "rash", "lesion"]):
        return PROVIDERS["dermatology"]
    return PROVIDERS["primary"]

# ── SESSION STATE ─────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_count" not in st.session_state:
    st.session_state.session_count = 0
if "show_booking" not in st.session_state:
    st.session_state.show_booking = False
if "current_providers" not in st.session_state:
    st.session_state.current_providers = []

# ── HEADER ────────────────────────────────────────────────────────
st.markdown("""
<div class="hm-header">
    <h1>🏥 HealthMate</h1>
    <p>AI-Powered Health Navigation · Grounded in Clinical Guidelines · May 2026</p>
</div>
""", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    api_key = st.text_input(
        "Anthropic API Key",
        value=os.environ.get("ANTHROPIC_API_KEY", ""),
        type="password",
        help="Get your key at console.anthropic.com"
    )
    st.markdown("---")
    st.markdown("### 📋 Quick Demos")
    st.markdown("Click to load a demo scenario:")

    demo_scenarios = {
        "🔴 Chest Pain (Emergency)": "I have chest tightness and trouble breathing. Started 20 minutes ago.",
        "💊 UTI Symptoms": "Burning when I pee, going very frequently. 28F, not pregnant, no fever.",
        "🔬 Suspicious Mole": "Mole on my back has changed shape and color over 2 months. I have fair skin, work outdoors.",
        "👶 Infant Fever": "My 7-week-old baby has a fever of 38.3°C. She weighs 4.5kg.",
        "🤰 UTI in Pregnancy": "14 weeks pregnant, burning urination and frequency. No fever. Can I take AZO?",
        "🧠 Low Mood": "Feeling down for 3 weeks, low energy, not enjoying things. No thoughts of harm.",
        "🦵 Ankle Sprain": "Rolled my ankle an hour ago, swollen and bruised. Can limp on it. No numbness.",
        "🔥 Heartburn": "Burning in chest after dinner almost every night for 3 weeks. 35M, gained weight recently.",
        "😷 Sore Throat": "Severe sore throat, fever 101.5, white patches on tonsils, no cough.",
        "🏋️ Back Pain": "Threw out my back at gym this morning. Sharp lower back pain. No leg numbness, no bladder issues.",
    }

    for label, scenario in demo_scenarios.items():
        if st.button(label, use_container_width=True):
            st.session_state.prefill = scenario

    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown("""
**HealthMate** is an AI health navigation platform grounded in:
- AAD, CDC, IDSA, ACP guidelines
- FDA DailyMed drug labels
- USPSTF preventive care recommendations

**Not for clinical use.** Physician validation in progress.

*HealthMate Inc. · Pre-Seed 2026*
    """)

    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.show_booking = False
        st.session_state.current_providers = []
        st.rerun()

# ── MAIN CHAT INTERFACE ───────────────────────────────────────────

# Display conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🏥"):
        st.markdown(msg["content"])

# Pre-fill from sidebar demo button
prefill_value = st.session_state.pop("prefill", "")

# Chat input
user_input = st.chat_input(
    "Describe your symptoms... (e.g. 'burning when I pee, going frequently, no fever')",
    key="main_input",
)

# Use prefill if no direct input
if prefill_value and not user_input:
    user_input = prefill_value

if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)

    # ── STEP 1: Emergency Check ───────────────────────────────────
    is_emergency, emergency_msg, emergency_type = check_emergency(user_input)

    if is_emergency:
        if emergency_type == "CRISIS":
            emergency_content = f"""## 🔴 Crisis Support Available Right Now

{emergency_msg}

**Please reach out immediately:**

📞 **988 Suicide & Crisis Lifeline** — Call or text **988** (24/7, free, confidential)

💬 **Crisis Text Line** — Text **HOME** to **741741**

🚨 **Emergency** — Call **911** if you are in immediate danger

---
You don't have to face this alone. These services are here for you right now.

*HealthMate's clinical safety system detected a potential crisis situation. No AI response was generated — you are being connected to crisis resources directly.*"""
        else:
            emergency_content = f"""## 🚨 Emergency — Call 911 Now

{emergency_msg}

**Do not wait. Do not drive yourself.**

🚨 **Call 911 immediately** or have someone drive you to the nearest emergency room.

{"If you have an EpiPen, use it NOW, then call 911." if emergency_type == "ANAPHYLAXIS" else ""}
{"Note the exact time symptoms started — critical for stroke treatment." if emergency_type == "STROKE" else ""}
{"Chew (don't swallow) one 325mg aspirin while waiting IF you are not allergic." if emergency_type == "CARDIAC" else ""}

---
*This emergency alert was generated by HealthMate's hard-coded safety rules engine — no AI was involved. Clinical authority: AHA/ACC Emergency Guidelines 2023.*"""

        st.session_state.messages.append({"role": "assistant", "content": emergency_content})
        with st.chat_message("assistant", avatar="🏥"):
            if emergency_type == "CRISIS":
                st.warning(emergency_content)
            else:
                st.error(emergency_content)
            if emergency_type != "CRISIS":
                col1, col2 = st.columns(2)
                with col1:
                    st.link_button("🚨 Call 911", "tel:911", use_container_width=True)
                with col2:
                    st.link_button("🏥 Find Nearest ER", "https://www.google.com/maps/search/emergency+room+near+me", use_container_width=True)
            else:
                col1, col2 = st.columns(2)
                with col1:
                    st.link_button("📞 Call 988", "tel:988", use_container_width=True)
                with col2:
                    st.link_button("💬 Crisis Text Line", "sms:741741?body=HOME", use_container_width=True)

    else:
        # ── STEP 2: AI Triage ─────────────────────────────────────
        if not api_key:
            st.error("Please enter your Anthropic API key in the sidebar to get a real response.")
            st.info("👈 Enter your API key in the sidebar. Get one free at console.anthropic.com")
        else:
            with st.chat_message("assistant", avatar="🏥"):
                with st.spinner("Analyzing your symptoms against clinical guidelines..."):

                    # Get relevant guidelines
                    guidelines = get_guidelines(user_input)

                    # Build messages for Claude
                    messages_for_claude = []
                    for msg in st.session_state.messages[:-1]:  # exclude current user msg
                        messages_for_claude.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
                    messages_for_claude.append({
                        "role": "user",
                        "content": f"Patient query: {user_input}\n\nRelevant clinical guidelines:\n{guidelines}"
                    })

                    try:
                        import anthropic
                        client = anthropic.Anthropic(api_key=api_key)

                        response = client.messages.create(
                            model="claude-sonnet-4-6",
                            max_tokens=1000,
                            system=SYSTEM_PROMPT,
                            messages=messages_for_claude,
                        )

                        response_text = response.content[0].text
                        input_tokens = response.usage.input_tokens
                        output_tokens = response.usage.output_tokens
                        cost = (input_tokens * 0.000003) + (output_tokens * 0.000015)

                        # Determine urgency for UI
                        if "URGENCY: URGENT" in response_text:
                            urgency_badge = '<span class="badge-red">🔴 URGENT — See Physician Today</span>'
                            show_booking = True
                        elif "URGENCY: YELLOW" in response_text:
                            urgency_badge = '<span class="badge-yellow">🟡 YELLOW — See Physician in 2-3 Days</span>'
                            show_booking = True
                        else:
                            urgency_badge = '<span class="badge-green">🟢 GREEN — Self-Care Appropriate</span>'
                            show_booking = "physician" in response_text.lower()

                        # Display urgency badge
                        st.markdown(urgency_badge, unsafe_allow_html=True)
                        st.markdown("---")

                        # Clean up response for display (remove URGENCY line)
                        display_text = response_text.replace("URGENCY: URGENT", "").replace(
                            "URGENCY: YELLOW", "").replace("URGENCY: GREEN", "").strip()

                        st.markdown(display_text)

                        # Token cost info (collapsible)
                        with st.expander(f"📊 Session stats — ${cost:.4f} cost", expanded=False):
                            col1, col2, col3 = st.columns(3)
                            col1.metric("Input tokens", f"{input_tokens:,}")
                            col2.metric("Output tokens", f"{output_tokens:,}")
                            col3.metric("Cost", f"${cost:.4f}")
                            st.caption("Based on Claude Sonnet 4.6 pricing — $3/$15 per MTok")

                        # Store response
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response_text
                        })
                        st.session_state.session_count += 1

                        # Set up booking if needed
                        if show_booking:
                            st.session_state.show_booking = True
                            st.session_state.current_providers = get_providers(response_text, user_input)

                    except Exception as e:
                        error_msg = str(e)
                        if "authentication" in error_msg.lower() or "api_key" in error_msg.lower():
                            st.error("Invalid API key. Please check your Anthropic API key in the sidebar.")
                        else:
                            st.error(f"Error calling Claude API: {error_msg}")

    # ── STEP 3: Booking Section ───────────────────────────────────
    if st.session_state.show_booking and st.session_state.current_providers:
        st.markdown("---")
        st.markdown("### 📅 Available In-Network Providers")
        st.caption("Verifying insurance... ✅ Coverage confirmed")

        for provider in st.session_state.current_providers:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.markdown(f"**{provider['name']}**")
                    st.caption(f"{provider['specialty']} · {provider['distance']}")
                with col2:
                    st.markdown(f"🕐 **{provider['available']}**")
                    st.caption(f"{provider['network']} · Est. {provider['copay']} copay")
                with col3:
                    st.button(
                        "Book",
                        key=f"book_{provider['name']}",
                        help="Demo only — no real booking made",
                        use_container_width=True,
                    )
                st.markdown("---")

        st.caption("*Demo only — booking simulation. Real version connects to Zocdoc + Availity API.*")

# ── FOOTER DISCLAIMER ─────────────────────────────────────────────
st.markdown("""
<div class="disclaimer">
⚕️ <strong>Medical Disclaimer:</strong> HealthMate provides health information based on published clinical guidelines for educational purposes only. It does not provide medical advice, diagnosis, or treatment. Always consult a qualified healthcare professional for medical decisions. In an emergency, call 911 immediately.
<br><br>
🔒 <strong>Privacy:</strong> This demo does not store any personal health information. No data is retained after your session ends.
<br><br>
📋 <strong>Clinical Sources:</strong> AAD · CDC · IDSA · ACP · AGA · ACG · USPSTF · FDA DailyMed · AAP · SAMHSA · AHA/ACC
</div>
""", unsafe_allow_html=True)
