import React, { useState, useEffect } from "react";
import {
  ClipboardList,
  UserPlus,
  Users,
  Clock,
  Calendar,
  Activity,
  User,
  Hash,
} from "lucide-react";
import { api } from "../utils/api";

const RecordOfficerDashboard = ({ onNavigate, user }) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [stats, setStats] = useState({ visitsToday: 0, waitingForTriage: 0, newRegistrationsToday: 0 });
  const [queue, setQueue] = useState([]);
  const [recentVisits, setRecentVisits] = useState([]);
  const [recentRegistrations, setRecentRegistrations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await api.get("/record-officer/dashboard");
        if (cancelled) return;
        setStats(data.stats || { visitsToday: 0, waitingForTriage: 0, newRegistrationsToday: 0 });
        setQueue(data.queue || []);
        setRecentVisits(data.recentVisits || []);
        setRecentRegistrations(data.recentRegistrations || []);
      } catch {
        if (!cancelled) {
          setStats({ visitsToday: 0, waitingForTriage: 0, newRegistrationsToday: 0 });
          setQueue([]);
          setRecentVisits([]);
          setRecentRegistrations([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    const timer = setInterval(() => setCurrentDate(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const statColorClasses = {
    visits: "bg-blue-50 border-blue-100 text-blue-700",
    triage: "bg-amber-50 border-amber-100 text-amber-700",
    registrations: "bg-green-50 border-green-100 text-green-700",
  };

  const queueColorClasses = {
    amber: "bg-amber-100 text-amber-800",
    blue: "bg-blue-100 text-blue-800",
    indigo: "bg-indigo-100 text-indigo-800",
    green: "bg-green-100 text-green-800",
  };

  return (
    <div className="space-y-8">
      {/* Header: Welcome + Date/Time */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-800">
            Welcome back, {user?.name?.split(" ")[0]}!
          </h2>
          <p className="text-gray-500 text-sm mt-0.5">Record Officer Dashboard</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-gray-500">
            <Calendar size={18} className="text-blue-500" />
            <span className="text-sm font-medium">
              {currentDate.toLocaleDateString("en-US", {
                weekday: "long",
                month: "long",
                day: "numeric",
                year: "numeric",
              })}
            </span>
          </div>
          <div className="flex items-center gap-2 text-gray-800">
            <Clock size={20} className="text-blue-600" />
            <span className="text-2xl font-bold tracking-tight">
              {currentDate.toLocaleTimeString("en-US", {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
              })}
            </span>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div
          className={`rounded-xl border p-5 ${statColorClasses.visits}`}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium opacity-90">Visits Today</p>
              <p className="text-2xl font-bold mt-1">{loading ? "—" : stats.visitsToday}</p>
            </div>
            <ClipboardList size={32} className="opacity-60" />
          </div>
        </div>
        <div
          className={`rounded-xl border p-5 ${statColorClasses.triage}`}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium opacity-90">Waiting for Triage</p>
              <p className="text-2xl font-bold mt-1">{loading ? "—" : stats.waitingForTriage}</p>
            </div>
            <Clock size={32} className="opacity-60" />
          </div>
        </div>
        <div
          className={`rounded-xl border p-5 ${statColorClasses.registrations}`}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium opacity-90">New Registrations Today</p>
              <p className="text-2xl font-bold mt-1">{loading ? "—" : stats.newRegistrationsToday}</p>
            </div>
            <UserPlus size={32} className="opacity-60" />
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Quick Actions</h3>
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => onNavigate("create-visit")}
            className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors shadow-sm"
          >
            <ClipboardList size={20} />
            Create Visit
          </button>
          <button
            type="button"
            onClick={() => onNavigate("register-patient")}
            className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors shadow-sm"
          >
            <UserPlus size={20} />
            Register Patient
          </button>
        </div>
      </div>

      {/* Queue Overview + Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Queue Status */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <h3 className="font-semibold text-gray-800 flex items-center gap-2">
              <Activity size={18} className="text-blue-600" />
              Queue Status
            </h3>
          </div>
          <div className="p-6 space-y-3">
            {queue.map((item) => (
              <div
                key={item.status}
                className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0"
              >
                <span className="text-gray-700">{item.status}</span>
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium ${queueColorClasses[item.color]}`}
                >
                  {item.count}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Visits */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
            <h3 className="font-semibold text-gray-800 flex items-center gap-2">
              <ClipboardList size={18} className="text-blue-600" />
              Recent Visits
            </h3>
            <button
              type="button"
              onClick={() => onNavigate("create-visit")}
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              View all
            </button>
          </div>
          <div className="divide-y divide-gray-100">
            {recentVisits.map((visit) => (
              <div
                key={visit.id}
                className="px-6 py-3 flex items-center justify-between hover:bg-gray-50"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center">
                    <Hash size={14} className="text-blue-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-800">{visit.patient}</p>
                    <p className="text-xs text-gray-500">{visit.id} · {visit.time}</p>
                  </div>
                </div>
                <span className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-600">
                  {visit.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Patient Registrations */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
          <h3 className="font-semibold text-gray-800 flex items-center gap-2">
            <User size={18} className="text-blue-600" />
            Recent Patient Registrations
          </h3>
          <button
            type="button"
            onClick={() => onNavigate("patient-records")}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            View all
          </button>
        </div>
        <div className="divide-y divide-gray-100">
            {recentRegistrations.map((reg, i) => (
            <div
              key={reg.pid || i}
              className="px-6 py-3 flex items-center justify-between hover:bg-gray-50"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                  <Users size={14} className="text-green-600" />
                </div>
                <div>
                  <p className="font-medium text-gray-800">{reg.name}</p>
                  <p className="text-xs text-gray-500">{reg.pid}</p>
                </div>
              </div>
              <span className="text-sm text-gray-500">{reg.time}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default RecordOfficerDashboard;
