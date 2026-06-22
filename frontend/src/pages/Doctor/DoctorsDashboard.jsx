import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Activity,
  CheckCircle2,
  Clock3,
  ClipboardCheck,
  UsersRound,
  ArrowRight,
  AlertCircle,
  Stethoscope,
  ClipboardList,
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

      try {
        const data = await api.get("/doctor/stats");
        if (!mounted) return;
        setStats(normalizeStats(data));
      } catch (err) {
        if (!mounted) return;
        setError("Doctor dashboard data is unavailable right now.");
        setStats({
          totalPatientsToday: 0,
          awaitingTriage: 0,
          awaitingConsultation: 0,
          visitsEnded: 0,
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
    <div className="transition-all duration-300 p-4 md:p-6 overflow-auto w-full bg-gray-50/50">
      <header className="mb-8">
        <WelcomeBanner user={userProfile} />
        <div className="flex items-center gap-3 mt-6">
          <div className="p-3 bg-blue-50 rounded-xl">
            <Activity className="text-blue-600" size={32} />
          </div>
          <div>
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900">
              Doctor Dashboard
            </h1>
            <p className="text-gray-600 mt-1">
              Welcome Dr. {userProfile?.name || "Doctor"}, here is your patient
              queue overview.
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
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          <QuickActionCard
            title="Patients Queue"
            description="See consultation-ready patients and start exams"
            icon={<Stethoscope size={24} />}
            color="bg-blue-500"
            href="/doctors-dashboard/patients_queue"
          />
          <QuickActionCard
            title="Nurse Triage Queue"
            description="Monitor the live nurse queue for awareness"
            icon={<ClipboardList size={24} />}
            color="bg-amber-500"
            href="/doctors-dashboard/nurse-queue"
          />
          {/* Triage Results removed from doctors dashboard per request */}
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
  <Link
    to={href}
    className="group card elevated p-6 hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1 cursor-pointer"
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
  </Link>
);

export default DoctorsDashboard;
