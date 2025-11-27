# -*- coding: utf-8 -*-
# Bu scripti Odoo Shell içerisinde çalıştırabilirsiniz.
# Çalıştırmak için: python odoo-bin shell -c <config_dosyasi> -d <veritabani_adi>
# Shell açıldıktan sonra bu dosyanın içeriğini yapıştırın veya import edin.

def remove_duplicate_ads_by_vin(env):
    print("Duplicate kontrolü başlıyor...")
    
    # 1. VIN attribute'unu bul
    vin_attr = env['escrow.ad.attribute'].search([('technical_name', '=', 'vin')], limit=1)
    if not vin_attr:
        print("HATA: 'vin' teknik adına sahip attribute bulunamadı.")
        return

    # 2. VIN değeri olan tüm attribute value'ları getir
    vin_values = env['escrow.ad.attribute.value'].search([
        ('attribute_id', '=', vin_attr.id),
        ('value_char', '!=', False)
    ])

    # 3. VIN numarasına göre ilanları grupla
    vin_groups = {}
    for val in vin_values:
        vin = val.value_char.strip() # Boşlukları temizle
        if not vin:
            continue
        
        if vin not in vin_groups:
            vin_groups[vin] = []
        
        # Bu değere sahip ilanı listeye ekle
        if val.ad_id and val.ad_id.exists():
            vin_groups[vin].append(val.ad_id)

    # 4. Tekrarlayanları tespit et ve silinecekleri belirle
    ads_to_delete = env['escrow.ad']
    duplicate_count = 0

    print(f"Toplam {len(vin_groups)} farklı şasi numarası kontrol ediliyor...")

    for vin, ads in vin_groups.items():
        # Aynı ilanın birden fazla value kaydı olabilir, unique ilanları al
        unique_ads_dict = {ad.id: ad for ad in ads}
        unique_ads = list(unique_ads_dict.values())
        
        # ID'ye göre sırala (Eskiden yeniye)
        sorted_ads = sorted(unique_ads, key=lambda a: a.id)

        if len(sorted_ads) > 1:
            # İlk oluşturulanı (en küçük ID) tut, diğerlerini sil
            keep_ad = sorted_ads[0]
            duplicates = sorted_ads[1:]
            
            print(f"\nŞasi No: {vin}")
            print(f"  TUTULACAK: ID {keep_ad.id} - {keep_ad.name}")
            
            for dup in duplicates:
                print(f"  SİLİNECEK: ID {dup.id} - {dup.name}")
                ads_to_delete += dup
                duplicate_count += 1

    print(f"\nToplam {duplicate_count} adet mükerrer ilan bulundu.")

    # 5. Silme işlemi
    if duplicate_count > 0:
        print("Silme işlemi başlatılıyor...")
        # Silme işlemini gerçekleştirmek için aşağıdaki satırların yorumunu kaldırın:
        # ads_to_delete.unlink()
        # env.cr.commit()
        print("DİKKAT: Silme komutu şu an yorum satırı halinde. Kodu düzenleyip 'unlink' satırını açın.")
    else:
        print("Mükerrer kayıt bulunamadı.")

# Fonksiyonu çalıştır (Shell ortamında 'env' değişkeni mevcuttur)
if 'env' in locals():
    remove_duplicate_ads_by_vin(env)
else:
    print("Bu script Odoo Shell ortamında çalıştırılmalıdır.")
