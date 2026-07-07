# -*- coding: utf-8 -*-
# Part of SIMRS. See LICENSE file for full copyright and licensing details.
{
    'name': 'RS - Manajemen Pasien & Klinik',
    'version': '19.0.1.0.0',
    'category': 'Healthcare',
    'summary': 'Manajemen pendaftaran pasien, antrian poliklinik, dan kunjungan rawat jalan',
    'description': """
Modul Manajemen Pasien & Klinik Rumah Sakit
============================================
Fitur:
- Pendaftaran dan master data pasien (NIK, BPJS, dll.)
- Manajemen poliklinik dan jadwal dokter
- Sistem antrian per poliklinik per hari
- Pencatatan kunjungan dan diagnosa
- Integrasi invoice otomatis untuk pasien umum
- Notifikasi SMS antrian
    """,
    'author': 'SIMRS Dev Team',
    'website': '',
    'depends': [
        'base',
        'mail',
        'hr',
        'calendar',
        'sms',
        'account',
    ],
    'data': [
        # Security — harus load pertama
        'security/rs_clinic_security.xml',
        'security/ir.model.access.csv',
        # Sequences & Data awal
        'data/rs_clinic_sequences.xml',
        # Assets (JS/CSS/XML OWL)
        'views/rs_clinic_assets.xml',
        # Views
        'views/rs_polyclinic_views.xml',
        'views/rs_patient_views.xml',
        'views/rs_clinic_visit_views.xml',
        'views/rs_clinic_queue_views.xml',
        'views/rs_clinic_dashboard_views.xml',
        'views/rs_clinic_menu.xml',
        # Reports
        'report/rs_clinic_reports.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'rs_clinic/static/src/js/rs_clinic_dashboard.js',
            'rs_clinic/static/src/xml/rs_clinic_dashboard.xml',
            'rs_clinic/static/src/css/rs_clinic_dashboard.css',
        ],
    },
    'demo': [
        'data/rs_clinic_demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
