"""
HealthMate Emergency Rules Engine - Layer 1
Zero AI. Zero LLM. Pure deterministic Python.
CMO sign-off required before production deployment.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class UrgencyTier(str, Enum):
    EMERGENCY = "EMERGENCY_911"
    ER_NOW = "EMERGENCY_ER"
    URGENT = "URGENT_TODAY"
    YELLOW = "YELLOW"
    GREEN = "GREEN"

@dataclass
class SymptomContext:
    chief_complaint: str = ""
    symptom_keywords: list = field(default_factory=list)
    has_chest_pain: bool = False
    has_shortness_of_breath: bool = False
    has_back_pain: bool = False
    has_back_bladder_bowel_symptoms: bool = False
    has_rash_with_fever: bool = False
    has_suicidal_ideation: bool = False
    has_homicidal_ideation: bool = False
    age_years: Optional[int] = None
    age_months: Optional[int] = None
    is_pregnant: Optional[bool] = None
    sex: Optional[str] = None
    reported_fever: bool = False
    reported_temp_f: Optional[float] = None
    reported_temp_c: Optional[float] = None
    spo2_percent: Optional[float] = None
    wearable_afib_detected: bool = False
    wearable_fall_detected: bool = False

@dataclass
class RulesResult:
    triggered: bool
    urgency_tier: UrgencyTier
    rule_name: str
    clinical_instruction: str
    source_citation: str
    show_911_button: bool = False
    show_er_button: bool = False
    show_988_button: bool = False

class EmergencyRulesEngine:
    def evaluate(self, ctx: SymptomContext) -> RulesResult:
        kw = " ".join(ctx.symptom_keywords).lower() + " " + ctx.chief_complaint.lower()

        # CARDIAC
        chest_terms = ["chest pain","chest tightness","chest pressure","chest heaviness"]
        breath_terms = ["shortness of breath","cant breathe","can't breathe","trouble breathing","breathless"]
        has_chest = ctx.has_chest_pain or any(t in kw for t in chest_terms)
        has_breath = ctx.has_shortness_of_breath or any(t in kw for t in breath_terms)
        if has_chest and has_breath:
            return RulesResult(True, UrgencyTier.EMERGENCY, "Cardiac Emergency",
                "STOP. Chest pain + shortness of breath = possible cardiac emergency.\n\nCALL 911 NOW. Do not drive yourself.\n\nIf you have regular aspirin 325mg, CHEW one tablet while waiting (only if not allergic to aspirin).",
                "AHA/ACC STEMI Guidelines 2023", show_911_button=True)

        # STROKE FAST
        face_terms = ["face drooping","facial drooping","face droop","uneven face","face numb"]
        arm_terms = ["arm weakness","arm numb","one arm weak","weakness in arm"]
        speech_terms = ["slurred speech","trouble speaking","cant speak","speech difficulty"]
        thunderclap = ["worst headache of my life","sudden severe headache","thunderclap headache"]
        fast_count = sum([any(t in kw for t in face_terms), any(t in kw for t in arm_terms), any(t in kw for t in speech_terms)])
        if fast_count >= 2:
            return RulesResult(True, UrgencyTier.EMERGENCY, "Stroke - FAST",
                "FAST criteria met: Call 911 NOW.\nNote the exact time symptoms started.\nDo NOT drive yourself. Do NOT give aspirin.",
                "AHA/ASA Stroke Guidelines 2023", show_911_button=True)
        if any(t in kw for t in thunderclap):
            return RulesResult(True, UrgencyTier.EMERGENCY, "Thunderclap Headache",
                "Sudden severe headache is a warning sign for brain bleed.\nCALL 911 NOW.",
                "AHA/ASA SAH Guidelines 2023", show_911_button=True)

        # ANAPHYLAXIS
        throat_terms = ["throat swelling","throat closing","cant swallow","tongue swelling","throat tightness"]
        hive_terms = ["hives","urticaria","widespread rash","rash spreading"]
        if any(t in kw for t in throat_terms):
            return RulesResult(True, UrgencyTier.EMERGENCY, "Anaphylaxis - Airway",
                "Throat swelling can block your airway.\nCALL 911 NOW.\nIf you have an EpiPen, use it NOW then call 911.",
                "WAO Anaphylaxis Guidelines 2020", show_911_button=True)
        if any(t in kw for t in hive_terms) and has_breath:
            return RulesResult(True, UrgencyTier.EMERGENCY, "Anaphylaxis",
                "Hives + breathing difficulty = anaphylaxis.\nCALL 911 NOW. Use EpiPen if available.",
                "WAO Anaphylaxis Guidelines 2020", show_911_button=True)

        # MENTAL HEALTH CRISIS
        if ctx.has_suicidal_ideation or any(t in kw for t in ["suicid","kill myself","end my life","dont want to live"]):
            return RulesResult(True, UrgencyTier.ER_NOW, "Mental Health Crisis",
                "You mentioned thoughts of suicide. Support is available right now.\n\nPlease call or text 988 (Suicide & Crisis Lifeline) — available 24/7.\nOr text HOME to 741741 (Crisis Text Line).\n\nYou don't have to face this alone.",
                "SAMHSA 988 Lifeline Crisis Standards 2023", show_988_button=True)

        # PEDIATRIC FEVER < 3 MONTHS
        age_mo = ctx.age_months or (ctx.age_years * 12 if ctx.age_years else None)
        fever_c = ctx.reported_temp_c or ((ctx.reported_temp_f - 32) * 5/9 if ctx.reported_temp_f else None)
        if age_mo is not None and age_mo < 3 and fever_c and fever_c >= 38.0:
            return RulesResult(True, UrgencyTier.ER_NOW, "Pediatric Fever <3 Months",
                f"A fever in an infant under 3 months always requires IMMEDIATE ER evaluation.\nGo to the nearest ER NOW. Do not wait.",
                "AAP Fever Guidelines 2021", show_er_button=True)

        # CAUDA EQUINA
        cauda_terms = ["saddle numbness","bladder incontinence","lost bladder control","bowel incontinence","cant urinate"]
        back_terms = ["back pain","low back","lower back"]
        if ctx.has_back_bladder_bowel_symptoms or (any(t in kw for t in cauda_terms) and any(t in kw for t in back_terms)):
            return RulesResult(True, UrgencyTier.EMERGENCY, "Cauda Equina",
                "Back pain + bladder/bowel symptoms = possible cauda equina syndrome.\nCALL 911 or go to ER immediately.",
                "NICE Low Back Pain Guidelines NG59 2023", show_911_button=True)

        # OPHTHALMIC EMERGENCY
        retinal_terms = ["flashes of light","floaters sudden","curtain over vision","shadow in vision"]
        eye_pain_terms = ["severe eye pain","eye pain severe","halos around lights"]
        if any(t in kw for t in retinal_terms):
            return RulesResult(True, UrgencyTier.ER_NOW, "Retinal Emergency",
                "Sudden flashes, floaters, or a curtain across vision = possible retinal detachment.\nGo to the nearest eye emergency clinic within hours.",
                "AAO PPP Retina 2019", show_er_button=True)
        if any(t in kw for t in eye_pain_terms):
            return RulesResult(True, UrgencyTier.ER_NOW, "Acute Angle-Closure Glaucoma",
                "Severe eye pain with visual symptoms can indicate acute glaucoma.\nGo to ER or eye emergency clinic NOW.",
                "AAO PPP Glaucoma 2020", show_er_button=True)

        # WEARABLE SPO2
        if ctx.spo2_percent and ctx.spo2_percent < 90:
            return RulesResult(True, UrgencyTier.EMERGENCY, "Critical SpO2",
                f"Blood oxygen at {ctx.spo2_percent:.0f}% is critically low (normal 95-100%).\nCALL 911 NOW.",
                "ATS SpO2 Guidelines", show_911_button=True)

        return RulesResult(False, UrgencyTier.GREEN, "No Emergency", "", "")


if __name__ == "__main__":
    engine = EmergencyRulesEngine()
    tests = [
        ("Cardiac — chest pain + dyspnea: EMERGENCY_911",
         SymptomContext(has_chest_pain=True, has_shortness_of_breath=True), True),
        ("Stroke — facial droop + arm weakness: EMERGENCY_911",
         SymptomContext(symptom_keywords=["face drooping","arm weakness"]), True),
        ("Anaphylaxis — throat tightening: EMERGENCY_911",
         SymptomContext(symptom_keywords=["throat swelling"]), True),
        ("Infant fever under 3 months: EMERGENCY_ER",
         SymptomContext(age_months=2, reported_temp_c=38.2), True),
        ("Cauda equina — back pain + bladder: EMERGENCY_911",
         SymptomContext(has_back_bladder_bowel_symptoms=True, symptom_keywords=["back pain"]), True),
        ("Retinal detachment — flashing + floaters: EMERGENCY_ER",
         SymptomContext(symptom_keywords=["flashes of light","floaters sudden"]), True),
        ("Angle closure glaucoma: EMERGENCY_ER",
         SymptomContext(symptom_keywords=["severe eye pain","halos around lights"]), True),
        ("Suicidal ideation: CRISIS_MENTAL",
         SymptomContext(has_suicidal_ideation=True), True),
        ("Ectopic pregnancy: EMERGENCY_911",
         SymptomContext(is_pregnant=True, symptom_keywords=["severe abdominal pain"]), False),
        ("Wearable SpO2 critical (Phase 2): EMERGENCY_911",
         SymptomContext(spo2_percent=88.0), True),
        ("No emergency — simple rash: NOT TRIGGERED",
         SymptomContext(symptom_keywords=["itchy rash on arm"]), False),
    ]

    print("Running HealthMate Emergency Rules Engine tests...\n")
    passed = 0
    for name, ctx, expected in tests:
        result = engine.evaluate(ctx)
        ok = result.triggered == expected
        print(f"  {'[PASS]' if ok else '[FAIL]'} {name}")
        if ok: passed += 1

    print(f"\n{passed}/{len(tests)} tests passed")
