import requests
from bs4 import BeautifulSoup
import os

# BURALARI KENDİNİZE GÖRE DÜZENLEYİN
URL = "https://yhgm.saglik.gov.tr/TR-119311/130donem-devlet-hizmeti-yukumlulugu-kurasi.html"
NTFY_TOPIC = "aa_1453_1_26"
ANAHTAR_KELIME = "Münhal Kadrolar"

def check_keyword():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    response = requests.get(URL, headers=headers)
    response.raise_for_status()
    
    # Sitenin sadece metin kısımlarını alıyoruz
    soup = BeautifulSoup(response.text, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    
    # Büyük/küçük harf duyarlılığını ortadan kaldırarak arama yapıyoruz
    return ANAHTAR_KELIME.lower() in text.lower()

try:
    is_found = check_keyword()
    
    # Sürekli aynı bildirimi atmamak için önceki durumu kontrol ediyoruz
    already_notified = False
    if os.path.exists("state.txt"):
        with open("state.txt", "r") as f:
            if f.read().strip() == "bulundu":
                already_notified = True

    if is_found and not already_notified:
        # Kelime eklendi ve henüz bildirim atılmadı!
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}", 
            data=f"DİKKAT: '{ANAHTAR_KELIME}' sitede yayınlandı!\nBağlantı: {URL}".encode('utf-8')
        )
        print("Kelime bulundu ve bildirim gönderildi.")
        
        # Durumu kaydediyoruz ki 10 dakika sonra tekrar bildirim atmasın
        with open("state.txt", "w") as f:
            f.write("bulundu")
            
    elif not is_found and already_notified:
        # Eğer kelime siteden tekrar kaldırılırsa durumu sıfırlıyoruz
        with open("state.txt", "w") as f:
            f.write("bulunmadi")
        print("Kelime siteden kaldırılmış, durum sıfırlandı.")
        
    else:
        if is_found:
            print("Kelime sitede var ama bildirim zaten gönderilmiş.")
        else:
            print("Kelime henüz sitede yok.")

except Exception as e:
    print("Bir hata oluştu:", e)
