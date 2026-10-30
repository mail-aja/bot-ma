import os
import yfinance as yf
import pandas as pd
import requests

TELEGRAM_USER = os.environ.get("TELEGRAM_USER")

def panggil_telegram(pesan):
    if not TELEGRAM_USER:
        print("Error: TELEGRAM_USER belum diatur di GitHub Secrets!")
        return
    pesan_url = pesan.replace(" ", "+")
    url = f"http://api.callmebot.com/start.php?user={TELEGRAM_USER}&text={pesan_url}&lang=id-ID-Standard-A&rpt=2"
    try:
        r = requests.get(url, timeout=15)
        print(f"Panggilan dipicu! Status: {r.status_code}")
        print("Jawaban Server CallMeBot:", r.text) # Menampilkan alasan jika telepon gagal
    except Exception as e:
        print("Gagal memanggil Telegram:", e)

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
        waktu = df.index[i]

        print(f"[{waktu}] MA44: {ma44_skrg:.2f} | MA332: {ma332_skrg:.2f}")

        if ma44_lalu <= ma332_lalu and ma44_skrg > ma332_skrg:
            print(">>> GOLDEN CROSS TERDETEKSI!")
            panggil_telegram("Sinyal Buy Gold. MA 44 memotong ke atas MA 332.")
            sinyal_ditemukan = True
            break
        elif ma44_lalu >= ma332_lalu and ma44_skrg < ma332_skrg:
            print(">>> DEATH CROSS TERDETEKSI!")
            panggil_telegram("Sinyal Sell Gold. MA 44 memotong ke bawah MA 332.")
            sinyal_ditemukan = True
            break

    if not sinyal_ditemukan:
        print("Belum ada persilangan MA44 dan MA332.")

if __name__ == "__main__":
    panggil_telegram("Tes panggilan bot Gold berhasil")
    main()
