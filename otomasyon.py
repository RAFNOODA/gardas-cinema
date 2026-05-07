import requests
import json
import os
import re

# ================= AYARLAR =================
# İstediğin API anahtarları buraya işlendi
VIDMOLY_API_KEY = "619236ku6lthluftwfvwfz"
TMDB_API_KEY = "3fd2be6f0c70a2a598f084ddfb75487c"
JSON_DOSYASI = "film.json"
# ===========================================

def ismi_temizle(dosya_adi):
    # Dosya adındaki teknik terimleri temizler (Matrix.1080p.mp4 -> Matrix)
    sil = r'(1080p|720p|480p|mkv|mp4|avi|x264|bluray|webrip|tr|dublaj|altyazılı|full|izle)'
    temiz = re.sub(sil, '', dosya_adi, flags=re.IGNORECASE)
    temiz = temiz.replace('.', ' ').replace('-', ' ').replace('_', ' ')
    temiz = re.sub(r'\(.*?\)', '', temiz)
    return temiz.strip()

def tmdb_bilgi_cek(film_adi):
    temiz_ad = ismi_temizle(film_adi)
    print(f"🔍 TMDB'de Aranan: {temiz_ad}")
    
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={temiz_ad}&language=tr-TR"
    
    try:
        res = requests.get(url, timeout=10).json()
        if res.get('results') and len(res['results']) > 0:
            f_id = res['results'][0]['id']
            # Detaylar ve Oyuncular için derin sorgu
            d_url = f"https://api.themoviedb.org/3/movie/{f_id}?api_key={TMDB_API_KEY}&append_to_response=credits&language=tr-TR"
            d = requests.get(d_url, timeout=10).json()
            
            afis_yolu = d.get('poster_path')
            return {
                "ad": d.get('title', temiz_ad),
                "puan": str(round(d.get('vote_average', 0), 1)),
                "oyuncular": ", ".join([c['name'] for c in d.get('credits', {}).get('cast', [])[:3]]),
                "konu": d.get('overview', 'Özet bulunamadı.'),
                "afis": f"https://image.tmdb.org/t/p/w500{afis_yolu}" if afis_yolu else "https://via.placeholder.com/500x750?text=Afis+Yok",
                "kategoriler": [g['name'] for g in d.get('genres', [])]
            }
    except Exception as e:
        print(f"⚠️ TMDB Hatası: {e}")
    return None

def main():
    print("🚀 Vidmoly Kütüphanesi taranıyor...")
    # Tarayıcıda çalışan .me uzantısını kullanıyoruz
    vid_url = f"https://vidmoly.me/api/file/list?key={VIDMOLY_API_KEY}"
    
    try:
        response = requests.get(vid_url, timeout=15)
        vid_res = response.json()
    except Exception as e:
        print(f"❌ Vidmoly Bağlantı Hatası: {e}")
        return

    if vid_res.get('status') == 200:
        # Mevcut JSON'u yükle veya yeni oluştur
        if os.path.exists(JSON_DOSYASI):
            with open(JSON_DOSYASI, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except:
                    data = {"filmler": [], "diziler": {}}
        else:
            data = {"filmler": [], "diziler": {}}

        mevcut_idler = [f['id'] for f in data.get('filmler', [])]
        dosyalar = vid_res.get('result', {}).get('files', [])
        
        if not dosyalar:
            print("✅ API Başarılı! Ancak Vidmoly hesabında henüz video yok.")
            return

        eklenen = 0
        for file in dosyalar:
            fid = file['file_code']
            fname = file['title']
            
            if fid not in mevcut_idler:
                print("-" * 30)
                print(f"🆕 Yeni Dosya: {fname}")
                detay = tmdb_bilgi_cek(fname)
                
                if detay:
                    detay["id"] = fid
                    data['filmler'].append(detay)
                    eklenen += 1
                    print(f"✅ Eklendi: {detay['ad']}")
                else:
                    print(f"⚠️ {fname} TMDB'de bulunamadı, atlanıyor.")

        if eklenen > 0:
            with open(JSON_DOSYASI, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"\n✨ İşlem Tamam! {eklenen} yeni film JSON'a işlendi.")
        else:
            print("\n😎 Tüm içerikler güncel, yeni bir şey yok.")
    else:
        print(f"❌ Vidmoly Hatası: {vid_res.get('msg', 'Bilinmeyen Hata')}")

if __name__ == "__main__":
    main()
