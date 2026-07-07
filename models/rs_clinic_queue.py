# -*- coding: utf-8 -*-
# Part of SIMRS.
from odoo import api, fields, models, _


class RsClinicQueue(models.Model):
    _name = 'rs.clinic.queue'
    _description = 'Antrian Poliklinik Harian'
    _order = 'date desc, polyclinic_id'
    _rec_name = 'display_name'

    date = fields.Date(
        string='Tanggal',
        required=True,
        default=fields.Date.today,
        index=True,
    )
    polyclinic_id = fields.Many2one(
        'rs.polyclinic',
        string='Poliklinik',
        required=True,
        ondelete='restrict',
        index=True,
    )
    doctor_id = fields.Many2one(
        'hr.employee',
        string='Dokter Jaga',
        domain="[('id', 'in', polyclinic_id.doctor_ids.ids)]",
    )
    current_number = fields.Integer(
        string='No. Antrian Saat Ini',
        default=0,
        help="Nomor antrian yang sedang dipanggil/dilayani",
    )
    visit_ids = fields.One2many(
        'rs.clinic.visit',
        compute='_compute_visit_ids',
        string='Daftar Antrian',
    )
    total_queue = fields.Integer(
        string='Total Antrian',
        compute='_compute_queue_stats',
    )
    waiting_count = fields.Integer(
        string='Menunggu',
        compute='_compute_queue_stats',
    )
    done_count = fields.Integer(
        string='Selesai',
        compute='_compute_queue_stats',
    )
    display_name = fields.Char(
        string='Nama',
        compute='_compute_display_name',
        store=True,
    )

    # ── Computed ─────────────────────────────────────────────────────────────
    @api.depends('date', 'polyclinic_id')
    def _compute_display_name(self):
        for rec in self:
            if rec.polyclinic_id and rec.date:
                rec.display_name = '%s — %s' % (
                    rec.polyclinic_id.name,
                    rec.date.strftime('%d/%m/%Y'),
                )
            else:
                rec.display_name = _('Antrian Baru')

    @api.depends('date', 'polyclinic_id')
    def _compute_visit_ids(self):
        Visit = self.env['rs.clinic.visit']
        for rec in self:
            rec.visit_ids = Visit.search([
                ('polyclinic_id', '=', rec.polyclinic_id.id),
                ('visit_date', '=', rec.date),
            ])

    @api.depends('date', 'polyclinic_id')
    def _compute_queue_stats(self):
        Visit = self.env['rs.clinic.visit']
        for rec in self:
            all_visits = Visit.search([
                ('polyclinic_id', '=', rec.polyclinic_id.id),
                ('visit_date', '=', rec.date),
            ])
            rec.total_queue = len(all_visits)
            rec.waiting_count = len(all_visits.filtered(
                lambda v: v.state in ('queued', 'registered')
            ))
            rec.done_count = len(all_visits.filtered(
                lambda v: v.state == 'done'
            ))

    # ── Actions ──────────────────────────────────────────────────────────────
    def action_call_next(self):
        """Panggil nomor antrian berikutnya."""
        self.ensure_one()
        next_visit = self.env['rs.clinic.visit'].search([
            ('polyclinic_id', '=', self.polyclinic_id.id),
            ('visit_date', '=', self.date),
            ('queue_number', '>', self.current_number),
            ('state', '=', 'queued'),
        ], order='queue_number asc', limit=1)

        if not next_visit:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _('Semua pasien sudah dilayani.'),
                    'type': 'success',
                }
            }
        self.current_number = next_visit.queue_number
        next_visit.action_start_treatment()
        return True

    # ── Constraints ──────────────────────────────────────────────────────────
    _unique_poli_date = models.Constraint(
        'UNIQUE(polyclinic_id, date)',
        'Sudah ada sesi antrian untuk poliklinik dan tanggal ini!',
    )

