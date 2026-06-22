import { useState, useEffect, useRef } from "react";
import MultiStepRegistration from "./MultistepForm/MultiStepForm";
import RecordOfficerDashboardComponent from "../../components/RecordOfficerDashboard";
import { useUserProfile } from "../../hooks/useUserProfile";
import { useAuth } from "../../contexts/AuthContext";
import { api } from "../../utils/api";

const emptyStats = {
  totalPatientsToday: 0,
  activeQueueCount: 0,
  visitsCreatedToday: 0,
  completedVisitsToday: 0,
};

const RecordOfficerDashboard = () => {
  const [view, setView] = useState("dashboard");
  const userProfile = useUserProfile();
  const { loading: authLoading, user: authUser } = useAuth();
  const loadedRef = useRef(false);

  const [stats, setStats] = useState(emptyStats);
  const [loading, setLoading] = useState(true);
  const [dashboardError, setDashboardError] = useState("");
  const [recentRegistrations, setRecentRegistrations] = useState([]);

  const loadDashboard = async (retry = true) => {
    try {
      const data = await api.get("/record-officer/dashboard");
      const nextStats = data?.stats || {};
      setStats({
        totalPatientsToday:
          nextStats.totalPatientsToday ?? nextStats.newRegistrationsToday ?? 0,
        activeQueueCount:
          nextStats.activeQueueCount ??
          nextStats.waitingForTriage ??
          (Array.isArray(data?.queue) ? data.queue.length : 0),
        visitsCreatedToday:
          nextStats.visitsCreatedToday ?? nextStats.visitsToday ?? 0,
        completedVisitsToday: nextStats.completedVisitsToday ?? 0,
      });
      setRecentRegistrations(
        Array.isArray(data?.recentRegistrations)
          ? data.recentRegistrations
          : [],
      );
      setDashboardError("");
    } catch (err) {
      if (err?.status === 401 && retry) {
        await new Promise((resolve) => setTimeout(resolve, 250));
        return loadDashboard(false);
      }
      setStats(emptyStats);
      setDashboardError(err?.message || "Unable to load dashboard data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (authLoading || !authUser || loadedRef.current) return;
    loadedRef.current = true;
    let cancelled = false;
    setLoading(true);
    (async () => {
      if (cancelled) return;
      await loadDashboard();
    })();
    return () => {
      cancelled = true;
    };
  }, [authLoading, authUser]);

  const handleNavigate = (target) => {
    if (target === "register-patient") setView("register-patient");
    else if (target === "patient-records") setView("records");
    else setView("dashboard");
  };

  return (
    <div>
      <div className={view === "dashboard" ? "block" : "hidden"}>
        <RecordOfficerDashboardComponent
          onNavigate={handleNavigate}
          user={userProfile}
          stats={stats}
          loading={loading}
          dashboardError={dashboardError}
          recentRegistrations={recentRegistrations}
          onLoadDashboard={loadDashboard}
        />
      </div>
      <div className={view === "register-patient" ? "block" : "hidden"}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">Register Patient</h2>
          <button
            onClick={() => setView("dashboard")}
            className="text-sm text-blue-600"
          >
            Back
          </button>
        </div>
        <MultiStepRegistration />
      </div>
    </div>
  );
};

export default RecordOfficerDashboard;
