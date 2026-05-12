import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ClipboardList, FileText, Stethoscope, AlertCircle, Loader2 } from "lucide-react";
import { api } from "../../utils/api";

const statusPriority = {
  awaiting_consultation: 1,
  awaiting_triage: 2,
  visit_ended: 3,
};

const statusMeta = {
  awaiting_consultation: {
    label: "Ready for Consultation",
    badge: "bg-emerald-100 text-emerald-700 border-emerald-200",
  },
  awaiting_triage: {
    label: "Awaiting Triage",
    badge: "bg-amber-100 text-amber-700 border-amber-200",
  },
  visit_ended: {
    label: "Visit Ended",
    badge: "bg-gray-100 text-gray-700 border-gray-200",
  },
};

const PatientsQueue = () => {
  const navigate = useNavigate();
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    const fetchQueue = async () => {
      try {
        setLoading(true);
        const data = await api.get("/doctor/triaged-queue");
        if (!cancelled) {
          setPatients(data?.queue || []);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message || "Failed to load patient queue");
          setPatients([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchQueue();
    return () => { cancelled = true; };
  }, []);

  const sortedPatients = useMemo(() => {
    return [...patients].sort(
      (a, b) => (statusPriority[a.status] || 999) - (statusPriority[b.status] || 999)
    );
  }, [patients]);

  // Loading State
  if (loading) {
    return (
      <div className="flex flex-col flex-1 p-8 items-center justify-center">
        <Loader2 className="text-blue-600 animate-spin mb-2" size={32} />
        <p className="text-gray-500 font-medium">Loading patient queue...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col flex-1 p-4 md:p-6 overflow-auto bg-gray-50/50">
      {/* Header Section */}
      <div className="mb-6">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-800 flex items-center gap-2">
          <ClipboardList className="text-blue-600" size={28} />
          Patient Queue
        </h1>
        <p className="text-gray-600 mt-1">
          Patients are automatically prioritized by care readiness.
        </p>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
          <AlertCircle className="text-red-600 shrink-0 mt-0.5" size={20} />
          <div>
            <p className="font-semibold text-red-900">Error loading queue</p>
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Queue Table Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-6 border-b border-gray-200 flex flex-wrap items-center gap-3">
          <h2 className="text-xl font-semibold flex items-center gap-2 mr-auto text-gray-800">
            <Stethoscope size={20} className="text-blue-500" />
            Queue Overview
          </h2>
          <span className="text-sm font-medium text-blue-700 bg-blue-50 px-3 py-1 rounded-full border border-blue-100">
            {sortedPatients.length} Patients Total
          </span>
        </div>

        {sortedPatients.length === 0 && !error ? (
          <div className="p-12 text-center text-gray-500">
            <p className="font-medium text-lg text-gray-600">Queue is empty</p>
            <p className="text-sm mt-1">No patients are currently awaiting care.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left min-w-[900px]">
              <thead className="bg-gray-50 text-gray-600 text-xs uppercase tracking-wider font-semibold">
                <tr>
                  <th className="px-6 py-4">Name</th>
                  <th className="px-6 py-4">Patient ID</th>
                  <th className="px-6 py-4">Session ID</th>
                  <th className="px-6 py-4">Age/Sex</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4">Records</th>
                  <th className="px-6 py-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {sortedPatients.map((patient) => {
                  const patientKey = patient.sessionId || patient.patientId || Math.random();
                  const meta = statusMeta[patient.status] || { label: "Unknown", badge: "bg-gray-100" };
                  
                  return (
                    <tr key={patientKey} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 font-medium text-gray-900">
                        {patient.name || "Unknown Patient"}
                      </td>
                      <td className="px-6 py-4 text-gray-500 font-mono text-xs uppercase">
                        {patient.patientId || patient.pid}
                      </td>
                      <td className="px-6 py-4 text-gray-500 font-mono text-xs uppercase">
                        {patient.sessionId || "N/A"}
                      </td>
                      <td className="px-6 py-4 text-gray-700 text-sm">
                        {patient.age}y / {patient.sex}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-bold border ${meta.badge}`}>
                          {meta.label}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <button className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 font-semibold text-sm transition-colors">
                          <FileText size={14} />
                          View History
                        </button>
                      </td>
                      <td className="px-6 py-4 text-right">
                        {patient.status === "awaiting_consultation" ? (
                          <button
                            onClick={() => navigate(`/doctors-dashboard/recording-session/${patient.patientId}/${patient.sessionId}`, { state: { patient } })}
                            className="px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm font-bold hover:bg-emerald-700 shadow-sm active:scale-95 transition-all"
                          >
                            Start Consultation
                          </button>
                        ) : (
                          <span className="text-sm text-gray-400 italic">
                            {patient.status === "visit_ended" ? "Complete" : "Wait for Triage"}
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default PatientsQueue;