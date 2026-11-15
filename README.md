# 💰 Moliyachim AI — Shaxsiy Moliya Telegram Boti

Foydalanuvchilarning shaxsiy xarajat va daromadlarini **10–30 soniyalik o'zbekcha ovozli xabarlar** yoki **oddiy matnlar** orqali avtomatik tahlil qiluvchi, haftalik va oylik eslatmalar yuboruvchi, hamda sun'iy intellekt orqali moliyaviy maslahat beruvchi Telegram bot.

---

## 🚀 Texnologiyalar (Tech Stack)

- **Til:** Python 3.11+
- **Telegram Bot Framework:** `aiogram` 3.x
- **Web Framework:** `FastAPI`
- **Ovozni tahlil qilish (Multimodal AI):** `Google Gemini 2.5 Flash` (`google-genai` SDK)
- **Matn va tezkor moliya tahlili:** `Groq API` (`qwen/qwen3.8-27b`)
- **Ma'lumotlar bazasi:** `Firebase Firestore` (`firebase-admin`)
- **Serverless Deploy:** `Vercel` (Webhooks & Vercel Crons)

---

## ✨ Asosiy Imkoniyatlar

1. 🎙 **Ovozli xabarlar orqali xarajatlarni kiritish:**
   - Foydalanuvchi bir ovozli xabarda bir nechta xarajat va daromadlarni aytishi mumkin:
     *«Tushlikka 45 ming ketdi, taksiga 15 ming berdim, oylikdan 2 million oldim»*
   - Gemini barcha operatsiyalarni toifasi, summasi va tavsifi bilan aniq ajratib beradi.
2. ✍️ **Tezkor matnli kiritish:**
   - Masalan: *«non 5000, go'sht 120 ming, benzin 100000»*
3. 🧠 **Interaktiv AI Moliyaviy Maslahatchi:**
   - Foydalanuvchi botga bemalol moliyaviy savollar berishi mumkin:
     *«Bu oy eng ko'p nimaga pul ishlatdim?»*
     *«Qanday qilib pul tejashim mumkin?»*
     *«Xarajatlarimni tahlil qilib ber»*
4. ⏰ **Haftalik va Oylik Avtomatik Eslatmalar (Hooks):**
   - **Har yakshanba soat 20:00 da:** Haftalik hisobot va qiziqarli eslatmalar (*«Bu hafta nima gap? Nega pul qo'shmayapsan?»*).
   - **Har oy oxirida soat 21:00 da:** To'liq oylik sarhisob va kelgusi oy budjet maslahati.
5. 🗑 **Xatolikni bekor qilish:**
   - Har bir qo'shilgan xarajat ostida `[🗑 O'chirish]` inline tugmasi yoki `/delete_last` buyrug'i.

---

## 🛠 Mahalliy Ishga Tushirish (Local Run)

1. Virtual muhitni faollashtiring:
```bash
source .venv/bin/activate
```

2. Kerakli paketlarni o'rnating:
```bash
pip install -r requirements.txt
```

3. Botni ishga tushiring:
```bash
python3 main.py
```

Telegramda botingiz username-iga (`@my_moliyachimbot`) kiring va `/start` bosing!

---

## ☁️ Vercel-ga Joylash (Deployment)

1. Vercel CLI o'rnating yoki GitHub orqali ulang:
```bash
vercel
```
2. Vercel Environment Variables sozlamalariga quyidagilarni kiriting:
   - `TELEGRAM_BOT_TOKEN`
   - `GEMINI_API_KEY`
   - `GROQ_API_KEY`
   - `FIREBASE_SERVICE_ACCOUNT_JSON` (service account JSON faylining to'liq matni)
   - `WEBHOOK_URL` (masalan: `https://sizning-loyiha.vercel.app`)
   - `WEBHOOK_SECRET`
3. Webhookni o'rnatish uchun brauzerda oching:
```
https://sizning-loyiha.vercel.app/api/set_webhook?url=https://sizning-loyiha.vercel.app
```
