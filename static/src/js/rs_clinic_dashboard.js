/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";

class RsClinicDashboard extends Component {
    static template = "rs_clinic.Dashboard";
    static props = {};

    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this._refreshTimer = null;

        this.state = useState({
            visitTodayCount: 0,
            queueCount: 0,
            inProgressCount: 0,
            doneCount: 0,
            patientCount: 0,
            polyclinics: [],
            activeVisits: [], // Pasien sedang ditangani
            todayStr: "",
            isLoading: true,
        });

        onWillStart(async () => {
            await this._loadData();
        });

        onMounted(() => {
            // Auto-refresh tiap 30 detik untuk kenyamanan real-time antrian
            this._refreshTimer = setInterval(() => this._loadData(), 30_000);
        });

        onWillUnmount(() => {
            if (this._refreshTimer) {
                clearInterval(this._refreshTimer);
                this._refreshTimer = null;
            }
        });
    }

    async _loadData() {
        // Ambil tanggal lokal browser (menghindari ketidakcocokan timezone UTC dengan local Odoo)
        const d = new Date();
        const today = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;

        // Format tanggal bahasa Indonesia
        const days = ["Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"];
        const months = [
            "Januari", "Februari", "Maret", "April", "Mei", "Juni",
            "Juli", "Agustus", "September", "Oktober", "November", "Desember"
        ];
        this.state.todayStr = `${days[d.getDay()]}, ${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`;

        try {
            const [visitToday, waitingCount, inProgressCount, doneCount, patientCount, polyclinics, activeVisits] =
                await Promise.all([
                    // Total kunjungan hari ini
                    this.orm.searchCount("rs.clinic.visit", [
                        ["visit_date", "=", today],
                        ["state", "!=", "cancelled"],
                    ]),
                    // Menunggu antrian
                    this.orm.searchCount("rs.clinic.visit", [
                        ["visit_date", "=", today],
                        ["state", "in", ["registered", "queued"]],
                    ]),
                    // Sedang ditangani
                    this.orm.searchCount("rs.clinic.visit", [
                        ["visit_date", "=", today],
                        ["state", "=", "in_progress"],
                    ]),
                    // Selesai
                    this.orm.searchCount("rs.clinic.visit", [
                        ["visit_date", "=", today],
                        ["state", "=", "done"],
                    ]),
                    // Total pasien
                    this.orm.searchCount("rs.patient", []),
                    // Live stats per poli
                    this.orm.searchRead(
                        "rs.polyclinic",
                        [["active", "=", true]],
                        ["name", "visit_today_count", "queue_today_count"],
                        { order: "name asc" }
                    ),
                    // Detail Pasien Sedang Ditangani (Real Data)
                    this.orm.searchRead(
                        "rs.clinic.visit",
                        [
                            ["visit_date", "=", today],
                            ["state", "=", "in_progress"],
                        ],
                        ["id", "reference", "patient_id", "polyclinic_id", "doctor_id", "queue_number", "insurance_type"],
                        { order: "queue_number asc" }
                    )
                ]);

            this.state.visitTodayCount = visitToday;
            this.state.queueCount = waitingCount;
            this.state.inProgressCount = inProgressCount;
            this.state.doneCount = doneCount;
            this.state.patientCount = patientCount;
            this.state.polyclinics = polyclinics;
            this.state.activeVisits = activeVisits;
            this.state.isLoading = false;
        } catch (err) {
            console.warn("[rs_clinic] Dashboard stats gagal dimuat:", err);
            this.state.isLoading = false;
        }
    }

    openAction(xmlId) {
        this.action.doAction(xmlId);
    }

    openVisitDetail(visitId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "rs.clinic.visit",
            res_id: visitId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    openNewVisit() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Daftar Kunjungan Baru",
            res_model: "rs.clinic.visit",
            view_mode: "form",
            views: [[false, "form"]],
            target: "current",
        });
    }

    refreshData() {
        this.state.isLoading = true;
        this._loadData();
    }
}

registry.category("actions").add("rs_clinic_dashboard", RsClinicDashboard);
