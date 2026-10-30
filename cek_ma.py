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
    
    pesan_url = urllib.parse.quote_plus(pesan)
    url = f"https://api.callmebot.com/text.php?user={TELEGRAM_USER}&text={pesan_url}"
    
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200 and "Message sent" in r.text:
            print("✅ Pesan chat Telegram berhasil dikirim!")
        else:
            print("Respons server:", r.text[:200])
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
            pesan = (
                f"🟢 SINYAL BUY GOLD (XAUUSD M5)\n"
                f"MA 44 memotong ke atas MA 332\n"
                f"Harga: {harga_close:.2f}\n"
                f"MA 44: {ma44_skrg:.2f} | MA 332: {ma332_skrg:.2f}"
            )
            kirim_chat_telegram(pesan)
            sinyal_ditemukan = True
            break
        elif ma44_lalu >= ma332_lalu and ma44_skrg < ma332_skrg:
            print(">>> DEATH CROSS TERDETEKSI!")
            pesan = (
                f"🔴 SINYAL SELL GOLD (XAUUSD M5)\n"
                f"MA 44 memotong ke bawah MA 332\n"
                f"Harga: {harga_close:.2f}\n"
                f"MA 44: {ma44_skrg:.2f} | MA 332: {ma332_skrg:.2f}"
            )
            kirim_chat_telegram(pesan)
            sinyal_ditemukan = True
            break

    # Bagian ini akan mengirim chat rutin setiap 5 menit meskipun belum bersilangan
    if not sinyal_ditemukan:
        harga_terakhir = df['Close'].iloc[-2]
        ma44_terakhir = df['MA44'].iloc[-2]
        ma332_terakhir = df['MA332'].iloc[-2]
        selisih = abs(ma44_terakhir - ma332_terakhir)
        posisi = "MA44 di ATAS MA332 (Tren Naik)" if ma44_terakhir > ma332_terakhir else "MA44 di BAWAH MA332 (Tren Turun)"

        pesan_rutin = (
            f"📊 Update Gold M5 (Belum Cross)\n"
            f"Harga: {harga_terakhir:.2f}\n"
            f"MA 44: {ma44_terakhir:.2f}\n"
            f"MA 332: {ma332_terakhir:.2f}\n"
            f"Jarak: {selisih:.2f} poin\n"
            f"Status: {posisi}"
        )
        print("Mengirim laporan rutin 5 menit ke Telegram...")
        kirim_chat_telegram(pesan_rutin)

if __name__ == "__main__":
    main()
