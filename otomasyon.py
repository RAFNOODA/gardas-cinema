import json, re, urllib.request, urllib.parse, os

# --- AYARLARIN ---
DRIVE_API_KEY = "AIzaSyAIezbRGTLiIZLfJFOS292lnKIwKqOT3Q0"
KLASOR_ID = "1iA-tbMeSOs-eiD_-bzV2P8ba2fBNabxf"
TMDB_API_KEY = "3fd2be6f0c70a2a598f084ddfb75487c"
JSON_FILE = "/home/musab/Desktop/film.json"

def temiz_isim(ham_ad):
    t = ham_ad.lower()
    t = re.sub(r'\.(mp4|mkv|avi|mov|json|py|html|png|jpg)$', '', t)
    t = re.sub(r'\(.*?\)|\[.*?\]', '', t)
    copler = ['1080p', '720p', 'x264', 'x265', 'bluray', 'hdtv', 'türkçe', 'dublaj', 'altyazılı', 'hd', 'izle', 'full', 'movie']
    for c in copler: t = t.replace(c, '')
    return t.strip().title()

def tmdb_sorgula(isim, tip="movie"):
    """Puan ve Kadro için derinlemesine sorgu yapar[cite: 1]"""
    encoded_name = urllib.parse.quote(isim)
    search_url = f"https://api.themoviedb.org/3/search/{tip}?api_key={TMDB_API_KEY}&query={encoded_name}&language=tr-TR"
    
    try:
        req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as res:
            veri = json.loads(res.read().decode())
            if not veri.get('results'): return None
            
            f = veri['results'][0]
            tmdb_id = f['id']
            
            # append_to_response ile tek seferde oyuncuları ve detayları al[cite: 1]
            detay_url = f"https://api.themoviedb.org/3/{tip}/{tmdb_id}?api_key={TMDB_API_KEY}&language=tr-TR&append_to_response=credits"
            
            with urllib.request.urlopen(detay_url, timeout=10) as d_res:
                d_veri = json.loads(d_res.read().decode())
                cast = d_veri.get('credits', {}).get('cast', [])
                
                return {
                    "ad": d_veri.get('name') if tip == "tv" else d_veri.get('title'),
                    "afis": f"https://image.tmdb.org/t/p/w500{d_veri['poster_path']}" if d_veri.get('poster_path') else None,
                    "konu": d_veri.get('overview') or "Açıklama bulunamadı.",
                    "kategoriler": [g['name'] for g in d_veri.get('genres', [])] or ["Genel"],
                    "puan": str(round(d_veri.get('vote_average', 0.0), 1)), # Tam Puan[cite: 1]
                    "oyuncular": ", ".join([o['name'] for o in cast[:5]]) if cast else "Bilinmiyor"
                }
    except: return None

def calistir():
    query = urllib.parse.quote(f"'{KLASOR_ID}' in parents and trashed = false")
    drive_url = f"https://www.googleapis.com/drive/v3/files?q={query}&key={DRIVE_API_KEY}&fields=files(id,name)"
    
    try:
        with urllib.request.urlopen(drive_url) as res:
            dosyalar = json.loads(res.read().decode()).get('files', [])
        
        arsiv = {"filmler": [], "diziler": {}}
        for d in dosyalar:
            if d['name'].lower().endswith(('.json', '.py', '.html', '.txt')): continue
            m = re.search(r'(.*?)[. ]?s(\d+)e(\d+)', d['name'], re.IGNORECASE)
            
            if m: # Dizi[cite: 1]
                ham_ad = temiz_isim(m.group(1)); s, e = int(m.group(2)), int(m.group(3))
                if ham_ad not in arsiv["diziler"]:
                    info = tmdb_sorgula(ham_ad, "tv")
                    arsiv["diziler"][ham_ad] = {
                        "ad": info['ad'] if info else ham_ad, "afis": info['afis'] if info else None,
                        "konu": info['konu'] if info else "Açıklama yok.",
                        "puan": info['puan'] if info else "0.0", "oyuncular": info['oyuncular'] if info else "Bilinmiyor",
                        "kategoriler": info['kategoriler'] if info else ["Dizi"], "sezonlar": {}
                    }
                if s not in arsiv["diziler"][ham_ad]["sezonlar"]: arsiv["diziler"][ham_ad]["sezonlar"][s] = []
                arsiv["diziler"][ham_ad]["sezonlar"][s].append({"bolum": e, "id": d['id']})
                print(f"🎬 {ham_ad} - Puan: {arsiv['diziler'][ham_ad]['puan']}")
            else: # Film[cite: 1]
                film_ad = temiz_isim(d['name'])
                info = tmdb_sorgula(film_ad, "movie") or tmdb_sorgula(film_ad, "tv")
                puan_verisi = info['puan'] if info else "0.0"
                arsiv["filmler"].append({
                    "id": d['id'], "ad": info['ad'] if info else film_ad,
                    "afis": info['afis'] if info else None, "konu": info['konu'] if info else "Açıklama yok.",
                    "puan": puan_verisi, "oyuncular": info['oyuncular'] if info else "Bilinmiyor",
                    "kategoriler": info['kategoriler'] if info else ["Film"]
                })
                print(f"🎥 {film_ad} - Puan: {puan_verisi}")

        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(arsiv, f, ensure_ascii=False, indent=4)
        print(f"✅ JSON Mühürlendi: {JSON_FILE}")
    except Exception as e: print(f"❌ Hata: {e}")

if __name__ == "__main__": calistir()
import subprocess

def githuba_firlat():
    try:
        print("🚀 Kütüphane GitHub'a yükleniyor...")
        # Terminal komutlarını sırayla çalıştırır
        subprocess.run(["git", "add", "film.json"], check=True)
        subprocess.run(["git", "commit", "-m", "Kütüphane güncellendi"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("✅ Başarılı! Tüm cihazlar güncellendi.")
    except Exception as e:
        print(f"❌ GitHub bağlantı hatası: {e}")

# Mevcut calistir() kısmını şu şekilde güncelle:
if __name__ == "__main__":
    calistir() # Önce Drive'ı tara ve JSON'u yap
    githuba_firlat() # Sonra otomatik GitHub'a gönder
