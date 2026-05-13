import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ClipboardList,
  FileText,
  Stethoscope,
  AlertCircle,
  Loader2,
  Search,
  Filter,
  Users,
  Clock,
} from "lucide-react";
import { api } from "../../utils/api";

const STATUS_META = {
  WITH_DOCTOR: {
    label: "Consultation",
    badge: "badge-success",
  },
  WAITING_FOR_DOCTOR: {
    label: "Ready for Consultation",
    badge: "badge-warning",
  },
  COMPLETED: {
    label: "Completed",
    badge: "badge-primary",
  },
  CANCELLED: {
    label: "Cancelled",
    badge: "badge-danger",
  },
};

const PatientsQueue = () => {
  const navigate = useNavigate();
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  useEffect(() => {
    let cancelled = false;

    const fetchQueue = async () => {
      try {
        setLoading(true);
        const data = await api.get("/doctor/queue");
        if (!cancelled) {
          setPatients(Array.isArray(data) ? data : []);
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
    return () => {
      cancelled = true;
    };
  }, []);

  const filteredPatients = useMemo(() => {
    return [...patients].filter((patient) => {
      const query = searchTerm.toLowerCase();
      const name = (patient.patient_name || patient.name || "").toLowerCase();
      const pid = (patient.patient_id || patient.patientId || "").toLowerCase();
      const vid = (patient.visit_id || patient.sessionId || "").toLowerCase();
      const status = (
        patient.visit_status ||
        patient.status ||
        ""
      ).toUpperCase();

      const matchesSearch =
        name.includes(query) || pid.includes(query) || vid.includes(query);
      const matchesStatus =
        statusFilter === "all" || status === statusFilter.toUpperCase();

      return matchesSearch && matchesStatus;
    });
  }, [patients, searchTerm, statusFilter]);

  const stats = useMemo(
    () => ({
      total: patients.length,
      ready: patients.filter(
        (p) => (p.visit_status || p.status) === "WAITING_FOR_DOCTOR",
      ).length,
      active: patients.filter(
        (p) => (p.visit_status || p.status) === "WITH_DOCTOR",
      ).length,
      completed: patients.filter(
        (p) => (p.visit_status || p.status) === "COMPLETED",
      ).length,
    }),
    [patients],
  );

  const handleStartConsultation = async (patient) => {
    const patientId = patient.patient_id || patient.patientId;
    const visitId = patient.visit_id || patient.sessionId;
    if (!patientId || !visitId) return;

    try {
      await api.post(
        `/doctor/start-exam?visit_id=${encodeURIComponent(visitId)}`,
      );
    } catch (_) {
      // Non-blocking: allow navigation if the exam is already active.
    }

    navigate(`/doctors-dashboard/recording-session/${patientId}/${visitId}`, {
      state: { patient },
    });
  };

  return (
    <div className="transition-all duration-300 p-4 md:p-6 overflow-auto w-full bg-gray-50/50">
      <header className="mb-8">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-blue-50 rounded-xl">
            <ClipboardList className="text-blue-600" size={32} />
          </div>
          <div>
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900">
              Patient Queue
            </h1>
            <p className="text-gray-600 mt-1">
              Here's a list of patients that are ready for consultation
            </p>
          </div>
        </div>
      </header>

      {error ? (
        <div className="alert alert-warning mb-6">
          <AlertCircle size={20} className="shrink-0" />
          <div>
            <p className="font-semibold">Error</p>
            <p className="text-sm">{error}</p>
          </div>
        </div>
      ) : null}

      <section className="mb-8">
        <div className="grid-responsive">
          <div className="stat-card">
            <div className="flex items-center gap-3">
              <div className="stat-card-icon">
                <Users size={20} />
              </div>
              <div>
                <p className="stat-card-label">Total in Queue</p>
                <p className="stat-card-value">{stats.total}</p>
              </div>
            </div>
          </div>
          <div className="stat-card">
            <div className="flex items-center gap-3">
              <div className="stat-card-icon bg-amber-100 text-amber-600">
                <Clock size={20} />
              </div>
              <div>
                <p className="stat-card-label">Ready</p>
                <p className="stat-card-value text-amber-600">{stats.ready}</p>
              </div>
            </div>
          </div>
          <div className="stat-card">
            <div className="flex items-center gap-3">
              <div className="stat-card-icon bg-emerald-100 text-emerald-600">
                <Stethoscope size={20} />
              </div>
              <div>
                <p className="stat-card-label">In Progress</p>
                <p className="stat-card-value text-emerald-600">
                  {stats.active}
                </p>
              </div>
            </div>
          </div>
          <div className="stat-card">
            <div className="flex items-center gap-3">
              <div className="stat-card-icon bg-slate-100 text-slate-600">
                <FileText size={20} />
              </div>
              <div>
                <p className="stat-card-label">Completed</p>
                <p className="stat-card-value text-slate-600">
                  {stats.completed}
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="card elevated p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              <Search size={16} className="inline mr-2" />
              Search by name or ID
            </label>
            <input
              type="text"
              placeholder="Enter patient name, patient ID, or visit ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field w-full"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              <Filter size={16} className="inline mr-2" />
              Filter by status
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input-field w-full"
            >
              <option value="all">All statuses</option>
              <option value="WAITING_FOR_DOCTOR">Ready for consultation</option>
              <option value="WITH_DOCTOR">In consultation</option>
              <option value="COMPLETED">Completed</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>
        </div>
      </section>

      <section className="card elevated">
        {loading ? (
          <div className="flex items-center justify-center p-12">
            <Loader2 size={32} className="animate-spin text-blue-600" />
            <span className="ml-3 text-gray-600 font-medium">
              Loading patient queue...
            </span>
          </div>
        ) : filteredPatients.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="table-modern">
              <thead>
                <tr>
                  <th>Patient Name</th>
                  <th>Patient ID</th>
                  <th>Visit ID</th>
                  <th>Age / Gender</th>
                  <th>Status</th>
                  <th>Registered</th>
                  <th className="text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredPatients.map((patient, index) => {
                  const visitStatus =
                    patient.visit_status ||
                    patient.status ||
                    "WAITING_FOR_DOCTOR";
                  const meta =
                    STATUS_META[visitStatus] || STATUS_META.WAITING_FOR_DOCTOR;
                  const patientId =
                    patient.patient_id || patient.patientId || "—";
                  const visitId = patient.visit_id || patient.sessionId || "—";

                  return (
                    <tr key={`${patientId}-${visitId}-${index}`}>
                      <td className="font-semibold text-gray-900">
                        {patient.patient_name ||
                          patient.name ||
                          "Unknown Patient"}
                      </td>
                      <td className="font-mono text-xs text-gray-700">
                        {patientId}
                      </td>
                      <td className="font-mono text-xs text-gray-700">
                        {visitId}
                      </td>
                      <td className="text-gray-700">
                        {patient.age || "—"} /{" "}
                        {patient.gender || patient.sex || "—"}
                      </td>
                      <td>
                        <span className={`badge ${meta.badge}`}>
                          {meta.label}
                        </span>
                      </td>
                      <td className="text-gray-600 text-sm">
                        {patient.created_at
                          ? new Date(patient.created_at).toLocaleString()
                          : "—"}
                      </td>
                      <td className="text-right">
                        <button
                          onClick={() => handleStartConsultation(patient)}
                          className="btn btn-primary btn-small"
                        >
                          {visitStatus === "WITH_DOCTOR"
                            ? "Continue Consultation"
                            : "Start Consultation"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-12 text-center text-gray-500">
            <p className="font-medium text-lg text-gray-600">
              No patients found
            </p>
            <p className="text-sm mt-1">
              {searchTerm || statusFilter !== "all"
                ? "Try adjusting your filters."
                : "No patients are currently waiting for consultation."}
            </p>
          </div>
        )}
      </section>
    </div>
  );
};

export default PatientsQueue;
