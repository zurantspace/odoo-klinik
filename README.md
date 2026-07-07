# SIMRS Klinik (rs_clinic)

Modul Odoo 19 untuk manajemen pelayanan rawat jalan, mencakup pendaftaran pasien, pengelolaan antrian poliklinik harian, pencatatan rekam medis, dan otomatisasi pembuatan invoice tagihan konsultasi.

## Fitur Utama

*   **Dashboard Real-Time**: 
    *   Pemantauan total kunjungan hari ini, status antrian (menunggu/sedang diperiksa/selesai).
    *   Daftar live feed pasien yang sedang ditangani oleh dokter di ruang pemeriksaan.
    *   Statistik jumlah kunjungan dan antrian aktif untuk masing-masing poliklinik.
    *   Akses cepat (shortcut) pendaftaran kunjungan baru dan pencarian data pasien.
*   **Registrasi & Master Pasien**:
    *   Pencatatan data identitas (Nama, NIK, Golongan Darah, Tanggal Lahir).
    *   Nomor rekam medis (no. RM) dibuat otomatis secara berurutan.
    *   Validasi NIK wajib 16 digit & nomor BPJS wajib 13 digit (unik).
    *   Deteksi otomatis pasien anak (< 12 tahun) dengan kewajiban mengisi nama wali.
*   **Transaksi Kunjungan & Antrian**:
    *   Sistem antrian otomatis per poliklinik per hari.
    *   Alur status terstruktur: *Terdaftar* -> *Menunggu Antrian* -> *Sedang Ditangani* -> *Selesai / Dibatalkan*.
    *   Penentuan jenis pembayaran (Umum / Mandiri, BPJS Kesehatan, Asuransi Swasta) langsung saat pasien mendaftar kunjungan.
    *   Peringatan catatan alergi pasien yang langsung muncul di form kunjungan untuk mencegah kesalahan medis.
*   **Integrasi Keuangan (Invoice)**:
    *   Otomatis membuat draft invoice (`account.move`) ketika status kunjungan diubah ke *Selesai* (khusus pasien kategori Umum/Mandiri & Asuransi Swasta dengan biaya konsultasi > 0).

## Struktur Modul

```text
rs_clinic/
├── data/
│   ├── rs_clinic_demo.xml        # Data demo (pasien, poli, kunjungan)
│   └── rs_clinic_sequences.xml   # Sequence nomor RM & nomor kunjungan
├── models/
│   ├── rs_patient.py             # Data master pasien & validasi NIK/BPJS
│   ├── rs_polyclinic.py          # Data master poliklinik & dokter jaga
│   ├── rs_clinic_visit.py        # Logika pendaftaran kunjungan & auto-invoice
│   └── rs_clinic_queue.py        # Logika pemanggilan nomor antrian harian
├── security/
│   ├── rs_clinic_security.xml    # Grouping akses (Resepsionis, Dokter, Manager)
│   └── ir.model.access.csv       # Hak akses tabel database
├── static/
│   └── src/
│       ├── css/                  # Styling minimal dashboard
│       ├── js/                   # OWL Component dashboard (data fetch & action)
│       └── xml/                  # Template OWL dashboard (Odoo native design)
├── views/
│   ├── rs_patient_views.xml      # View list, form, search pasien
│   ├── rs_polyclinic_views.xml   # View list, form poliklinik
│   ├── rs_clinic_visit_views.xml # View list, kanban antrian, form kunjungan
│   ├── rs_clinic_queue_views.xml # View sesi antrian harian
│   ├── rs_clinic_dashboard_views.xml # Client action dashboard
│   └── rs_clinic_menu.xml        # Navigasi menu utama
└── __manifest__.py               # Informasi dependensi & list file xml
```

## Persyaratan Sistem

*   Odoo 19.0 (Community / Enterprise)
*   Python 3.10 / 3.12
*   Modul dependensi Odoo bawaan:
    *   `base`
    *   `mail` (Chatter & tracking log)
    *   `hr` (Data dokter/karyawan)
    *   `calendar` (Jadwal)
    *   `sms` (Rencana notifikasi antrian)
    *   `account` (Faktur / Invoice)

## Cara Instalasi

1.  Salin direktori `rs_clinic` ke folder `custom_addons` Odoo Anda.
2.  Pastikan path `custom_addons` sudah didaftarkan pada file konfigurasi `odoo.conf`:
    ```ini
    addons_path = /path/to/odoo/addons, /path/to/your/custom_addons
    ```
3.  Restart service server Odoo Anda.
4.  Aktifkan **Developer Mode** di Odoo.
5.  Masuk ke menu **Apps**, klik **Update Apps List** di bagian atas.
6.  Cari kata kunci `rs_clinic` (nama modul: *RS - Manajemen Pasien & Klinik*).
7.  Klik tombol **Activate** untuk memulai proses instalasi.
