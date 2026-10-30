import os
import warnings
import yfinance as yf
import pandas as pd
import requests
import urllib.parse

warnings.filterwarnings("ignore")

TELEGRAM_USER = os.environ.get("TELEGRAM_USER")

def kirim_chat_telegram(pesan):
    if not TELEGRAM_USER:
        print("Error: TELEGRAM_USER belum diatur di GitHub Secrets!")
        return
    
    # Mengganti baris baru (\n) dengan pemisah spasi agar tidak terkena 403 Forbidden di Apache CallMeBot
    pesan_satu_baris = pesan.replace("\n", " | ")
    pesan_url = urllib.parse.quote(pesan_satu_baris)
    url = f"http://api.callmebot.com/text.php?user={TELEGRAM_USER}&text={pesan_url}"
    
    # Menyamarkan Python sebagai browser Chrome biasa agar tidak diblokir firewall
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200 and "Message sent" in r.text:
            print("✅ Pesan chat Telegram berhasil dikirim!")
        else:
            print(f"Status: {r.status_code} | Respons server:", r.text[:250])
    except Exception as e:
        print("Gagal mengirim chat Telegram:", e)

def main():
    print("Mengambil data Gold (XAUUSD / GC=F) timeframe 5m...")
    df = yf.download("GC=F", period="5d", interval="5m", progress=False)
    
    if df.empty or len(df) < 340:
        print("Data tidak cukup untuk menghitung MA 332.")
        return

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df['MA44'] = df['Close'].rolling(window=44).mean()
    df['MA332'] = df['Close'].rolling(window=332).mean()

    sinyal_ditemukan = False
    for i in [-2, -3]:
        ma44_lalu = df['MA44'].iloc[i - 1]
        ma332_lalu = df['MA332'].iloc[i - 1]
        ma44_skrg = df['MA44'].iloc[i]
        ma332_skrg = df['MA332'].iloc[i]
        harga_close = df['Close'].iloc[i]
        waktu = df.index[i]

        print(f"[{waktu}] Close: {harga_close:.2f} | MA44: {ma44_skrg:.2f} | MA332: {ma332_skrg:.2f}")

        if ma44_lalu <= ma332_lalu and ma44_skrg > ma332_skrg:
            print(">>> GOLDEN CROSS TERDETEKSI!")
            pesan = f"🟢 SINYAL BUY GOLD M5 | MA44 potong atas MA332 | Harga: {harga_close:.2f} | MA44: {ma44_skrg:.2f} | MA332: {ma332_skrg:.2f}"
            kirim_chat_telegram(pesan)
            sinyal_ditemukan = True
            break
        elif ma44_lalu >= ma332_lalu and ma44_skrg < ma332_skrg:
            print(">>> DEATH CROSS TERDETEKSI!")
            pesan = f"🔴 SINYAL SELL GOLD M5 | MA44 potong bawah MA332 | Harga: {harga_close:.2f} | MA44: {ma44_skrg:.2f} | MA332: {ma332_skrg:.2f}"
            kirim_chat_telegram(pesan)
            sinyal_ditemukan = True
            break

    if not sinyal_ditemukan:
        harga_terakhir = df['Close'].iloc[-2]
        ma44_terakhir = df['MA44'].iloc[-2]
        ma332_terakhir = df['MA332'].iloc[-2]
        selisih = abs(ma44_terakhir - ma332_terakhir)
        posisi = "Tren Naik" if ma44_terakhir > ma332_terakhir else "Tren Turun"

        pesan_rutin = f"📊 Update Gold M5 | Harga: {harga_terakhir:.2f} | MA44: {ma44_terakhir:.2f} | MA332: {ma332_terakhir:.2f} | Jarak: {selisih:.2f} ({posisi})"
        print("Mengirim laporan rutin 5 menit ke Telegram...")
        kirim_chat_telegram(pesan_rutin)

if __name__ == "__main__":
    main()
