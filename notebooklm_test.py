import os
import ssl
import httpx
import asyncio

# 1. עקיפת SSL גורפת
ssl._create_default_https_context = ssl._create_unverified_context

_original_init = httpx.AsyncClient.__init__
def patch_async_client_init(self, *args, **kwargs):
    kwargs['verify'] = False
    _original_init(self, *args, **kwargs)

httpx.AsyncClient.__init__ = patch_async_client_init

from notebooklm import NotebookLMClient

async def main():
    print("Connecting to NotebookLM...")
    
    async with await NotebookLMClient.from_storage() as client:
        notebook = await client.notebooks.create("בדיקת חילוץ קולות קוראים")
        print(f"Created Notebook! ID: {notebook.id}")

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
        
        # שמירת הטקסט לקובץ זמני
        temp_file_path = "temp_sample_call.txt"
        with open(temp_file_path, "w", encoding="utf-8") as f:
            f.write(sample_call)

        print("Uploading source file...")
        try:
            # העלאת קובץ במקום add_text
            await client.sources.add_file(notebook.id, file_path=temp_file_path)
            print("Source uploaded successfully!")
        finally:
            # מחיקת הקובץ הזמני
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        await asyncio.sleep(2)

        prompt = """
        אנא נתח את מסמך הקול הקורא המצורף וחלץ ממנו את הפרמטרים הבאים. 
        החזר אך ורק בלוק קוד (Code Block) בפורמט CSV נקי הכולל שורת כותרות (Header) ושורה אחת יחידה של נתונים:

        כותרות העמודות:
        budget,duration_months,max_pi_count,prior_knowledge_required,issuing_unit,target_population,research_tools

        כללים:
        1. budget, duration_months, max_pi_count: מספרים בלבד.
        2. prior_knowledge_required: 1 ל"כן", 0 ל"לא".
        3. עטוף שדות טקסט בעברית במירכאות כפולות (").
        4. החזר רק את בלוק הקוד ללא שום טקסט נוסף.
        """

        print("Sending prompt to NotebookLM...")
        response = await client.chat.ask(notebook.id, prompt)

        print("\n================ התוצאה שהתקבלה ================")
        print(response.text)
        print("==================================================")

if __name__ == "__main__":
    asyncio.run(main())