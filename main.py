from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from models.database import get_db, Survey, Response, PersonalHealthData, CycleHistory
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Women's Health Survey")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

from models.database import init_db
init_db()


questions_data = [
    {"role": "nurse", "text": "What are the most common women's health issues you see in your clinic/daily work?", "description": "Look for: PCOS, menstrual disorders, anxiety, harassment cases", "type": "checkbox", "options": ["PCOS", "Menstrual disorders", "Anxiety/Depression", "Physical Harassment", "UTIs", "Vaginal Infections"]},
    {"role": "nurse", "text": "How do patients currently track their menstrual cycles or mood? Do they use apps?", "description": "Look for: Existing tools (Flo, Clue, paper), accuracy issues", "type": "radio", "options": ["Flo", "Clue", "Paper/Journal", "Memory", "Never track"]},
    {"role": "nurse", "text": "How often do you encounter patients who feel ashamed to discuss reproductive issues?", "description": "Stigma Assessment: Understanding cultural barriers in clinics.", "type": "radio", "options": ["Every patient", "Most patients", "Some patients", "Rarely"]},
    {"role": "nurse", "text": "Do patients often bring family members into consultation? How does it affect their openness?", "description": "Privacy context: Understanding the environment where health info is shared.", "type": "text"},
    {"role": "nurse", "text": "What information do patients usually miss or misunderstand about their cycle/emotions?", "description": "Look for: Knowledge gaps (ovulation, fertile window, PCOS signs)", "type": "text"},
    {"role": "nurse", "text": "Have you seen cases where a woman's emotional distress went unnoticed until it became serious?", "description": "Look for: Need for AI emotion monitoring, early warning signs", "type": "radio", "options": ["Yes, frequently", "Sometimes", "Rarely", "Never"]},
    {"role": "nurse", "text": "In emergencies, what barriers do women face when trying to get help?", "description": "Look for: SOS feature needs, location sharing, contact alerts", "type": "checkbox", "options": ["Fear of judgement", "No phone access", "Lack of information", "Slow police response", "Geographic distance"]},
    {"role": "nurse", "text": "What would make a wellness app trustworthy for you to recommend to patients?", "description": "Look for: Privacy concerns, medical accuracy, data security", "type": "checkbox", "options": ["Strict privacy policy", "Verified medical content", "Endorsement by hospitals", "Easy data sharing with doctors"]},
    {"role": "nurse", "text": "If an app could alert you when a patient is in distress, would you find it helpful?", "description": "Look for: AI emotion alert feature, professional integration", "type": "radio", "options": ["Yes", "Only with consent", "No, too much liability"]},
    {"role": "nurse", "text": "What is the biggest challenge in explaining PCOS or hormonal imbalances to patients?", "description": "Communication gap: Helps guide the app's simplified tone.", "type": "text"},
    {"role": "nurse", "text": "Do you feel patients would prefer interacting with a female AI bot for reproductive issues?", "description": "Gender preference in AI: Testing if female-voiced bots improve trust.", "type": "radio", "options": ["Yes, strongly", "Maybe", "No, gender doesn't matter"]},
    {"role": "nurse", "text": "How many minutes on average do you spend educating a patient on menstrual hygiene?", "description": "Time constraint analysis: Seeing if the app can save nurse workload.", "type": "radio", "options": ["< 5 mins", "5-10 mins", "10-20 mins", "More than 20 mins"]},
    {"role": "nurse", "text": "What is the most common reason patients skip follow-up appointments?", "description": "Follow-up retention: Designing better app reminders.", "type": "checkbox", "options": ["Distance", "Cost", "Forgetfulness", "Stigma", "Recovered already"]},
    {"role": "nurse", "text": "Would a 'Digital Referral' system from app to your clinic be useful?", "description": "Eco-system integration: Connecting users to physical clinics.", "type": "radio", "options": ["Yes", "Maybe", "No"]},
    {"role": "doctor", "text": "What menstrual health data is most important for accurate cycle prediction?", "description": "Look for: BBT, minHR, symptoms, cycle length (validates LSTM approach)", "type": "checkbox", "options": ["Basal Body Temp (BBT)", "Resting Heart Rate (minHR)", "Symptoms", "Cycle length history", "Cervical mucus"]},
    {"role": "doctor", "text": "How accurate are current period tracker apps for irregular cycles in your experience?", "description": "Look for: Limitations of calendar-based methods (supports ML upgrade)", "type": "radio", "options": ["Very accurate", "Somewhat accurate", "Not accurate", "I don't know"]},
    {"role": "doctor", "text": "What emotional/mental health signs should trigger concern in young women?", "description": "Look for: Anxiety thresholds, depression red flags (AI emotion alerts)", "type": "checkbox", "options": ["Severe anxiety", "Social withdrawal", "Mood swings", "Suicidal ideation"]},
    {"role": "doctor", "text": "How do you handle 'Data Overload' when a patient brings months of tracking data?", "description": "Visualization: Designing charts that doctors actually want to see.", "type": "radio", "options": ["Helpful", "Too messy", "Ignore it mostly", "Only if summarized by AI"]},
    {"role": "doctor", "text": "What women's safety issues are most urgent in Kathmandu/Nepal today?", "description": "Look for: Local context (harassment zones, transport safety, campus issues)", "type": "checkbox", "options": ["Public transport harassment", "Unsafe streets", "Workplace safety", "Cyber-bullying"]},
    {"role": "doctor", "text": "Should wellness apps include medical warnings (e.g., 'Possible PCOS')?", "description": "Look for: Medical disclaimer needs, liability concerns", "type": "radio", "options": ["Yes, always", "No, causes panic", "Yes, with disclaimers"]},
    {"role": "doctor", "text": "Would you recommend an AI-based emotion monitoring app to patients?", "description": "Look for: Trust in AI, privacy concerns, medical validation needs", "type": "text"},
    {"role": "doctor", "text": "How would you want to receive alerts if a patient seems at risk (anxiety, depression, emergency)?", "description": "Look for: Professional integration, doctor notification feature", "type": "checkbox", "options": ["In-app dashboard", "Email alerts", "Direct SMS", "Professional portal integration"]},
    {"role": "doctor", "text": "What are the ethical implications of an app predicting fertility windows?", "description": "Ethics: Understanding professional boundaries of AI.", "type": "text"},
    {"role": "doctor", "text": "Are you seeing an increase in PCOS cases among urban women in Nepal?", "description": "Epidemiology: Validating the 'Urban PCOS' trend.", "type": "radio", "options": ["Significant increase", "Moderate increase", "No change", "Decrease"]},
    {"role": "doctor", "text": "How often do patients bring misinformation from social media (TikTok/Insta) to clinics?", "description": "Verify Info: Combating 'fake news' with verified app content.", "type": "radio", "options": ["Daily", "Weekly", "Rarely", "Never"]},
    {"role": "doctor", "text": "Would you trust an AI-generated summary of a patient's 30-day symptom log?", "description": "AI Efficiency: Designing high-density data summaries for specialists.", "type": "radio", "options": ["Yes, if accurate", "Maybe as a backup", "No, I'll read raw data"]},
    {"role": "doctor", "text": "What nutritional gaps are most common in women with hormonal imbalances?", "description": "Feature: Adding a 'Nutrition/Diet' tracker to the app.", "type": "checkbox", "options": ["Iron/Anemia", "Vitamin D", "Fiber", "Excess Sugar", "Protein"]},
    {"role": "women18plus", "text": "How do you currently track your periods/mood? Apps, paper, or memory?", "description": "Current tools, frustration points (multiple apps)", "type": "radio", "options": ["Mobile Apps", "Paper Diary", "Memory", "I don't track"]},
    {"role": "women18plus", "text": "What's the most frustrating thing about period tracker apps you've used?", "description": "Inaccurate predictions, premium features, privacy", "type": "checkbox", "options": ["Inaccurate predictions", "Too many ads", "Privacy fears", "No Nepali support"]},
    {"role": "women18plus", "text": "Have you ever felt unsafe in Kathmandu (bus, street, campus)? What did you do?", "description": "SOS feature relevance, real safety scenarios", "type": "text"},
    {"role": "women18plus", "text": "Would you use voice-triggered SOS (say 'SOS' or 'Help') instead of tapping a button?", "description": "Voice SOS preference, false trigger concerns", "type": "radio", "options": ["Yes, safer", "Maybe", "No, button is better"]},
    {"role": "women18plus", "text": "Do you journal about your mood/emotions? How often? In what language (Nepali/English)?", "description": "Journaling feature demand, Nepali language need", "type": "text"},
    {"role": "women18plus", "text": "What emotional wellness features would help you most (breathing, meditation, AI chat)?", "description": "Priority features (breathing > AI chat > meditation)", "type": "checkbox", "options": ["Breathing exercises", "Meditation", "AI wellness chat", "Mood journaling"]},
    {"role": "women18plus", "text": "Would you trust an AI that analyzes your journal entries and suggests 'You seem stressed — try this'?", "description": "AI emotion trust, privacy concerns", "type": "radio", "options": ["Yes, sounds helpful", "Maybe, if private", "No trust in AI"]},
    {"role": "women18plus", "text": "Would you share your emergency location with friends/family if you triggered SOS?", "description": "Location sharing consent, privacy preferences", "type": "radio", "options": ["Yes, always", "Only in high danger", "No, too private"]},
    {"role": "women18plus", "text": "What women's health topics do you want to learn more about (PCOS, cancer, menstrual disorders)?", "description": "Awareness module content priorities", "type": "checkbox", "options": ["PCOS/PCOD", "Cervical Cancer", "Menstrual Disorders", "Mental Health Support"]},
    {"role": "women18plus", "text": "If this app was 100% offline (no internet, data stays on phone), would you trust it more?", "description": "Privacy priorities, offline preference", "type": "radio", "options": ["Yes, trust more", "Doesn't matter", "No, I like cloud sync"]},
    {"role": "women18plus", "text": "If you could share a 'Health Summary' directly with your doctor, would you?", "description": "Interoperability: Sharing data for better checkups.", "type": "radio", "options": ["Yes", "Only if encrypted", "No"]},
    {"role": "women18plus", "text": "Does your period affect your professional performance? How?", "description": "Impact assessment for productivity tips.", "type": "text"},
    {"role": "women18plus", "text": "Have you used Pathao/InDrive? Have you ever felt unsafe during a ride?", "description": "Transport Safety: Integrating ride-sharing safety checks.", "type": "radio", "options": ["Frequently", "Occasionally", "Once", "Never"]},
    {"role": "women18plus", "text": "Do you feel comfortable discussing menstrual health with your male colleagues?", "description": "Taboo Analysis: Workplace culture and support systems.", "type": "radio", "options": ["Very comfortable", "Somewhat", "Uncomfortable", "Absolutely not"]},
    {"role": "under18", "text": "Did your mom/sister teach you about periods? Or did you learn from Google/apps?", "description": "Education gaps, need for awareness content", "type": "radio", "options": ["Family members", "School", "Internet/Apps", "Friends", "Self-taught"]},
    {"role": "under18", "text": "What's the most confusing thing about your period cycle?", "description": "Knowledge gaps (ovulation, fertile window, PCOS)", "type": "checkbox", "options": ["Ovulation", "Fertile Window", "PCOS/PCOD", "Heavy Bleeding", "Irregularity"]},
    {"role": "under18", "text": "Do you feel your mood changes during your period? How does it affect you?", "description": "Mood-period connection, need for tracking", "type": "text"},
    {"role": "under18", "text": "Have you ever felt unsafe at school/bus/home? What happened?", "description": "SOS feature relevance for teens", "type": "text"},
    {"role": "under18", "text": "Would you tell your parents if you triggered an emergency SOS alert? Why/why not?", "description": "Parental notification feature, consent concerns", "type": "text"},
    {"role": "under18", "text": "Would you use an app that guesses your mood from your journal (like 'You seem sad today')?", "description": "AI emotion feature for teens, trust level", "type": "radio", "options": ["Yes, sounds cool", "Maybe", "No, creepy"]},
    {"role": "under18", "text": "What would make you scared to use a period/mood app?", "description": "Privacy fears (parents seeing, data shared)", "type": "checkbox", "options": ["Parents seeing it", "Friends seeing it", "Data being sold", "Hacking"]},
    {"role": "under18", "text": "Would you prefer this app look like a normal app (e.g., calculator) so no one knows it's for periods?", "description": "Discreet UI need, privacy protection", "type": "radio", "options": ["Yes, Calculator icon", "Yes, Game icon", "No, normal icon"]},
    {"role": "under18", "text": "Do you want to learn about PCOS, breast cancer, or cervical cancer? Or is that too old?", "description": "Awareness module age-appropriateness", "type": "checkbox", "options": ["PCOS", "Breast Cancer", "Cervical Cancer", "Too old for me"]},
    {"role": "under18", "text": "If this app was FREE forever (no premium), would you use it more than Flo/Clue?", "description": "Pricing sensitivity, free vs. premium", "type": "radio", "options": ["Yes! Definitely", "Maybe", "No, I like Flo/Clue"]},
    {"role": "under18", "text": "Suppose you had a question you were too shy to ask your mom, would you ask a bot?", "description": "Privacy: Testing the bot as a safe medical 'sister'.", "type": "radio", "options": ["Yes! Definitely", "Maybe", "No, I'd ask a friend"]},
    {"role": "under18", "text": "Have you ever missed school because of your period? What was the reason?", "description": "Understanding 'Period Poverty' or infrastructure issues.", "type": "checkbox", "options": ["Pain", "No clean toilets", "Stigma", "No supply access", "Never"]},
    {"role": "under18", "text": "Would you use an app that gives you 'Reward Points' for tracking daily?", "description": "Gamification: Testing incentives for teenagers.", "type": "radio", "options": ["Yes! Love rewards", "Maybe", "No"]},
    {"role": "under18", "text": "Is 'Anxiety about stained clothes' a major stress during school?", "description": "Stigma: Understanding psychological impacts of period leaks.", "type": "radio", "options": ["Yes, all the time", "Occasionally", "Rarely", "Never"]},
    {"role": "under18", "text": "If the app offered a 'Safe anonymous Chat' with other girls your age, would you join?", "description": "Community: Testing appetite for peer-to-peer support.", "type": "radio", "options": ["Yes! Definitely", "Only if moderated", "No, too risky"]}
]

