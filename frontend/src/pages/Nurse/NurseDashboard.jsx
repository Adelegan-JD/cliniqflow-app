import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  Activity,
  CheckCircle2,
  Clock3,
  ClipboardCheck,
  UsersRound,
  ArrowRight,
  AlertCircle,
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
      data.totalPatientsToday ??
      data.totalPatients ??
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
      0,
    visitsEnded:
      data.visitsEnded ?? data.completedVisits ?? data.endedVisits ?? 0,
  });

  useEffect(() => {
    let mounted = true;

    const loadNurseStats = async () => {
      setLoading(true);
      setError("");

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

          const awaitingTriage = queueData.filter(
            (p) => p.status === "awaiting_triage",
          ).length;
          const triagedCount = queueData.filter(
            (p) => p.status === "triaged",
          ).length;
          const visitsEnded = recordsData.filter(
            (r) => r.urgencyLevel === "normal",
          ).length;

          if (!mounted) return;
          setStats({
            totalPatientsToday: awaitingTriage + triagedCount + visitsEnded,
            awaitingTriage,
            awaitingConsultation: triagedCount,
            visitsEnded,
          });
          if (!mounted) return;
          setTriageQueue(Array.isArray(queueData) ? queueData : []);
          if (!mounted) return;
          setTriageRecords(Array.isArray(recordsData) ? recordsData : []);
        } else {
          const data = await api.get("/nurse/stats");
          if (!mounted) return;
          setStats(normalizeStats(data));
          const [queueData, recordsData] = await Promise.all([
            api.get("/nurse/triage-queue"),
            api.get("/nurse/triage-records"),
          ]);
          if (!mounted) return;
          setTriageQueue(Array.isArray(queueData) ? queueData : []);
          if (!mounted) return;
          setTriageRecords(Array.isArray(recordsData) ? recordsData : []);
        }
      } catch (error) {
        if (!mounted) return;
        console.error("Nurse stats fetch failed", error);
        if (!mounted) return;
        setError("Nurse dashboard data is unavailable right now.");
        setStats({
          totalPatientsToday: 0,
          awaitingTriage: 0,
          awaitingConsultation: 0,
          visitsEnded: 0,
        });
        setTriageQueue([]);
        setTriageRecords([]);
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
          setTriageQueue(Array.isArray(queueData) ? queueData : []);
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
    <div className="transition-all duration-300 p-4 md:p-6 overflow-auto w-full">
      <header className="mb-8">
        <WelcomeBanner user={userProfile} />
        <div className="flex items-center gap-3 mt-6">
          <div className="p-3 bg-blue-50 rounded-xl">
            <Activity className="text-blue-600" size={32} />
          </div>
          <div>
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900">
              Nurse Dashboard
            </h1>
            <p className="text-gray-600 mt-1">
              Welcome {userProfile?.name || "Nurse"}, here's your triage
              overview.
            </p>
          </div>
        </div>
      </header>

      {error ? (
        <div className="alert alert-warning mb-6">
          <AlertCircle size={20} className="shrink-0" />
          <div>
            <p className="font-semibold">Warning</p>
            <p className="text-sm">{error}</p>
          </div>
        </div>
      ) : null}

      <section className="mb-8">
        <h2 className="section-title">Today's Overview</h2>
        <div className="grid-responsive">
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

      <section className="mb-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <QuickActionCard
            title="Start Triage"
            description="Begin triaging waiting patients"
            icon={<ClipboardCheck size={24} />}
            color="bg-blue-500"
            href="/nurse-dashboard/triage-queue"
          />
          <QuickActionCard
            title="View Records"
            description="Check triaged patient records"
            icon={<CheckCircle2 size={24} />}
            color="bg-emerald-500"
            href="/nurse-dashboard/records"
          />
        </div>
      </section>
    </div>
  );
};

const StatCard = ({ title, count, icon, color }) => (
  <div className="stat-card">
    <div className="flex items-center gap-3">
      <div
        className="stat-card-icon"
        style={{ background: color + "20", color }}
      >
        {icon}
      </div>
      <div className="flex-1">
        <p className="stat-card-label">{title}</p>
        <p className="stat-card-value">{count}</p>
      </div>
    </div>
  </div>
);

const QuickActionCard = ({ title, description, icon, color, href }) => (
  <a
    href={href}
    className="group card elevated p-6 hover:shadow-lg transition-all duration-300 transform hover:scale-105 cursor-pointer"
  >
    <div className="flex items-start justify-between">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
          {title}
        </h3>
        <p className="text-gray-600 text-sm mt-1">{description}</p>
      </div>
      <div
        className={`p-3 rounded-lg text-white ${color} group-hover:shadow-lg transition-all`}
      >
        {icon}
      </div>
    </div>
    <div className="mt-4 flex items-center gap-2 text-blue-600 opacity-0 group-hover:opacity-100 transition-opacity">
      <span className="text-sm font-semibold">Go to page</span>
      <ArrowRight
        size={16}
        className="group-hover:translate-x-1 transition-transform"
      />
    </div>
  </a>
);
