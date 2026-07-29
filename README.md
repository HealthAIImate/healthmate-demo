# HealthMate — AI Health Navigation Demo

## Run Locally (2 minutes)

```bash
# 1. Install dependencies
pip install streamlit anthropic

# 2. Set your API key
export ANTHROPIC_API_KEY=sk-ant-your-key-here

# 3. Run the app
streamlit run app.py
```

Opens at http://localhost:8501

## Deploy to Streamlit Cloud (Free — share with anyone)

1. Push this folder to GitHub (free account)
2. Go to share.streamlit.io
3. Click "New app" → connect your GitHub repo
4. Set `app.py` as the main file
5. Add secret: `ANTHROPIC_API_KEY = "sk-ant-your-key"`
6. Click Deploy → get a public URL in 2 minutes

## Demo Scenarios (click in sidebar)

- 🔴 Chest Pain → emergency rules engine fires instantly
- 💊 UTI → exact AZO dosing + same-day booking
- 👶 Infant Fever → ER_NOW regardless of how baby looks
- 🤰 UTI in Pregnancy → refuses OTC, books OB-GYN today
- 🔬 Suspicious Mole → ABCDE rule → urgent derm referral
- 🧠 Low Mood → PHQ screening → therapy booking
- 🦵 Ankle Sprain → Ottawa Rules → PRICE protocol
- 🔥 Heartburn → GERD algorithm → OTC PPI exact dosing
- 😷 Sore Throat → Centor criteria → antibiotic stewardship
- 🏋️ Back Pain → ACP guidelines → no unnecessary imaging

## Cost

Each triage session costs < $0.01 using Claude Sonnet 4.6.
100 demo sessions = under $1.

## Clinical Note

For physician validation only. Not HIPAA-compliant. No PHI stored.
CMO-Derm sign-off required before any real patient use.