common_questions = [
    {"role": "all", "text": "Describe your 'Ideal' wellness app in 3 words.", "description": "Quick psychological profiling.", "type": "text"},
    {"role": "all", "text": "What's the ONE feature you'd want most in this app?", "description": "Prioritizing the MVP.", "type": "text"},
    {"role": "all", "text": "Would you trust a Nepali language interface over English?", "description": "Localization: Testing language comfort.", "type": "radio", "options": ["Prefer Nepali", "Use both", "Only English"]},
    {"role": "all", "text": "How much do you value 'Privacy' vs 'Social Sharing'?", "description": "Defining the core app philosophy.", "type": "radio", "options": ["Total Privacy", "Some Sharing", "Open Social"]},
    {"role": "all", "text": "How much would you pay monthly (in NPR)?", "description": "Value assessment in local currency.", "type": "radio", "options": ["Free only", "NPR 50", "NPR 100", "NPR 200+"]},
    {"role": "all", "text": "Would you trust an app developed by a local team in Nepal?", "description": "Trust in local innovation.", "type": "radio", "options": ["Yes, more trust", "Doesn't matter", "Less trust"]},
    {"role": "all", "text": "What would make you delete this app in the first week?", "description": "Retention: Identifying 'Deal-breakers'.", "type": "text"},
    {"role": "all", "text": "How often do you use your phone for health-related searches?", "description": "Digital Literacy: Assessing mobile habits.", "type": "radio", "options": ["Daily", "Weekly", "Monthly", "Never"]},
    {"role": "all", "text": "Would you prefer video content or text content for health tips?", "description": "Content Type: Guiding the media strategy.", "type": "radio", "options": ["Videos", "Articles", "Infographics", "Audio/Podcasts"]},
    {"role": "all", "text": "Rate your trust in 'AI Health Tips' from 1 to 5.", "description": "Trust Metric: Measuring AI skepticism.", "type": "radio", "options": ["1 (Very Low)", "2", "3", "4", "5 (Very High)"]}
]

