import React, { useState, useEffect } from "react";
import { api } from "../utils/api";
import { FileText, AlertTriangle, Clock, CheckCircle, Users, Search, ChevronDown, ChevronUp } from "lucide-react";

export default function TriageRecords() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [urgencyFilter, setUrgencyFilter] = useState("");
  const [search, setSearch] = useState("");
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const timer = setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams();
        if (urgencyFilter) params.set("urgency", urgencyFilter);
        if (search.trim()) params.set("search", search.trim());
        const data = await api.get(`/nurse/triage-records?${params.toString()}`);
        if (!cancelled) setRecords(Array.isArray(data) ? data : []);
      } catch (e) {
        if (!cancelled) {
          setError(e?.message || "Failed to load triage records");
          setRecords([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }, search ? 400 : 0);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [urgencyFilter, search]);

  const emergencyCount = records.filter((r) => r.urgencyLevel === "emergency").length;
  const urgentCount = records.filter((r) => r.urgencyLevel === "urgent").length;
  const normalCount = records.filter((r) => r.urgencyLevel === "normal").length;

  return (
    <div className="space-y-6">
      {/* Summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 flex items-center gap-4">
          <div className="p-3 bg-slate-100 rounded-lg">
            <FileText className="text-slate-600" size={24} />
          </div>
          <div>
            <p className="text-slate-600 text-sm font-medium">Total Triaged</p>
            <p className="text-2xl font-bold text-slate-800">{records.length}</p>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-red-200 shadow-sm p-4 flex items-center gap-4">
          <div className="p-3 bg-red-100 rounded-lg">
            <AlertTriangle className="text-red-600" size={24} />
          </div>
          <div>
            <p className="text-slate-600 text-sm font-medium">Emergency</p>
            <p className="text-2xl font-bold text-red-700">{emergencyCount}</p>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-amber-200 shadow-sm p-4 flex items-center gap-4">
          <div className="p-3 bg-amber-100 rounded-lg">
            <Clock className="text-amber-600" size={24} />
          </div>
          <div>
            <p className="text-slate-600 text-sm font-medium">Urgent</p>
            <p className="text-2xl font-bold text-amber-700">{urgentCount}</p>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-green-200 shadow-sm p-4 flex items-center gap-4">
          <div className="p-3 bg-green-100 rounded-lg">
            <CheckCircle className="text-green-600" size={24} />
          </div>
          <div>
            <p className="text-slate-600 text-sm font-medium">Normal</p>
            <p className="text-2xl font-bold text-green-700">{normalCount}</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 flex flex-wrap gap-4 items-center">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
          <input
            type="text"
            placeholder="Search by name or PID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10 pr-4 py-2 w-full border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-sm"
          />
        </div>
        <select
          value={urgencyFilter}
          onChange={(e) => setUrgencyFilter(e.target.value)}
          className="px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
        >
          <option value="">All urgency levels</option>
          <option value="emergency">Emergency</option>
          <option value="urgent">Urgent</option>
          <option value="normal">Normal</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="px-6 py-5 border-b border-slate-100 bg-slate-50/50">
          <h2 className="font-bold text-slate-700 flex items-center gap-2">
            <FileText size={18} className="text-blue-500" />
            Triage Records
          </h2>
        </div>

        {loading ? (
          <div className="px-6 py-12 text-center text-slate-500">Loading records...</div>
        ) : error ? (
          <div className="px-6 py-12 text-center text-amber-600">{error}</div>
        ) : records.length === 0 ? (
          <div className="px-6 py-12 text-center text-slate-500">
            No triage records yet. Complete a triage from the queue to see records here.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-white text-slate-400 text-[11px] uppercase tracking-widest border-b border-slate-100">
                <tr>
                  <th className="px-6 py-4 font-bold text-slate-300">#</th>
                  <th className="px-6 py-4 font-bold text-slate-500">Patient</th>
                  <th className="px-6 py-4 font-bold text-center">Age / Gender</th>
                  <th className="px-6 py-4 font-bold">Vitals</th>
                  <th className="px-6 py-4 font-bold">Urgency</th>
                  <th className="px-6 py-4 font-bold">Triaged</th>
                  <th className="px-6 py-4 font-bold w-12"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {records.map((r) => (
                  <React.Fragment key={r.id}>
                    <tr className="hover:bg-slate-50 transition-all">
                      <td className="px-6 py-4 text-slate-400 font-mono text-xs">{r.pid || "—"}</td>
                      <td className="px-6 py-4 font-semibold text-slate-800">{r.name}</td>
                      <td className="px-6 py-4 text-center text-slate-600">
                        {r.age ?? "—"} / {(r.gender || "").charAt(0) || "—"}
                      </td>
                      <td className="px-6 py-4 text-slate-600 text-sm">{r.vitalsSummary || "—"}</td>
                      <td className="px-6 py-4">
                        <span
                          className={`px-3 py-1 rounded-full text-[10px] uppercase font-semibold ${
                            r.urgencyLevel === "emergency"
                              ? "bg-red-100 text-red-700 border border-red-200"
                              : r.urgencyLevel === "urgent"
                                ? "bg-amber-100 text-amber-700 border border-amber-200"
                                : "bg-green-100 text-green-700 border border-green-200"
                          }`}
                        >
                          {r.urgencyLevel || "normal"}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-slate-600 text-sm">{r.triagedAt || "—"}</td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => setExpandedId(expandedId === r.id ? null : r.id)}
                          className="p-1.5 text-slate-400 hover:bg-slate-100 rounded"
                        >
                          {expandedId === r.id ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                        </button>
                      </td>
                    </tr>
                    {expandedId === r.id && r.vitals && (
                      <tr className="bg-slate-50">
                        <td colSpan={7} className="px-6 py-4">
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            {r.vitals.temperature && <div><span className="text-slate-500">Temp:</span> {r.vitals.temperature}°C</div>}
                            {(r.vitals.bpSystolic || r.vitals.bpDiastolic) && (
                              <div><span className="text-slate-500">BP:</span> {r.vitals.bpSystolic}/{r.vitals.bpDiastolic} mmHg</div>
                            )}
                            {r.vitals.heartRate && <div><span className="text-slate-500">HR:</span> {r.vitals.heartRate} bpm</div>}
                            {r.vitals.respiratoryRate && <div><span className="text-slate-500">RR:</span> {r.vitals.respiratoryRate}</div>}
                            {r.vitals.weight && <div><span className="text-slate-500">Weight:</span> {r.vitals.weight} kg</div>}
                            {r.vitals.height && <div><span className="text-slate-500">Height:</span> {r.vitals.height} cm</div>}
                            {r.vitals.bmi && <div><span className="text-slate-500">BMI:</span> {r.vitals.bmi}</div>}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
