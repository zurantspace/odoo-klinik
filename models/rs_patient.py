# -*- coding: utf-8 -*-
# Part of SIMRS.
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import re


class RsPatient(models.Model):
    _name = 'rs.patient'
    _description = 'Data Pasien'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'patient_no desc'
    _rec_name = 'name'

    # ── Identitas Utama ─────────────────────────────────────────────────────
    name = fields.Char(
        string='Nama Lengkap',
        required=True,
        tracking=True,
    )
    patient_no = fields.Char(
        string='No. Rekam Medis',
        copy=False,
        readonly=True,
        default=lambda self: _('Baru'),
        help="Nomor rekam medis unik, dibuat otomatis saat disimpan.",
    )
    nik = fields.Char(
        string='NIK',
        size=16,
        tracking=True,
        help="Nomor Induk Kependudukan (16 digit)",
    )
    birth_date = fields.Date(string='Tanggal Lahir', tracking=True)
    age = fields.Integer(
        string='Umur (thn)',
        compute='_compute_age',
        store=True,
    )
    gender = fields.Selection([
        ('male', 'Laki-laki'),
        ('female', 'Perempuan'),
    ], string='Jenis Kelamin', required=True, tracking=True)
    blood_type = fields.Selection([
        ('A', 'A'), ('B', 'B'), ('AB', 'AB'), ('O', 'O'),
    ], string='Golongan Darah')

    # ── Kontak ──────────────────────────────────────────────────────────────
    phone = fields.Char(string='No. HP', tracking=True)
    email = fields.Char(string='Email')
    address = fields.Text(string='Alamat Lengkap')
    emergency_contact_name = fields.Char(string='Nama Kontak Darurat')
    emergency_contact_phone = fields.Char(string='HP Kontak Darurat')
    emergency_contact_relation = fields.Char(string='Hubungan')

    # ── Asuransi / BPJS ─────────────────────────────────────────────────────
    insurance_type = fields.Selection([
        ('general', 'Umum / Mandiri'),
        ('bpjs', 'BPJS Kesehatan'),
        ('private', 'Asuransi Swasta'),
    ], string='Jenis Pembayaran', default='general', required=True, tracking=True)
    bpjs_no = fields.Char(
        string='No. BPJS',
        size=13,
        help="Nomor Kartu BPJS Kesehatan (13 digit)",
    )
    bpjs_class = fields.Selection([
        ('1', 'Kelas 1'),
        ('2', 'Kelas 2'),
        ('3', 'Kelas 3'),
    ], string='Kelas BPJS')
    insurance_company = fields.Char(
        string='Nama Asuransi',
        help="Isi jika Asuransi Swasta",
    )
    insurance_no = fields.Char(string='No. Polis Asuransi')

    # ── Medis ────────────────────────────────────────────────────────────────
    allergy_notes = fields.Text(
        string='Catatan Alergi',
        help="Alergi obat, makanan, atau bahan lain",
    )
    chronic_disease = fields.Text(string='Penyakit Kronis')
    is_minor = fields.Boolean(
        string='Pasien Anak',
        compute='_compute_is_minor',
        store=True,
    )
    guardian_name = fields.Char(string='Nama Wali (Anak)')
    guardian_relation = fields.Char(string='Hubungan Wali')

    # ── Partner Link ────────────────────────────────────────────────────────
    partner_id = fields.Many2one(
        'res.partner',
        string='Kontak Odoo',
        ondelete='set null',
        help="Link ke res.partner untuk keperluan invoice",
    )

    # ── Relasi ──────────────────────────────────────────────────────────────
    visit_ids = fields.One2many(
        'rs.clinic.visit', 'patient_id',
        string='Riwayat Kunjungan',
    )
    visit_count = fields.Integer(
        string='Jumlah Kunjungan',
        compute='_compute_visit_count',
    )
    last_visit_date = fields.Date(
        string='Kunjungan Terakhir',
        compute='_compute_last_visit_date',
        store=True,
    )

    # ── Computed Methods ─────────────────────────────────────────────────────
    @api.depends('birth_date')
    def _compute_age(self):
        today = fields.Date.today()
        for rec in self:
            if rec.birth_date:
                rec.age = (today - rec.birth_date).days // 365
            else:
                rec.age = 0

    @api.depends('age')
    def _compute_is_minor(self):
        for rec in self:
            rec.is_minor = rec.age < 12

    @api.depends('visit_ids')
    def _compute_visit_count(self):
        for rec in self:
            rec.visit_count = len(rec.visit_ids)

    @api.depends('visit_ids.visit_date')
    def _compute_last_visit_date(self):
        for rec in self:
            visits = rec.visit_ids.filtered(
                lambda v: v.state == 'done'
            ).sorted('visit_date', reverse=True)
            rec.last_visit_date = visits[0].visit_date if visits else False

    # ── ORM Overrides ────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('patient_no', _('Baru')) == _('Baru'):
                vals['patient_no'] = self.env['ir.sequence'].next_by_code(
                    'rs.patient.sequence'
                ) or _('Baru')
            # Auto-buat res.partner jika belum ada
            if not vals.get('partner_id'):
                partner = self.env['res.partner'].create({
                    'name': vals.get('name'),
                    'phone': vals.get('phone'),
                    'email': vals.get('email'),
                    'is_company': False,
                })
                vals['partner_id'] = partner.id
        return super().create(vals_list)

    # ── Validasi ─────────────────────────────────────────────────────────────
    @api.constrains('nik')
    def _check_nik(self):
        for rec in self:
            if rec.nik:
                if not re.match(r'^\d{16}$', rec.nik):
                    raise ValidationError(_("NIK harus 16 digit angka."))
                existing = self.search([
                    ('nik', '=', rec.nik),
                    ('id', '!=', rec.id),
                ])
                if existing:
                    raise ValidationError(
                        _("NIK %s sudah terdaftar untuk pasien: %s") % (
                            rec.nik, existing[0].name
                        )
                    )

    @api.constrains('bpjs_no')
    def _check_bpjs_no(self):
        for rec in self:
            if rec.bpjs_no and not re.match(r'^\d{13}$', rec.bpjs_no):
                raise ValidationError(_("Nomor BPJS harus 13 digit angka."))

    @api.constrains('is_minor', 'guardian_name')
    def _check_minor_guardian(self):
        for rec in self:
            if rec.is_minor and not rec.guardian_name:
                raise ValidationError(
                    _("Pasien anak (umur < 12 tahun) wajib mengisi nama wali.")
                )

    # ── Actions ──────────────────────────────────────────────────────────────
    def action_view_visits(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Kunjungan %s' % self.name,
            'res_model': 'rs.clinic.visit',
            'view_mode': 'list,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id},
        }

    def action_register_visit(self):
        """Shortcut buka form kunjungan baru dari halaman pasien."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Daftar Kunjungan Baru',
            'res_model': 'rs.clinic.visit',
            'view_mode': 'form',
            'context': {
                'default_patient_id': self.id,
                'default_partner_id': self.partner_id.id,
            },
        }
