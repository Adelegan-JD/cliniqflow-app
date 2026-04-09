import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
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
import { supabase } from "../../utils/supabaseClient";

export const NurseDashboard = () => {
  const userProfile = useUserProfile();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [stats, setStats] = useState({
    totalPatientsToday: 0,
    awaitingTriage: 0,
    awaitingConsultation: 0,
    visitsEnded: 0,
  });
  const [triageQueue, setTriageQueue] = useState([]);
  const [triageRecords, setTriageRecords] = useState([]);

  const navigate = useNavigate();
  const location = useLocation();

  const defaultTriageQueue = [
    {
      patientId: "PT-002-TO",
      name: "Tunde Okafor",
      age: 41,
      sex: "Male",
      status: "awaiting_triage",
      urgency: "urgent",
    },
    {
      patientId: "PT-005-CE",
      name: "Chioma Eze",
      age: 22,
      sex: "Female",
      status: "awaiting_triage",
      urgency: "routine",
    },
    {
      patientId: "PT-007-MA",
      name: "Maryam Abubakar",
      age: 30,
      sex: "Female",
      status: "awaiting_triage",
      urgency: "critical",
    },
  ];

  const handleCompleteTriage = (patientId) => {
    setTriageQueue((prevQueue) =>
      prevQueue.map((patient) =>
        patient.patientId === patientId
          ? { ...patient, status: "triaged" }
          : patient,
      ),
    );
    setStats((prev) => ({
      ...prev,
      awaitingTriage: Math.max(prev.awaitingTriage - 1, 0),
      awaitingConsultation: prev.awaitingConsultation + 1,
    }));
  };

  const handleStartTriage = (patient) => {
    navigate(`triage/${patient.patientId}`, {
      state: { patient },
    });
  };

  const normalizeStats = (data = {}) => ({
    totalPatientsToday:
      data.totalPatientsToday ?? data.totalPatients ?? data.patientsAvailable ?? 0,
    awaitingTriage:
      data.awaitingTriage ?? data.patientsAwaitingTriage ?? data.triageQueue ?? 0,
    awaitingConsultation:
      data.awaitingConsultation ?? data.patientsAwaitingConsultation ?? data.consultationQueue ?? 0,
    visitsEnded: data.visitsEnded ?? data.completedVisits ?? data.endedVisits ?? 0,
  });

  useEffect(() => {
    let mounted = true;

    const loadNurseStats = async () => {
      setLoading(true);
      setError("");

      // default fallback shown in case API is unavailable
      const fallbackStats = {
        totalPatientsToday: 6,
        awaitingTriage: 3,
        awaitingConsultation: 2,
        visitsEnded: 2,
      };

      setStats(fallbackStats);
      setTriageQueue(defaultTriageQueue);

      try {
        if (import.meta.env.CLINIQ_AUTH_MODE === "supabase") {
          const { data: queueData, error: queueError } = await supabase
            .from("nurse_triage_queue")
            .select("*");

          if (queueError) throw queueError;

          const { data: recordsData, error: recordsError } = await supabase
            .from("nurse_triage_records")
            .select("*");

          if (recordsError) throw recordsError;

          const awaitingTriage = queueData.filter((p) => p.status === "awaiting_triage").length;
          const triagedCount = queueData.filter((p) => p.status === "triaged").length;
          const visitsEnded = recordsData.filter((r) => r.urgencyLevel === "normal").length;

          if (!mounted) return;
          setStats({
            totalPatientsToday: awaitingTriage + triagedCount + visitsEnded,
            awaitingTriage,
            awaitingConsultation: triagedCount,
            visitsEnded,
          });
          if (!mounted) return;
          setTriageQueue(queueData || defaultTriageQueue);
          if (!mounted) return;
          setTriageRecords(recordsData || []);
        } else {
          const data = await api.get("/nurse/stats");
          if (!mounted) return;
          setStats(normalizeStats(data));

          try {
            const queueData = await api.get("/nurse/triage-queue");
            if (!mounted) return;
            setTriageQueue(Array.isArray(queueData) ? queueData : defaultTriageQueue);

            const recordsData = await api.get("/nurse/triage-records");
            if (!mounted) return;
            setTriageRecords(Array.isArray(recordsData) ? recordsData : []);
          } catch (_) {
            if (!mounted) return;
            setTriageQueue(defaultTriageQueue);
            setTriageRecords([]);
          }
        }
      } catch (error) {
        if (!mounted) return;
        console.error("Nurse stats fetch failed", error);
        if (!mounted) return;
        setError("Nurse stats service is unavailable. Showing fallback values.");
        setStats(fallbackStats);
        setTriageQueue(defaultTriageQueue);
      } finally {
        if (mounted) setLoading(false);
      }
    };

    loadNurseStats();

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (location.state?.triagedPatient) {
      const triagedPatient = location.state.triagedPatient;
      setTriageQueue((prev) =>
        prev.map((patient) =>
          patient.patientId === triagedPatient.patientId
            ? {
                ...patient,
                status: "triaged",
                urgency: triagedPatient.urgency || "normal",
              }
            : patient,
        ),
      );
      setStats((prev) => ({
        ...prev,
        awaitingTriage: Math.max(prev.awaitingTriage - 1, 0),
        awaitingConsultation: prev.awaitingConsultation + 1,
      }));
      // refresh from backend for consistency
      (async () => {
        try {
          const data = await api.get("/nurse/stats");
          setStats(normalizeStats(data));
          const queueData = await api.get("/nurse/triage-queue");
          setTriageQueue(Array.isArray(queueData) ? queueData : defaultTriageQueue);
        } catch (_) {
          // keep local changes if backend unavailable
        }
      })();

      navigate("/nurse-dashboard", { replace: true, state: null });
    }
  }, [location.state, navigate]);

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

  return (
    <div className="transition-all duration-300 p-4 overflow-auto w-full">
      <header className="mb-8">
        <WelcomeBanner user={userProfile} />
        <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-2">
          <Activity className="text-blue-600" />
          Nurse Dashboard
        </h1>
        <p className="text-gray-500 mt-1">
          Welcome {userProfile?.name || "Nurse"}, here is your current triage overview.
        </p>
      </header>

      {error ? (
        <div className="mb-6 p-4 bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 rounded-md">
          {error}
        </div>
      ) : null}

      <section className="mb-6">
        <h2 className="text-lg font-semibold text-gray-700 mb-4">Today's Overview</h2>
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

      <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-700">Triage Queue</h2>
          <span className="text-sm text-gray-500">
            {triageQueue.filter((item) => item.status === "awaiting_triage").length} waiting
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left min-w-[720px]">
            <thead className="bg-gray-50 text-gray-600 text-sm uppercase tracking-wider">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Age</th>
                <th className="px-4 py-3">Sex</th>
                <th className="px-4 py-3">Urgency</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {triageQueue.map((patient) => (
                <tr key={patient.patientId} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{patient.name}</td>
                  <td className="px-4 py-3 text-gray-700">{patient.age}</td>
                  <td className="px-4 py-3 text-gray-700">{patient.sex}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-semibold uppercase ${
                        patient.urgency === "critical"
                          ? "bg-red-100 text-red-700 border border-red-200"
                          : patient.urgency === "emergency"
                            ? "bg-red-100 text-red-700 border border-red-200"
                            : patient.urgency === "urgent"
                              ? "bg-amber-100 text-amber-700 border border-amber-200"
                              : "bg-green-100 text-green-700 border border-green-200"
                      }`}
                    >
                      {patient.urgency || "normal"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                      patient.status === "triaged"
                        ? "bg-green-100 text-green-700"
                        : "bg-amber-100 text-amber-700"
                    }`}>
                      {patient.status.replace("_", " ")}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {patient.status === "awaiting_triage" ? (
                      <button
                        onClick={() => handleStartTriage(patient)}
                        className="px-3 py-1 rounded-md text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 transition"
                      >
                        Start Triage
                      </button>
                    ) : (
                      <span className="px-3 py-1 rounded-md text-sm font-semibold bg-gray-100 text-gray-600">
                        {patient.urgency ? patient.urgency.toUpperCase() : "TRIAGED"}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
              {triageQueue.length === 0 && (
                <tr>
                  <td className="px-4 py-3 text-gray-500" colSpan={6}>
                    No patients in triage queue.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mt-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-700">Triage Results</h2>
          <span className="text-sm text-gray-500">{triageRecords.length} records</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left min-w-[720px]">
            <thead className="bg-gray-50 text-gray-600 text-sm uppercase tracking-wider">
              <tr>
                <th className="px-4 py-3">Patient</th>
                <th className="px-4 py-3">Urgency</th>
                <th className="px-4 py-3">Triaged At</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {triageRecords.length > 0 ? (
                triageRecords.map((r) => (
                  <tr key={r.id || r.patientId} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-900 font-medium">{r.name || r.patientId}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold uppercase ${
                        r.urgencyLevel === "critical" || r.urgencyLevel === "emergency"
                          ? "bg-red-100 text-red-700 border border-red-200"
                          : r.urgencyLevel === "urgent"
                          ? "bg-amber-100 text-amber-700 border border-amber-200"
                          : "bg-green-100 text-green-700 border border-green-200"
                      }`}>
                        {r.urgencyLevel || "normal"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-700">{new Date(r.triagedAt).toLocaleString() || "—"}</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700">
                        Triaged
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td className="px-4 py-3 text-gray-500" colSpan={4}>
                    No triage results yet.
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
        <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">{title}</p>
        <h3 className="text-3xl font-bold text-gray-900 mt-2">{count}</h3>
      </div>
      <div className={`p-3 rounded-lg text-white shadow-lg ${color}`}>{icon}</div>
    </div>
  </div>
);

