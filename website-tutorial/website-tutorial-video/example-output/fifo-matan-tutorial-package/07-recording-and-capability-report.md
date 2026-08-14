# דוח יכולות — מה עבד ומה לא (הרצה זו)

**קרא את זה קודם** — זה אומר לך אם אתה מחזיק סרטון כמעט-מוכן, או תסריט
שעדיין צריך להקליט.

| יכולת | סטטוס | פירוט |
|---|---|---|
| Screenshots | ⚠️ חלקי | נוטה בפועל בכלי preview מקומי (session אמיתי, login מלא), אך לא נשמרו קבצים לדיסק בהרצה הזו — מגבלה של כלי הבדיקה הספציפי, לא עקרונית. עם Playwright מותקן (`pip install playwright && playwright install chromium`) ו-`scripts/capture_screens.py`, זה יעבוד ישירות לדיסק. |
| וידאו אמיתי (Playwright) | ❌ לא זמין | Playwright Python מותקן, אבל בינארי Chromium לא הותקן בהרצה הזו (`playwright install chromium` לא רץ). |
| GIF מונפש (claude-in-chrome) | ❌ לא זמין | תוסף ה-Chrome לא היה מחובר בזמן ההרצה. |
| SRT (כתוביות) | ✅ הצליח | `captions-short.he.srt` (10 סצנות, ~72 שנ') ו-`captions-full.he.srt` (24 סצנות, ~189 שנ') — נוצרו ישירות מ-scenes.json |
| SSML (קריינות ל-TTS) | ✅ הצליח | `narration-short.ssml` ו-`narration-full.ssml` — מוכנים להזנה ישירה ל-ElevenLabs/Polly/Google TTS |
| פרומפטים ל-AI tools | ✅ הצליח (עם דילוג חלקי) | `06-ai-tool-prompts.md` — Runway/Veo דולג (אין screenshots להנפיש), CapCut AI ו-ElevenLabs מלאים |

## מה זה אומר בפועל

אין עדיין וידאו מוכן. יש: תסריט מלא סצנה-סצנה (01/02), כתוביות מוכנות (SRT),
וקובץ קריינות מוכן להזנה ל-TTS (SSML). כדי לקבל סרטון בפועל — צריך להקליט
בעצמך (ראה למטה) ואז לשלב את הכתוביות/הקריינות שכבר מוכנים.

## הקלטה ידנית (Loom / Screen Studio / OBS)

### Loom
1. פתח Loom, בחר "Screen Only", בחר את הטאב עם האתר
2. הקלט, עקוב אחרי 01 או 02 סצנה-סצנה
3. עצור, גזור זמן מת בעורך המובנה

### Screen Studio (Mac)
1. בחר את חלון הדפדפן
2. מזום אוטומטית על קליקים — טוב לזום על התגיות (סצנה 12-14 בגרסה המלאה)
3. ייצוא ב-1080p+

### OBS Studio
1. Display/Window Capture על הדפדפן, 1920x1080 לפחות
2. הקלט, עצור, גזור עם QuickTime/עורך פשוט

לאחר ההקלטה: ייבא את `captions-short.he.srt`/`captions-full.he.srt` לעורך
הווידאו (רוב העורכים תומכים ב-SRT ישירות), והזן את קובץ ה-SSML המתאים
ל-ElevenLabs (או כלי TTS אחר) לקבלת קריינות — או הקלט קריינות אנושית לפי
הטקסט ב-01/02.
