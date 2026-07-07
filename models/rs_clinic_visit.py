# -*- coding: utf-8 -*-
# Part of SIMRS.
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class RsClinicVisit(models.Model):
    _name = 'rs.clinic.visit'
    _description = 'Kunjungan Pasien'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'visit_date desc, queue_number asc'
    _rec_name = 'reference'

    # ── Identitas ────────────────────────────────────────────────────────────
    reference = fields.Char(
        string='No. Kunjungan',
        copy=False,
        readonly=True,
        default=lambda self: _('Baru'),
    )
    patient_id = fields.Many2one(
        'rs.patient',
        string='Pasien',
        required=True,
        ondelete='restrict',
        tracking=True,
        index=True,
    )
    patient_no = fields.Char(
        related='patient_id.patient_no',
        string='No. Rekam Medis',
        readonly=True,
    )
    partner_id = fields.Many2one(
        related='patient_id.partner_id',
        string='Partner',
        store=True,
    )
    insurance_type = fields.Selection([
        ('general', 'Umum / Mandiri'),
        ('bpjs', 'BPJS Kesehatan'),
        ('private', 'Asuransi Swasta'),
    ], string='Jenis Pembayaran', default='general', required=True,
        tracking=True, index=True,
        help="Jenis pembayaran untuk kunjungan ini. Default dari data pasien tapi dapat diubah.",
    )
    bpjs_no = fields.Char(
        string='No. BPJS',
        help="Nomor BPJS untuk kunjungan ini. Diisi otomatis dari data pasien.",
    )

    # ── Klinik ───────────────────────────────────────────────────────────────
    polyclinic_id = fields.Many2one(
        'rs.polyclinic',
        string='Poliklinik',
        required=True,
        tracking=True,
        index=True,
    )
    doctor_id = fields.Many2one(
        'hr.employee',
        string='Dokter',
        domain="[('id', 'in', polyclinic_id.doctor_ids.ids)]",
        tracking=True,
    )
    visit_date = fields.Date(
        string='Tanggal Kunjungan',
        required=True,
        default=fields.Date.today,
        tracking=True,
        index=True,
    )
    queue_number = fields.Integer(
        string='No. Antrian',
        readonly=True,
        copy=False,
        help="Nomor antrian otomatis per poliklinik per hari",
    )
    visit_type = fields.Selection([
        ('new', 'Pasien Baru'),
        ('control', 'Kontrol'),
        ('emergency', 'Darurat / UGD'),
        ('referral', 'Rujukan'),
    ], string='Jenis Kunjungan', required=True, default='new', tracking=True)

    # ── Medis ────────────────────────────────────────────────────────────────
    complaint = fields.Text(
        string='Keluhan Utama',
        help="Keluhan yang disampaikan pasien saat pendaftaran",
    )
    diagnosis = fields.Text(
        string='Diagnosa',
        tracking=True,
        help="Diagnosa dokter setelah pemeriksaan",
    )
    icd10_code = fields.Char(
        string='Kode ICD-10',
        help="Kode diagnosa International Classification of Diseases",
    )
    prescription_notes = fields.Text(string='Catatan Resep / Tindakan')
    follow_up_date = fields.Date(string='Tanggal Kontrol Berikutnya')
    notes = fields.Text(string='Catatan Tambahan')

    # ── Keuangan ────────────────────────────────────────────────────────────
    consultation_fee = fields.Float(
        string='Biaya Konsultasi',
        default=0.0,
        tracking=True,
    )
    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        copy=False,
        readonly=True,
    )
    invoice_state = fields.Selection(
        related='invoice_id.payment_state',
        string='Status Pembayaran',
        readonly=True,
    )

    # ── Status ───────────────────────────────────────────────────────────────
    state = fields.Selection([
        ('registered', 'Terdaftar'),
        ('queued', 'Menunggu Antrian'),
        ('in_progress', 'Sedang Ditangani'),
        ('done', 'Selesai'),
        ('cancelled', 'Dibatalkan'),
    ], string='Status', default='registered', required=True,
        tracking=True, copy=False, index=True)

    # ── Computed ─────────────────────────────────────────────────────────────
    patient_age = fields.Integer(
        related='patient_id.age',
        string='Umur',
        readonly=True,
    )
    patient_allergy = fields.Text(
        related='patient_id.allergy_notes',
        string='Alergi',
        readonly=True,
    )

    # ── Onchange ─────────────────────────────────────────────────────────────
    @api.onchange('patient_id')
    def _onchange_patient_id(self):
        """Isi default insurance_type dan bpjs_no dari data pasien.
        Petugas masih bisa mengubahnya sesuai kondisi kunjungan."""
        if self.patient_id:
            self.insurance_type = self.patient_id.insurance_type or 'general'
            self.bpjs_no = self.patient_id.bpjs_no
        else:
            self.insurance_type = 'general'
            self.bpjs_no = False

    # ── ORM Overrides ────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Generate nomor kunjungan
            if vals.get('reference', _('Baru')) == _('Baru'):
                vals['reference'] = self.env['ir.sequence'].next_by_code(
                    'rs.clinic.visit.sequence'
                ) or _('Baru')
            # Generate nomor antrian per poli per hari
            if not vals.get('queue_number'):
                vals['queue_number'] = self._get_next_queue_number(
                    vals.get('polyclinic_id'),
                    vals.get('visit_date'),
                )
        return super().create(vals_list)

    @api.model
    def _get_next_queue_number(self, polyclinic_id, visit_date):
        """Hitung nomor antrian berikutnya untuk poli & tanggal tertentu."""
        if not polyclinic_id or not visit_date:
            return 1
        last_visit = self.search([
            ('polyclinic_id', '=', polyclinic_id),
            ('visit_date', '=', visit_date),
        ], order='queue_number desc', limit=1)
        return (last_visit.queue_number + 1) if last_visit else 1

    # ── State Transitions ────────────────────────────────────────────────────
    def action_confirm_queue(self):
        """Dari Terdaftar → Menunggu Antrian"""
        for rec in self:
            if rec.state != 'registered':
                raise UserError(_("Hanya kunjungan berstatus 'Terdaftar' yang bisa dikonfirmasi."))
            rec.state = 'queued'

    def action_start_treatment(self):
        """Dari Menunggu Antrian → Sedang Ditangani"""
        for rec in self:
            if rec.state != 'queued':
                raise UserError(_("Hanya kunjungan berstatus 'Menunggu Antrian' yang bisa diproses."))
            rec.state = 'in_progress'

    def action_done(self):
        """Dari Sedang Ditangani → Selesai. Auto-buat invoice untuk pasien umum."""
        for rec in self:
            if rec.state != 'in_progress':
                raise UserError(_("Hanya kunjungan yang sedang ditangani yang bisa diselesaikan."))
            rec.state = 'done'
            # Auto-generate invoice untuk pasien umum & asuransi swasta
            if rec.insurance_type in ('general', 'private') and rec.consultation_fee > 0:
                rec._create_invoice()

    def action_cancel(self):
        """Batalkan kunjungan."""
        for rec in self:
            if rec.state == 'done':
                raise UserError(_("Kunjungan yang sudah selesai tidak bisa dibatalkan."))
            rec.state = 'cancelled'

    def action_reset_to_registered(self):
        """Reset ke status awal (jika dibatalkan)."""
        for rec in self:
            if rec.state != 'cancelled':
                raise UserError(_("Hanya kunjungan yang dibatalkan yang bisa direset."))
            rec.state = 'registered'

    # ── Invoice ──────────────────────────────────────────────────────────────
    def _create_invoice(self):
        """Buat invoice otomatis setelah kunjungan selesai."""
        self.ensure_one()
        if not self.partner_id:
            return
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.today(),
            'ref': self.reference,
            'invoice_line_ids': [(0, 0, {
                'name': 'Biaya Konsultasi — %s — %s' % (
                    self.polyclinic_id.name,
                    self.doctor_id.name or 'Dokter',
                ),
                'quantity': 1.0,
                'price_unit': self.consultation_fee,
            })],
        })
        self.invoice_id = move.id
        return move

    def action_view_invoice(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
        }

    # ── Validasi ─────────────────────────────────────────────────────────────
    @api.constrains('visit_date')
    def _check_visit_date(self):
        today = fields.Date.today()
        for rec in self:
            if rec.visit_date and rec.visit_date > today:
                raise ValidationError(_("Tanggal kunjungan tidak boleh di masa depan."))
