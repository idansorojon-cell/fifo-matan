# פרומפטים לכלי AI — Runway / Veo / CapCut AI / ElevenLabs Studio

## Runway / Veo (הנפשת screenshot)

**דולג** — לא נלכדו screenshots אמיתיים בהרצה הזו (ראה 07 — capability report),
אז אין תמונות מקור להנפיש. אם ירוצו screenshots אמיתיים בהרצה הבאה, לכל סצנה
ללא וידאו יהיה כאן פרומפט מהצורה:

```
Image-to-video. Input: <screenshot filename>.
Subtle, slow zoom-in toward <element>. Static UI otherwise — no distortion.
Duration: <X> seconds. Style: clean screen-recording, not cinematic.
```

## CapCut AI (הרכבת סרטון מסקריפט)

```
Create a tutorial video from this script and footage.
Footage: (אין footage אמיתי בהרצה הזו — יש להקליט ידנית לפי 07, ואז להזין הנה)
Script: ראה 01-short-version_60-90s.md / 02-full-version_3-5min.md המלאים
Captions: burn in the caption per scene (טור "טקסט על המסך" בכל סצנה)
Voice: ניתן להזין את narration-short.ssml / narration-full.ssml ל-CapCut AI
        ליצירת קריינות אוטומטית בעברית, או להשתמש בקובץ קול מ-ElevenLabs (ראה מטה)
Pacing: לחתוך לפי משכי הסצנות ב-scenes-short.json / scenes-full.json
```

## ElevenLabs Studio (קריינות)

```
Voice: קריין רגוע, בטוח בעצמו, ידידותי. עברית (he-IL).
Input: narration-short.ssml (לגרסה הקצרה) / narration-full.ssml (לגרסה המלאה)
        — יש להזין את קובץ ה-SSML כמות שהוא, לא להעתיק טקסט רגיל, כי תגי
        <break> קובעים את הקצב בין סצנות.
Output: קובץ אודיו רציף אחד, WAV או MP3
```

אם קול ה-Hebrew הזמין ב-ElevenLabs לא נשמע טבעי לסגנון מסוים — זו בעיית בחירת
קול לפתור בתוך הכלי עצמו, לא סיבה לשנות את תסריט הקריינות.
