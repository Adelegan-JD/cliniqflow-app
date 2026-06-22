import React, { useEffect, useMemo, useState } from "react";
import {
  Calendar,
  ClipboardList,
  Clock,
  PlusCircle,
  Search,
  ShieldCheck,
  Users,
  UserPlus,
} from "lucide-react";
import { toast } from "react-toastify";
import { api } from "../utils/api";
import { useAuth } from "../contexts/AuthContext";

const emptyStats = {
  totalPatientsToday: 0,
  activeQueueCount: 0,
  visitsCreatedToday: 0,
  completedVisitsToday: 0,
};

const RecordOfficerDashboard = ({
  onNavigate,
  user,
  stats = emptyStats,
  loading = true,
  dashboardError = "",
  recentRegistrations = [],
  onLoadDashboard,
}) => {
  const { user: authUser } = useAuth();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [pidSearchValue, setPidSearchValue] = useState("");
  const [pidSearching, setPidSearching] = useState(false);
  const [pidPatient, setPidPatient] = useState(null);
  const [pidCreating, setPidCreating] = useState(false);
  const [pidError, setPidError] = useState("");

  const displayName =
    user?.name || authUser?.user_metadata?.name || authUser?.email || "User";
  const firstName = useMemo(() => displayName.split(" ")[0], [displayName]);

  useEffect(() => {
    const timer = setInterval(() => setCurrentDate(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const statCards = [
    {
      label: "Total patients today",
      value: stats.totalPatientsToday,
      icon: UserPlus,
      accent: "text-emerald-600",
      iconBg: "bg-emerald-50",
      tone: "bg-emerald-50 border-emerald-100",
    },
    {
      label: "Active queue count",
      value: stats.activeQueueCount,
      icon: ClipboardList,
      accent: "text-blue-600",
      iconBg: "bg-blue-50",
      tone: "bg-blue-50 border-blue-100",
    },
    {
      label: "Visits created today",
      value: stats.visitsCreatedToday,
      icon: Search,
      accent: "text-violet-600",
      iconBg: "bg-violet-50",
      tone: "bg-violet-50 border-violet-100",
    },
    {
      label: "Completed visits",
      value: stats.completedVisitsToday,
      icon: ShieldCheck,
      accent: "text-amber-600",
      iconBg: "bg-amber-50",
      tone: "bg-amber-50 border-amber-100",
    },
  ];

  const handleLookupPid = async () => {
    if (!pidSearchValue.trim()) return;
    setPidSearching(true);
    setPidError("");
    try {
      const params = new URLSearchParams({
        q: pidSearchValue.trim(),
        search_by: "pid",
      });
      const results = await api.get(
        `/record-officer/patients/search?${params}`,
      );
      setPidPatient(
        Array.isArray(results) && results.length ? results[0] : null,
      );
    } catch (err) {
      setPidPatient(null);
      setPidError(err?.message || "PID lookup failed.");
      toast.error(err?.message || "PID lookup failed.", {
        position: "top-right",
        autoClose: 4000,
      });
    } finally {
      setPidSearching(false);
    }
  };

  const handleCreateVisit = async () => {
    if (!pidPatient) return;
    setPidCreating(true);
    try {
      await api.post("/record-officer/visits", {
        patient_id: pidPatient.id,
        reason_for_visit: null,
        department: null,
      });
      setPidPatient(null);
      setPidSearchValue("");
      setPidError("");
      if (typeof onLoadDashboard === "function") {
        await onLoadDashboard();
      }
      toast.success("Patient's visit created successfully!", {
        position: "top-right",
        autoClose: 4000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
      });
    } catch (err) {
      const errorMessage = err?.message || "Failed to create visit.";
      setPidError(errorMessage);

      // Show appropriate toast based on error type
      if (err?.status === 409) {
        toast.warning(errorMessage, {
          position: "top-right",
          autoClose: 5000,
        });
      } else {
        toast.error(errorMessage, {
          position: "top-right",
          autoClose: 4000,
        });
      }
    } finally {
      setPidCreating(false);
    }
  };

  if (loading && !dashboardError) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="bg-white rounded-2xl border border-gray-200 p-6 h-28" />
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="bg-white rounded-2xl border border-gray-200 p-5 h-28"
            />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="bg-white rounded-2xl border border-gray-200 p-6 h-48" />
          <div className="bg-white rounded-2xl border border-gray-200 p-6 h-48" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 lg:space-y-8">
      <section className="rounded-3xl border border-blue-100 bg-linear-to-r from-blue-50 via-indigo-50 to-blue-100 p-6 text-blue-900 shadow-md shadow-blue-200/30">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.25em] text-blue-700/80">
              Record Officer Dashboard
            </p>
            <h2 className="mt-2 text-2xl md:text-3xl font-semibold text-blue-900">
              Welcome back, {firstName}
            </h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-blue-800/85">
              Focus on new registrations and returning patients. Create visits
              fast, keep the queue clean, and avoid duplicate records.
            </p>
          </div>
          <div className="rounded-2xl border border-blue-200 bg-white/60 px-4 py-3 backdrop-blur-sm shadow-lg shadow-blue-100/20">
            <div className="flex items-center gap-2 text-sm text-blue-800">
              <Calendar size={16} />
              <span>
                {currentDate.toLocaleDateString("en-US", {
                  weekday: "long",
                  month: "long",
                  day: "numeric",
                  year: "numeric",
                })}
              </span>
            </div>
            <div className="mt-2 flex items-center gap-2 text-2xl font-semibold text-blue-900">
              <Clock size={20} />
              <span>
                {currentDate.toLocaleTimeString("en-US", {
                  hour: "2-digit",
                  minute: "2-digit",
                  second: "2-digit",
                })}
              </span>
            </div>
          </div>
        </div>
      </section>

      {dashboardError && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          {dashboardError}
        </div>
      )}

      <section className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <div
              key={card.label}
              className={`rounded-2xl border ${card.tone} bg-white p-5 shadow-sm`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-medium text-gray-500">
                    {card.label}
                  </p>
                  <p className="mt-2 text-3xl font-semibold text-gray-900">
                    {loading ? "—" : card.value}
                  </p>
                </div>
                <div className={`rounded-xl p-3 ${card.iconBg}`}>
                  <Icon size={20} className={card.accent} />
                </div>
              </div>
            </div>
          );
        })}
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-6">
        <div className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl bg-emerald-50 p-3 text-emerald-600">
              <UserPlus size={22} />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Patient Registration
              </h3>
              <p className="text-sm text-gray-500">
                Register a brand-new patient with fresh demographics and
                hospital identity.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => onNavigate?.("register-patient")}
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-3 font-medium text-white transition-colors hover:bg-emerald-700"
          >
            <UserPlus size={18} />
            Register Patient
          </button>
        </div>

        <div className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl bg-blue-50 p-3 text-blue-600">
              <ClipboardList size={22} />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Create New Visit
              </h3>
              <p className="text-sm text-gray-500">
                Search a returning patient by PID and generate a new visit that
                goes straight into the queue.
              </p>
            </div>
          </div>

          <div className="mt-5 flex flex-col gap-3 sm:flex-row">
            <input
              type="text"
              value={pidSearchValue}
              onChange={(e) => setPidSearchValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleLookupPid();
                }
              }}
              placeholder="Enter Patient ID (PID)"
              className="w-full flex-1 rounded-xl border border-gray-300 px-4 py-3 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
            />
            <button
              type="button"
              onClick={handleLookupPid}
              disabled={pidSearching || !pidSearchValue.trim()}
              className="rounded-xl bg-blue-600 px-5 py-3 font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {pidSearching ? "Searching..." : "Lookup PID"}
            </button>
          </div>

          {pidPatient && (
            <div className="mt-4 rounded-2xl border border-blue-100 bg-blue-50 p-4">
              <p className="text-sm font-medium text-blue-900">
                Found returning patient
              </p>
              <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-blue-800">
                <span>{pidPatient.name}</span>
                <span>{pidPatient.pid || pidPatient.id}</span>
              </div>
              <button
                type="button"
                onClick={handleCreateVisit}
                disabled={pidCreating}
                className="mt-4 inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-3 font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <PlusCircle size={18} />
                {pidCreating ? "Creating Visit..." : "Create Visit"}
              </button>
            </div>
          )}
        </div>
      </section>

      <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl bg-emerald-50 p-3 text-emerald-600">
              <Users size={22} />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Recently Registered Patients
              </h3>
              <p className="text-sm text-gray-500">
                Latest registrations pulled from the dashboard feed.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => onNavigate?.("patient-records")}
            className="text-sm font-medium text-blue-600 hover:text-blue-700"
          >
            View all
          </button>
        </div>

        <div className="mt-5 divide-y divide-gray-100 overflow-hidden rounded-2xl border border-gray-100">
          {recentRegistrations.length ? (
            recentRegistrations.map((reg, index) => (
              <div
                key={reg.pid || reg.id || index}
                className="flex items-center justify-between gap-4 px-4 py-3 hover:bg-gray-50"
              >
                <div className="min-w-0">
                  <p className="truncate font-medium text-gray-900">
                    {reg.name || "Unnamed patient"}
                  </p>
                  <p className="text-sm text-gray-500">{reg.pid || reg.id}</p>
                </div>
                <div className="text-right text-sm text-gray-500">
                  <p>{reg.time || "—"}</p>
                  {reg.created_at && (
                    <p className="text-xs text-gray-400">
                      {new Date(reg.created_at).toLocaleDateString()}
                    </p>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="px-4 py-8 text-center text-sm text-gray-500">
              No recent registrations yet.
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default RecordOfficerDashboard;
