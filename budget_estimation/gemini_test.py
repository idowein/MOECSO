import ssl
import httpx

# עקיפת בדיקת SSL עבור רשתות ארגוניות
ssl._create_default_https_context = ssl._create_unverified_context
_original_init = httpx.Client.__init__
def patch_client_init(self, *args, **kwargs):
    kwargs['verify'] = False
    _original_init(self, *args, **kwargs)
httpx.Client.__init__ = patch_client_init

from google import genai

# הדבק כאן את המפתח שהנפקת ב-AI Studio
API_KEY = "AIzaSy..." 

client = genai.Client(api_key=API_KEY)

sample_call = """
קול קורא למחקר: שילוב כלי בינה מלאכותית בלמידה עצמאית
מזמין: לשכת המדען הראשי, משרד החינוך
תקציב מרבי: 220,000 ש"ח
משך המחקר: 18 חודשים
צוות מחקר: עד 3 חוקרים ראשיים בדרגת ד"ר או סגל פנים.
כלי מחקר: שאלונים מקוונים, ראיונות עומק ותצפיות בכיתות.
אוכלוסיית יעד: תלמידים ומורים בחטיבות הביניים.
דרישת פיילוט: כן.
"""

prompt = f"""
נתח את הקול הקורא הבא וחלץ ממנו את הפרמטרים הבאים.
החזר אך ורק בלוק קוד (Code Block) בפורמט CSV נקי הכולל שורת כותרות ושורה אחת של נתונים:

budget,duration_months,max_pi_count,prior_knowledge_required,issuing_unit,target_population,research_tools

כללים:
1. budget, duration_months, max_pi_count: מספרים בלבד.
2. prior_knowledge_required: 1 ל"כן", 0 ל"לא".
3. עטוף שדות טקסט בעברית במירכאות כפולות (").

טקסט הקול הקורא:
{sample_call}
"""

print("Sending request to Gemini API...")
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=prompt,
)

print("\n================ התוצאה שהתקבלה ================")
print(response.text)
print("==================================================")