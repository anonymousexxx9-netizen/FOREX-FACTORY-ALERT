# Forex High-Impact Alert Bot (Telegram)

Bot Telegram yang memantau **Economic Calendar Forex Factory**, dan hanya mengirim alert untuk event **High Impact**. Setiap kali data dirilis, bot otomatis mengirim:

1. **Alert hasil rilis** — actual vs forecast vs previous.
2. **Bias instan (rule-based)** — bullish/bearish/netral, dihitung otomatis dari angka actual vs forecast (gratis, tanpa API key).
3. **Analisa market AI** — narasi analisa dari Claude (atau GPT) tentang dampak ke pasar hari itu, pair yang perlu diperhatikan, dan hal yang perlu diwaspadai.

Setiap pagi (jam yang bisa diatur), bot juga mengirim **agenda harian**: daftar semua event high-impact yang terjadwal hari itu.

## Struktur Project

```
forex-alert-bot/
├── main.py                          # entry point, jalan sekali setiap kali dipanggil cron
├── bot/
│   ├── config.py                    # baca semua setting dari environment variable
│   ├── calendar_fetcher.py          # ambil & filter data dari feed Forex Factory
│   ├── analyzer.py                  # bias rule-based + analisa AI
│   ├── telegram_sender.py           # kirim pesan ke Telegram + format pesan
│   └── state.py                     # simpan riwayat alert (anti-duplikat)
├── test_offline.py                  # test logika pakai data palsu, tanpa internet/credential asli
├── state.json                       # riwayat alert (auto-update, jangan diedit manual)
├── requirements.txt
├── .env.example
└── .github/workflows/forex_alert.yml  # jadwal otomatis (GitHub Actions, GRATIS)
```

## 1. Buat Bot Telegram

1. Chat **@BotFather** di Telegram → `/newbot` → ikuti instruksi → kamu akan dapat **token** seperti `123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`.
2. Cari **chat ID** tujuan alert:
   - Untuk chat pribadi: chat bot kamu dulu (kirim `/start`), lalu buka `https://api.telegram.org/bot<TOKEN>/getUpdates` di browser, cari field `"chat":{"id": ...}`.
   - Lebih mudah: chat **@userinfobot** atau **@myidbot** untuk dapat ID kamu langsung.
   - Untuk grup/channel: tambahkan bot ke grup, kirim pesan apapun, lalu cek `getUpdates` yang sama — ID grup biasanya angka negatif.

## 2. Dapatkan API Key untuk Analisa AI

Ada dua opsi **gratis tanpa kartu kredit** (default bot ini pakai opsi pertama), dan dua opsi berbayar kalau nanti mau upgrade kualitas:

