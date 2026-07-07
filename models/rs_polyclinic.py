# -*- coding: utf-8 -*-
# Part of SIMRS.
from odoo import api, fields, models, _


class RsPolyclinic(models.Model):
    _name = 'rs.polyclinic'
    _description = 'Poliklinik'
    _inherit = ['mail.thread']
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(string='Nama Poliklinik', required=True, tracking=True)
    code = fields.Char(string='Kode Poli', required=True, size=10)
    location = fields.Char(
        string='Lokasi / Ruangan',
        help="Contoh: Lantai 2 - Gedung A",
    )
    doctor_ids = fields.Many2many(
        'hr.employee',
        'rs_polyclinic_doctor_rel',
        'polyclinic_id',
        'doctor_id',
        string='Dokter Bertugas',
        domain=[('job_id.name', 'ilike', 'dokter')],
    )
    active = fields.Boolean(string='Aktif', default=True)
    color = fields.Integer(string='Warna', default=0)
    description = fields.Text(string='Keterangan')

    # ── Statistik ────────────────────────────────────────────────────────────
    visit_today_count = fields.Integer(
        string='Kunjungan Hari Ini',
        compute='_compute_visit_today_count',
    )
    queue_today_count = fields.Integer(
        string='Antrian Aktif',
        compute='_compute_queue_today_count',
    )

    @api.depends()
    def _compute_visit_today_count(self):
        today = fields.Date.today()
        Visit = self.env['rs.clinic.visit']
        for rec in self:
            rec.visit_today_count = Visit.search_count([
                ('polyclinic_id', '=', rec.id),
                ('visit_date', '=', today),
            ])

    @api.depends()
    def _compute_queue_today_count(self):
        today = fields.Date.today()
        Visit = self.env['rs.clinic.visit']
        for rec in self:
            rec.queue_today_count = Visit.search_count([
                ('polyclinic_id', '=', rec.id),
                ('visit_date', '=', today),
                ('state', 'in', ['queued', 'in_progress']),
            ])

    def action_view_today_visits(self):
        self.ensure_one()
        return {
            'name': _('Kunjungan Hari Ini'),
            'type': 'ir.actions.act_window',
            'res_model': 'rs.clinic.visit',
            'view_mode': 'kanban,list,form',
            'domain': [
                ('polyclinic_id', '=', self.id),
                ('visit_date', '=', fields.Date.today()),
            ],
            'context': {
                'default_polyclinic_id': self.id,
                'default_visit_date': fields.Date.today(),
            },
        }

    # ── Constraints ──────────────────────────────────────────────────────────
    _code_uniq = models.Constraint(
        'UNIQUE(code)',
        'Kode poliklinik harus unik!',
    )
