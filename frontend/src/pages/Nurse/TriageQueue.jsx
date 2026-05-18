import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Clock,
  Users,
  AlertCircle,
  Search,
  Filter,
  Loader2,
} from "lucide-react";
import { api } from "../../utils/api";

const TriageQueue = () => {
  const navigate = useNavigate();
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [urgencyFilter, setUrgencyFilter] = useState("all");

  useEffect(() => {
    let mounted = true;

    const loadQueue = async () => {
      setLoading(true);
      setError("");
      try {
        const data = await api.get("/nurse/triage-queue");
        if (!mounted) return;
        setQueue(Array.isArray(data) ? data : []);
      } catch (err) {
        if (!mounted) return;
        console.error("Failed to load triage queue:", err);
        setError("Failed to load triage queue. Please try again.");
        setQueue([]);
      } finally {
        if (mounted) setLoading(false);
      }
    };

    loadQueue();
    const interval = setInterval(loadQueue, 30000); // Refresh every 30 seconds

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  // Filter queue based on search and urgency
  const filteredQueue = queue.filter((patient) => {
    const matchesSearch =
      patient.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      patient.patientId?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      patient.patient_id?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesUrgency =
      urgencyFilter === "all" ||
      (patient.urgency || "normal").toLowerCase() ===
        urgencyFilter.toLowerCase();

    return matchesSearch && matchesUrgency;
  });

  // Calculate stats
  const stats = {
    totalWaiting: queue.filter((p) => p.status === "awaiting_triage").length,
    critical: queue.filter(
      (p) =>
        (p.urgency === "critical" || p.urgency === "emergency") &&
        p.status === "awaiting_triage",
    ).length,
    high: queue.filter(
      (p) => p.urgency === "urgent" && p.status === "awaiting_triage",
    ).length,
    moderate: queue.filter(
      (p) =>
        (p.urgency === "normal" || !p.urgency) &&
        p.status === "awaiting_triage",
    ).length,
  };

  const handleStartTriage = (patient) => {
    const normalized = {
      id:
        patient.patientId ||
        patient.patient_id ||
        patient.patient_id ||
        patient.id,
      patientId: patient.patientId || patient.patient_id || patient.id,
      visit_id:
        patient.visit_id ||
        patient.visitId ||
        patient.visitId ||
        patient.visitId,
      name: patient.name || patient.patient_name || "",
      age: patient.age,
      gender: patient.gender || patient.sex || patient.sex,
      sex: patient.gender || patient.sex || patient.sex,
      contact: patient.contact,
      created_at: patient.created_at,
      arrivalTime: patient.created_at
        ? new Date(patient.created_at).toLocaleString()
        : patient.arrival_time || patient.arrivalTime,
      status: patient.status,
      urgency: patient.urgency,
    };
    navigate(`../triage/${normalized.patientId}`, {
      state: { patient: normalized },
    });
  };

  return (
    <div className="flex-1 overflow-auto bg-gray-50">
      {/* Header */}
      <div className="sticky top-0 z-20 bg-white border-b border-gray-200 px-6 py-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Clock size={24} className="text-blue-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Triage Queue</h1>
            <p className="text-sm text-gray-600">
              Patients awaiting triage assessment
            </p>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-600 font-medium">Total Waiting</p>
            <p className="text-2xl font-bold text-blue-900">
              {stats.totalWaiting}
            </p>
          </div>
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm text-red-600 font-medium">Critical</p>
            <p className="text-2xl font-bold text-red-900">{stats.critical}</p>
          </div>
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <p className="text-sm text-orange-600 font-medium">High</p>
            <p className="text-2xl font-bold text-orange-900">{stats.high}</p>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-sm text-green-600 font-medium">Moderate</p>
            <p className="text-2xl font-bold text-green-900">
              {stats.moderate}
            </p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search
              size={18}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
            />
            <input
              type="text"
              placeholder="Search by name or patient ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-sm"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter size={18} className="text-gray-500" />
            <select
              value={urgencyFilter}
              onChange={(e) => setUrgencyFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
            >
              <option value="all">All Urgencies</option>
              <option value="critical">Critical</option>
              <option value="emergency">Emergency</option>
              <option value="urgent">Urgent</option>
              <option value="normal">Normal</option>
            </select>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertCircle size={20} className="text-red-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-red-900">Error</p>
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          </div>
        )}

        {loading ? (
          <div className="flex flex-col items-center justify-center py-12">
            <Loader2 size={32} className="text-blue-600 animate-spin mb-2" />
            <p className="text-gray-600">Loading triage queue...</p>
          </div>
        ) : filteredQueue.length === 0 ? (
          <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
            <Users size={48} className="mx-auto mb-4 text-gray-400" />
            <p className="text-gray-600 font-medium">
              {searchTerm || urgencyFilter !== "all"
                ? "No patients match your filters"
                : "No patients awaiting triage"}
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                      Name
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                      Patient ID
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                      Age
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                      Gender
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                      Time
                    </th>
                    <th className="px-6 py-3 text-right text-sm font-semibold text-gray-700">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {filteredQueue.map((patient) => {
                    const createdDate = patient.created_at
                      ? new Date(patient.created_at)
                      : null;
                    const dateStr = createdDate
                      ? createdDate.toLocaleDateString()
                      : "—";
                    const timeStr = createdDate
                      ? createdDate.toLocaleTimeString()
                      : "—";

                    return (
                      <tr
                        key={patient.patientId || patient.patient_id}
                        className="hover:bg-gray-50 transition-colors"
                      >
                        <td className="px-6 py-4 text-sm font-medium text-gray-900">
                          {patient.name || "Unknown"}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600 font-mono">
                          {patient.patientId || patient.patient_id}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600">
                          {patient.age || "—"}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600">
                          {patient.sex || patient.gender || "—"}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600">
                          {dateStr}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600">
                          {timeStr}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <button
                            onClick={() => handleStartTriage(patient)}
                            className="px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 transition-colors"
                          >
                            Start Triage
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TriageQueue;