| Provider | Biaya | Catatan |
|---|---|---|
| **Google Gemini** (`aistudio.google.com`) | Gratis, tanpa kartu kredit | Default bot ini. Kuota harian cukup besar (ratusan-ribuan request/hari tergantung model), jauh lebih dari cukup untuk beberapa alert per hari. Buka [aistudio.google.com](https://aistudio.google.com) → "Get API key". |
| **Groq** (`console.groq.com`) | Gratis, tanpa kartu kredit | Inference sangat cepat, model open-source (Llama, dll). Daftar di [console.groq.com](https://console.groq.com/keys) pakai email/Google. |
| Claude (Anthropic) | Berbayar (murah untuk pemakaian ringan begini) | Daftar di [console.anthropic.com](https://console.anthropic.com). |
| OpenAI (GPT) | Berbayar | Daftar di [platform.openai.com](https://platform.openai.com). |

Set `AI_PROVIDER=gemini` (atau `groq`/`anthropic`/`openai`) di `.env`, lalu isi API key yang sesuai. Kalau tidak mau pakai AI sama sekali, set `AI_PROVIDER=none` — bot tetap jalan, hanya analisanya jadi bias rule-based saja (tanpa narasi AI).

> Catatan soal kuota gratis: baik Gemini maupun Groq membatasi jumlah request per menit/hari (bukan per bulan), dan kebijakannya bisa berubah sewaktu-waktu mengikuti masing-masing provider. Untuk bot ini yang hanya memanggil AI beberapa kali sehari (saat ada rilis data high-impact), kuota gratis manapun harusnya jauh lebih dari cukup. Kalau suatu saat kena limit, tinggal ganti `AI_PROVIDER` ke opsi lain di `.env` tanpa ubah kode.

## 3. Coba Dulu Secara Lokal (opsional)

```bash
cd forex-alert-bot
pip install -r requirements.txt
cp .env.example .env        # lalu isi TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, dst.

# Test logika pakai data palsu dulu (tanpa kirim ke Telegram asli, tanpa perlu token):
python test_offline.py

# Kalau sudah yakin, jalankan beneran (akan benar-benar kirim ke Telegram & panggil AI):
python main.py
```

## 4. Deploy Gratis — GitHub Actions (rekomendasi karena tidak butuh server sama sekali)

Kamu bilang belum punya hosting — opsi paling gampang dan **100% gratis** untuk bot seperti ini adalah **GitHub Actions**, karena tidak perlu sewa server/VPS apapun. Bot akan otomatis "dibangunkan" oleh GitHub setiap 10 menit untuk cek kalender, kirim alert kalau ada, lalu tidur lagi.

**Langkah-langkah:**

1. Buat repo baru di GitHub (boleh **private**, GitHub Actions tetap gratis dengan kuota ±2000 menit/bulan untuk akun gratis — bot ini sangat ringan, jauh di bawah kuota itu).
2. Upload semua file di folder `forex-alert-bot/` ini ke repo tersebut.
3. Buka **Settings → Secrets and variables → Actions** di repo:
   - Tab **Secrets** → New repository secret, tambahkan:
     - `TELEGRAM_BOT_TOKEN`
     - `TELEGRAM_CHAT_ID`
     - `GEMINI_API_KEY` (default, gratis — atau `GROQ_API_KEY`/`ANTHROPIC_API_KEY` kalau pakai provider lain)
   - Tab **Variables** (opsional, kalau mau override default) → tambahkan `AI_PROVIDER`, `TZ_NAME`, `DAILY_AGENDA_HOUR` sesuai kebutuhan.
4. Buka tab **Actions** di repo → enable workflow kalau diminta.
5. Test manual dulu: tab **Actions** → pilih workflow "Forex High Impact Alert Bot" → **Run workflow** (tombol kanan atas) → cek apakah alert masuk ke Telegram.
6. Kalau berhasil, biarkan saja — workflow akan jalan otomatis setiap 10 menit selamanya, gratis, tanpa perlu kamu nyalakan komputer.

> Catatan: jadwal cron di file `.github/workflows/forex_alert.yml` memakai zona waktu **UTC** (standar GitHub Actions), tapi itu hanya menentukan *kapan workflow dijalankan* — perhitungan waktu event & jam agenda di dalam bot sendiri sudah otomatis dikonversi ke `TZ_NAME` (default `Asia/Jakarta` / WIB).

### Alternatif hosting lain (kalau suatu saat butuh bot yang lebih interaktif, misal command `/today`)

- **Render.com (free Web Service)** + **cron-job.org** (free, bisa ping tiap 1 menit) — Render free tier untuk *Background Worker* berbayar, tapi *Web Service* gratis bisa "dibangunkan" lewat HTTP ping dari cron-job.org untuk menjalankan cek secara periodik. Cocok kalau nanti mau tambah command interaktif.
- **VPS murah** (Contabo, DigitalOcean, dll, ~$4-6/bulan) atau **Oracle Cloud Free Tier** (VM gratis selamanya, tapi setup lebih teknis: SSH + systemd) — paling fleksibel untuk bot yang nyala 24/7 dan bisa merespons command real-time.

Untuk kebutuhan sekarang (alert + analisa, bukan bot yang harus merespons command), GitHub Actions sudah lebih dari cukup dan paling minim ribet.

## Kustomisasi

Semua diatur lewat environment variable (lihat `.env.example`):

| Variable | Default | Keterangan |
|---|---|---|
| `MIN_IMPACT` | `High` | Level impact yang dialert (`High`/`Medium`/`Low`) |
| `DAILY_AGENDA_HOUR` | `6` | Jam (WIB) agenda harian dikirim |
| `TZ_NAME` | `Asia/Jakarta` | Timezone untuk semua perhitungan waktu |
| `AI_PROVIDER` | `anthropic` | `anthropic` / `openai` / `none` |
| Interval cek | `*/10 * * * *` | Edit langsung di `.github/workflows/forex_alert.yml` |

## Batasan & Disclaimer Penting

- Feed kalender memakai endpoint publik Forex Factory (`nfs.faireconomy.media`) yang **tidak resmi** dan bisa berubah/limit sewaktu-waktu (dibatasi ±2 request/5 menit per IP) — sudah diberi fallback URL & interval 10 menit supaya aman.
- **Bias rule-based** hanya heuristik sederhana (bandingkan angka actual vs forecast), beberapa indikator seperti Unemployment/Jobless Claims sudah dibalik logikanya, tapi tetap tidak menangkap semua nuansa makro (contoh: inflasi tinggi kadang bullish kadang bearish tergantung konteks suku bunga).
- **Analisa AI** adalah opini yang dihasilkan model bahasa berdasarkan data yang ada, bukan rekomendasi finansial atau sinyal trading.
- Selalu lakukan riset/konfirmasi sendiri sebelum mengambil keputusan trading apapun.