def get_questions_for_role(role):
    role_questions = [q for q in questions_data if q["role"] == role]
    for cq in common_questions:
        role_questions.append({**cq, "role": role})
    return role_questions


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/survey/{role}", response_class=HTMLResponse)
async def survey(request: Request, role: str):
    valid_roles = ["nurse", "doctor", "women18plus", "under18"]
    if role not in valid_roles:
        raise HTTPException(status_code=404, detail="Invalid role")
    questions = get_questions_for_role(role)
    return templates.TemplateResponse("survey.html", {"request": request, "role": role, "questions": questions})


@app.post("/submit/{role}")
async def submit(request: Request, role: str, db: Session = Depends(get_db)):
    form = await request.form()
    questions = get_questions_for_role(role)
    survey = Survey(role=role)
    db.add(survey)
    db.commit()
    db.refresh(survey)
    for idx, q in enumerate(questions):
        val = form.get(f"q{idx}")
        if val is not None:
            if isinstance(val, str):
                answer = val
            else:
                answer = json.dumps(list(val))
        else:
            answer = ""
        resp = Response(survey_id=survey.id, question_index=idx, question_text=q["text"], answer=answer)
        db.add(resp)
    db.commit()
    return RedirectResponse(url="/thank-you", status_code=303)


@app.get("/thank-you", response_class=HTMLResponse)
async def thank_you(request: Request):
    return templates.TemplateResponse("thank_you.html", {"request": request})


