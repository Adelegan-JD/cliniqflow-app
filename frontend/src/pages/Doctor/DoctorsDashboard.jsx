import React, { useEffect, useMemo, useState } from "react";
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
  const userProfile = useUserProfile();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [stats, setStats] = useState({
    totalPatientsToday: 0,
    awaitingTriage: 0,
    awaitingConsultation: 0,
    visitsEnded: 0,
  });

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
        const data = await api.get("/doctor/stats");
        if (!mounted) return;
        setStats(normalizeStats(data));
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
