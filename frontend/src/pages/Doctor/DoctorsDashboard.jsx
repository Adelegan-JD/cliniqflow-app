import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Activity,
  CheckCircle2,
  Clock3,
  ClipboardCheck,
  UsersRound,
} from "lucide-react";
import WelcomeBanner from "../../components/WelcomeBanner";
import { useUserProfile } from "../../hooks/useUserProfile";
import { api } from "../../utils/api";

const DoctorsDashboard = () => {
  const navigate = useNavigate();
  const userProfile = useUserProfile();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [stats, setStats] = useState({
    totalPatientsToday: 0,
    awaitingTriage: 0,
    awaitingConsultation: 0,
    visitsEnded: 0,
  });
  const [nurseQueue, setNurseQueue] = useState([]);
  const [triagedQueue, setTriagedQueue] = useState([]);

  useEffect(() => {
    let mounted = true;

    const normalizeStats = (data = {}) => ({
      totalPatientsToday:
        data.totalPatientsToday ??
        data.totalPatients ??
        data.totalPatientsForDay ??
        data.patientsAvailable ??
        0,
      awaitingTriage:
        data.awaitingTriage ??
        data.patientsAwaitingTriage ??
        data.triageQueue ??
        0,
      awaitingConsultation:
        data.awaitingConsultation ??
        data.patientsAwaitingConsultation ??
        data.consultationQueue ??
        data.awaitingDoctor ??
        0,
      visitsEnded:
        data.visitsEnded ?? data.completedVisits ?? data.endedVisits ?? 0,
    });

    const loadDoctorStats = async () => {
      setLoading(true);
      setError("");
      setStats({
        totalPatientsToday: 6,
        awaitingTriage: 2,
        awaitingConsultation: 2,
        visitsEnded: 2,
      });

      try {
        const [statsData, nurseQueueData, triagedQueueData] = await Promise.all(
          [
            api.get("/doctor/stats"),
            api.get("/doctor/nurse-queue-awareness"),
            api.get("/doctor/triaged-queue"),
          ],
        );
        if (!mounted) return;
        setStats(normalizeStats(statsData));
        setNurseQueue(Array.isArray(nurseQueueData) ? nurseQueueData : []);
        setTriagedQueue(
          Array.isArray(triagedQueueData) ? triagedQueueData : [],
        );
      } catch (_) {
        if (!mounted) return;
        setError(
          "Doctor stats service is unavailable. Showing default values.",
        );
        // Keep fallback aligned with current dummy queue in PatientsQueue
        setStats({
          totalPatientsToday: 6,
          awaitingTriage: 2,
          awaitingConsultation: 2,
          visitsEnded: 2,
        });
        setNurseQueue([]);
        setTriagedQueue([]);
      } finally {
        if (mounted) setLoading(false);
      }
    };

    loadDoctorStats();

    return () => {
      mounted = false;
    };
  }, []);

  const cards = useMemo(
    () => [
      {
        title: "Total Patients (Today)",
        value: stats.totalPatientsToday,
        icon: <UsersRound size={28} />,
        color: "bg-blue-500",
      },
      {
        title: "Awaiting Triage",
        value: stats.awaitingTriage,
        icon: <ClipboardCheck size={28} />,
        color: "bg-amber-500",
      },
      {
        title: "Awaiting Consultation",
        value: stats.awaitingConsultation,
        icon: <Clock3 size={28} />,
        color: "bg-emerald-500",
      },
      {
        title: "Visits Ended",
        value: stats.visitsEnded,
        icon: <CheckCircle2 size={28} />,
        color: "bg-slate-500",
      },
    ],
    [stats],
  );

  const handleStartConsultation = async (patient) => {
    if (!patient?.visit_id || !patient?.patient_id) return;

    try {
      await api.post(
        `/doctor/start-exam?visit_id=${encodeURIComponent(patient.visit_id)}`,
      );
    } catch (_) {
      // Non-blocking: allow navigation even if start-exam cannot be persisted now
    }

    navigate(
      `/doctors-dashboard/recording-session/${patient.patient_id}/${patient.visit_id}`,
      { state: { patient } },
    );
  };

  return (
    <div className="transition-all duration-300 p-4 overflow-auto w-full">
      <header className="mb-8">
        <WelcomeBanner user={userProfile} />
        <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-2">
          <Activity className="text-blue-600" />
          Doctor Dashboard
        </h1>
        <p className="text-gray-500 mt-1">
          Welcome Dr. {userProfile?.name || "Doctor"}, here is your patient
          queue overview.
        </p>
      </header>

      {/* {error ? (
        <div className="mb-6 p-4 bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 rounded-md">
          {error}
        </div>
      ) : null} */}

      <section className="mb-6">
        <h2 className="text-lg font-semibold text-gray-700 mb-4">
          Today's Overview
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
          {cards.map((card) => (
            <StatCard
              key={card.title}
              title={card.title}
              count={loading ? "—" : card.value}
              icon={card.icon}
              color={card.color}
            />
          ))}
        </div>
      </section>

      {error ? (
        <div className="mb-6 p-4 bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 rounded-md">
          {error}
        </div>
      ) : null}

      {/* Nurse Queue Awareness Section */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-700">
            Nurse Triage Queue (Awareness)
          </h2>
          <span className="text-sm text-gray-500">
            {nurseQueue.length}{" "}
            {nurseQueue.length === 1 ? "patient" : "patients"}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left min-w-full">
            <thead className="bg-gray-50 text-gray-600 text-sm uppercase tracking-wider">
              <tr>
                <th className="px-4 py-3">Patient Name</th>
                <th className="px-4 py-3">Patient ID</th>
                <th className="px-4 py-3">Age / Gender</th>
                <th className="px-4 py-3">Urgency</th>
                <th className="px-4 py-3">Registered</th>
                <th className="px-4 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {nurseQueue.length > 0 ? (
                nurseQueue.map((patient) => (
                  <tr
                    key={`${patient.patient_id}-${patient.created_at || ""}`}
                    className="hover:bg-gray-50"
                  >
                    <td className="px-4 py-3 font-medium text-gray-900">
                      {patient.name || "Unknown"}
                    </td>
                    <td className="px-4 py-3 text-gray-700 font-mono text-sm">
                      {patient.patientId || patient.patient_id}
                    </td>
                    <td className="px-4 py-3 text-gray-700">
                      {patient.age || "—"} /{" "}
                      {patient.sex || patient.gender || "—"}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-semibold uppercase ${
                          patient.urgency === "critical" ||
                          patient.urgency === "emergency"
                            ? "bg-red-100 text-red-700 border border-red-200"
                            : patient.urgency === "urgent"
                              ? "bg-amber-100 text-amber-700 border border-amber-200"
                              : "bg-green-100 text-green-700 border border-green-200"
                        }`}
                      >
                        {patient.urgency || "normal"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600 text-sm">
                      {patient.created_at
                        ? new Date(patient.created_at).toLocaleString()
                        : "—"}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        disabled
                        className="px-4 py-2 bg-gray-200 text-gray-500 text-sm font-semibold rounded-lg cursor-not-allowed"
                        title="Nurses handle triage. Doctors can only monitor this queue."
                      >
                        Start Triage (Disabled)
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td
                    className="px-4 py-3 text-gray-500 text-center"
                    colSpan={6}
                  >
                    No patients in nurse triage queue.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Triaged Queue Section */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-700">
            Triaged Queue (Ready for Consultation)
          </h2>
          <span className="text-sm text-gray-500">
            {triagedQueue.length}{" "}
            {triagedQueue.length === 1 ? "patient" : "patients"}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left min-w-full">
            <thead className="bg-gray-50 text-gray-600 text-sm uppercase tracking-wider">
              <tr>
                <th className="px-4 py-3">Patient Name</th>
                <th className="px-4 py-3">Patient ID</th>
                <th className="px-4 py-3">Age / Gender</th>
                <th className="px-4 py-3">Urgency Level</th>
                <th className="px-4 py-3">Triaged At</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {triagedQueue.length > 0 ? (
                triagedQueue.map((patient) => (
                  <tr
                    key={`${patient.patient_id}-${patient.visit_id}`}
                    className="hover:bg-gray-50"
                  >
                    <td className="px-4 py-3 font-medium text-gray-900">
                      {patient.patient_name}
                    </td>
                    <td className="px-4 py-3 text-gray-700 font-mono text-sm">
                      {patient.patient_id}
                    </td>
                    <td className="px-4 py-3 text-gray-700">
                      {patient.age || "—"} / {patient.gender || "—"}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-semibold uppercase ${
                          patient.urgency_level === "emergency"
                            ? "bg-red-100 text-red-700 border border-red-200"
                            : patient.urgency_level === "urgent"
                              ? "bg-amber-100 text-amber-700 border border-amber-200"
                              : "bg-green-100 text-green-700 border border-green-200"
                        }`}
                      >
                        {patient.urgency_level || "normal"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600 text-sm">
                      {patient.triaged_at
                        ? new Date(patient.triaged_at).toLocaleString()
                        : "—"}
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-700">
                        Ready
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        onClick={() => handleStartConsultation(patient)}
                        className="px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm font-bold hover:bg-emerald-700 shadow-sm active:scale-95 transition-all"
                      >
                        Start Consultation
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td
                    className="px-4 py-3 text-gray-500 text-center"
                    colSpan={7}
                  >
                    No patients in triaged queue.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};

const StatCard = ({ title, count, icon, color }) => (
  <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 relative overflow-hidden group">
    <div
      className={`absolute right-0 top-0 w-24 h-24 transform translate-x-8 -translate-y-8 rounded-full opacity-10 ${color}`}
    />
    <div className="relative z-10 flex justify-between items-start">
      <div>
        <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">
          {title}
        </p>
        <h3 className="text-3xl font-bold text-gray-900 mt-2">{count}</h3>
      </div>
      <div className={`p-3 rounded-lg text-white shadow-lg ${color}`}>
        {icon}
      </div>
    </div>
  </div>
);

export default DoctorsDashboard;