@app.get("/personal-health", response_class=HTMLResponse)
async def personal_health_form(request: Request):
    return templates.TemplateResponse("personal_health.html", {"request": request})


@app.post("/personal-health", response_class=HTMLResponse)
async def submit_personal_health(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    symptoms = form.getlist("symptoms")
    record = PersonalHealthData(
        age=int(form["age"]) if form.get("age") else None,
        height=form.get("height"),
        weight=form.get("weight"),
        stress_level=form.get("stress_level"),
        exercise_frequency=form.get("exercise_frequency"),
        sleep_hours=form.get("sleep_hours"),
        diet=form.get("diet"),
        cycle_start_date=form.get("cycle_start_date"),
        cycle_length=int(form["cycle_length"]) if form.get("cycle_length") else None,
        period_length=int(form["period_length"]) if form.get("period_length") else None,
        symptoms=json.dumps(symptoms) if symptoms else None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    past_dates = form.getlist("past_cycle_start_date")
    past_lengths = form.getlist("past_cycle_length")
    past_periods = form.getlist("past_period_length")

    for i in range(len(past_dates)):
        past_symptoms = form.getlist(f"past_symptoms_{i}")
        db.add(CycleHistory(
            personal_health_id=record.id,
            cycle_start_date=past_dates[i] if i < len(past_dates) else None,
            cycle_length=int(past_lengths[i]) if i < len(past_lengths) and past_lengths[i] else None,
            period_length=int(past_periods[i]) if i < len(past_periods) and past_periods[i] else None,
            symptoms=json.dumps(past_symptoms) if past_symptoms else None,
        ))
    db.commit()
    return RedirectResponse(url="/thank-you", status_code=303)


@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request, db: Session = Depends(get_db)):
    surveys = db.query(Survey).order_by(Survey.created_at.desc()).all()
    data = []
    for s in surveys:
        resps = db.query(Response).filter(Response.survey_id == s.id).all()
        data.append({
            "id": s.id,
            "role": s.role,
            "created_at": s.created_at.strftime("%Y-%m-%d %H:%M"),
            "responses": [(r.question_text, r.answer) for r in resps]
        })
    return templates.TemplateResponse("admin.html", {"request": request, "data": data})
