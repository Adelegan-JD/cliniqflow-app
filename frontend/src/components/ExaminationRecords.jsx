import React, { useState, useEffect } from "react";
import {
  FileText,
  Calendar,
  User,
  ChevronDown,
  ChevronUp,
  Activity,
  Pill,
  AlertTriangle,
  CheckCircle2,
  Stethoscope,
} from "lucide-react";
import { api } from "../utils/api";

const Section = ({ title, icon: Icon, children }) => (
  <div className="mb-6 last:mb-0">
    <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-2">
      {Icon && <Icon size={14} className="text-slate-400" />}
      {title}
    </h4>
    {children}
  </div>
);

const ExaminationRecords = () => {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    async function fetchRecords() {
      setLoading(true);
      setError(null);
      try {
        const data = await api.get("/doctor/examination-records");
        setRecords(Array.isArray(data) ? data : []);
      } catch (e) {
        setError(e?.message || "Failed to load examination records");
        setRecords([]);
      } finally {
        setLoading(false);
      }
    }
    fetchRecords();
  }, []);

  const formatDate = (created) => {
    if (!created) return "—";
    try {
      const d = new Date(created);
      return d.toLocaleDateString("en-NG", {
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return created;
    }
  };

  const formatVitals = (vitals) => {
    if (!vitals || typeof vitals !== "object") return null;
    const parts = [];
    if (vitals.temperature != null) parts.push(`Temp: ${vitals.temperature}°C`);
    if (vitals.bpSystolic != null && vitals.bpDiastolic != null)
      parts.push(`BP: ${vitals.bpSystolic}/${vitals.bpDiastolic} mmHg`);
    if (vitals.heartRate != null) parts.push(`HR: ${vitals.heartRate} bpm`);
    if (vitals.respiratoryRate != null)
      parts.push(`RR: ${vitals.respiratoryRate}/min`);
    if (vitals.weight != null || vitals.weight_kg != null)
      parts.push(`Weight: ${vitals.weight ?? vitals.weight_kg} kg`);
    if (vitals.height != null || vitals.height_cm != null)
      parts.push(`Height: ${vitals.height ?? vitals.height_cm} cm`);
    if (vitals.bmi != null) parts.push(`BMI: ${vitals.bmi}`);
    return parts.length ? parts.join(" · ") : null;
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
          <FileText size={22} className="text-blue-500" />
          Examination Records
        </h2>
        <p className="text-slate-500 text-sm mt-1">
          Full consultation records: triage, transcript, SOAP, prescriptions
        </p>
      </div>

      {loading ? (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-12 text-center text-slate-500">
          Loading records…
        </div>
      ) : error ? (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-12 text-center text-amber-600">
          {error}
        </div>
      ) : records.length === 0 ? (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-12 text-center text-slate-500">
          No completed examinations yet. Finish a consultation to see records here.
        </div>
      ) : (
        <div className="space-y-3">
          {records.map((r) => (
            <div
              key={r.id}
              className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden"
            >
              <button
                onClick={() => setExpandedId(expandedId === r.id ? null : r.id)}
                className="w-full px-6 py-4 flex items-center justify-between hover:bg-slate-50 transition-colors text-left"
              >
                <div className="flex items-center gap-4">
                  <div className="bg-blue-50 p-2 rounded-lg text-blue-600">
                    <User size={20} />
                  </div>
                  <div>
                    <p className="font-bold text-slate-800">
                      {r.patient_name || "Unknown"}
                    </p>
                    <p className="text-sm text-slate-500">
                      {r.pid && `#${r.pid}`} · {r.age != null && `${r.age} yrs`}{" "}
                      {r.gender && `· ${r.gender}`} · Visit {r.visit_id?.slice(0, 8)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-xs text-slate-400 flex items-center gap-1">
                    <Calendar size={14} />
                    {formatDate(r.created_at)}
                  </span>
                  {expandedId === r.id ? (
                    <ChevronUp size={20} className="text-slate-400" />
                  ) : (
                    <ChevronDown size={20} className="text-slate-400" />
                  )}
                </div>
              </button>

              {expandedId === r.id && (
                <div className="px-6 pb-6 pt-0 border-t border-slate-100 space-y-6">
                  {/* Patient basic details */}
                  <Section title="Patient Details" icon={User}>
                    <div className="bg-slate-50 p-4 rounded-lg text-sm text-slate-700 space-y-1">
                      <p><strong>Name:</strong> {r.patient_name || "—"}</p>
                      <p><strong>PID:</strong> {r.pid ?? "—"}</p>
                      <p><strong>Age:</strong> {r.age ?? "—"}</p>
                      <p><strong>Gender:</strong> {r.gender || "—"}</p>
                      {r.date_of_birth && (
                        <p><strong>DOB:</strong> {r.date_of_birth}</p>
                      )}
                      {r.phone_number && (
                        <p><strong>Phone:</strong> {r.phone_number}</p>
                      )}
                      <p><strong>Visit ID:</strong> <code className="text-xs bg-slate-200 px-1 rounded">{r.visit_id}</code></p>
                    </div>
                  </Section>

                  {/* Nurse triage data */}
                  {r.triage_data && (
                    <Section title="Nurse Triage" icon={Stethoscope}>
                      <div className="bg-slate-50 p-4 rounded-lg text-sm">
                        <p className="text-slate-700 mb-2">
                          <strong>Vitals:</strong>{" "}
                          {formatVitals(r.triage_data.vitals) || "—"}
                        </p>
                        <p className="text-slate-700">
                          <strong>Urgency:</strong>{" "}
                          <span
                            className={`px-2 py-0.5 rounded text-xs font-semibold ${
                              r.triage_data.urgency_level === "emergency"
                                ? "bg-red-100 text-red-700"
                                : r.triage_data.urgency_level === "urgent"
                                ? "bg-amber-100 text-amber-700"
                                : "bg-slate-200 text-slate-700"
                            }`}
                          >
                            {r.triage_data.urgency_level || "normal"}
                          </span>
                        </p>
                      </div>
                    </Section>
                  )}

                  {/* Transcript */}
                  <Section title="Consultation Transcript" icon={FileText}>
                    <div className="bg-slate-50 p-4 rounded-lg text-slate-700 whitespace-pre-wrap text-sm leading-relaxed">
                      {r.transcript_full || "—"}
                    </div>
                  </Section>

                  {/* SOAP summary */}
                  {r.soap_json && (
                    <Section title="SOAP Summary" icon={Activity}>
                      <div className="space-y-3 text-sm">
                        {["subjective", "objective", "assessment", "plan"].map(
                          (key) => (
                            <div key={key}>
                              <p className="font-bold text-slate-600 uppercase text-xs mb-1">
                                {key === "subjective" && "S — Subjective"}
                                {key === "objective" && "O — Objective"}
                                {key === "assessment" && "A — Assessment"}
                                {key === "plan" && "P — Plan"}
                              </p>
                              <p className="text-slate-700 whitespace-pre-wrap bg-slate-50 p-3 rounded-lg">
                                {r.soap_json[key] || "—"}
                              </p>
                            </div>
                          )
                        )}
                      </div>
                    </Section>
                  )}

                  {/* Doctor notes */}
                  {r.doctor_notes && (
                    <Section title="Doctor Notes" icon={FileText}>
                      <div className="bg-amber-50 p-4 rounded-lg text-slate-700 whitespace-pre-wrap text-sm">
                        {r.doctor_notes}
                      </div>
                    </Section>
                  )}

                  {/* Prescriptions */}
                  {r.prescriptions_json && r.prescriptions_json.length > 0 && (
                    <Section title="Prescribed Medications" icon={Pill}>
                      <div className="space-y-3">
                        {r.prescriptions_json.map((rx, idx) => (
                          <div
                            key={idx}
                            className="bg-slate-50 p-4 rounded-lg border-l-4 border-blue-200"
                          >
                            <div className="flex items-start justify-between gap-4">
                              <div>
                                <p className="font-bold text-slate-800">
                                  {rx.drug_name}
                                </p>
                                <p className="text-sm text-slate-600">
                                  {rx.dose_mg_per_day} mg/day · {rx.frequency_per_day}x/day
                                  {rx.duration_days && ` × ${rx.duration_days} days`}
                                </p>
                              </div>
                              <span
                                className={`shrink-0 px-2 py-1 rounded text-xs font-semibold flex items-center gap-1 ${
                                  rx.is_safe
                                    ? "bg-green-100 text-green-700"
                                    : "bg-amber-100 text-amber-700"
                                }`}
                              >
                                {rx.is_safe ? (
                                  <CheckCircle2 size={12} />
                                ) : (
                                  <AlertTriangle size={12} />
                                )}
                                {rx.is_safe ? "Safe" : "Override"}
                              </span>
                            </div>
                            {rx.dose_check_result &&
                              (rx.dose_check_result.warnings?.length > 0 ||
                                rx.dose_check_result.recommended_range_mg_per_day) && (
                              <div className="mt-2 pt-2 border-t border-slate-200 text-xs text-slate-600">
                                <p>
                                  <strong>Dose check:</strong>{" "}
                                  {rx.dose_check_result.safe ? "Safe" : "Warning"}
                                </p>
                                {rx.dose_check_result.warnings?.length > 0 && (
                                  <p className="text-amber-700 mt-1">
                                    {rx.dose_check_result.warnings.join(". ")}
                                  </p>
                                )}
                                {rx.dose_check_result.recommended_range_mg_per_day && (
                                  <p className="mt-1">
                                    Recommended: {rx.dose_check_result.recommended_range_mg_per_day.min}–
                                    {rx.dose_check_result.recommended_range_mg_per_day.max} mg/day
                                  </p>
                                )}
                              </div>
                            )}
                            {rx.override_reason && (
                              <div className="mt-2 pt-2 border-t border-amber-200 text-xs">
                                <p className="text-amber-700">
                                  <strong>Override reason:</strong> {rx.override_reason}
                                </p>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </Section>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ExaminationRecords;
