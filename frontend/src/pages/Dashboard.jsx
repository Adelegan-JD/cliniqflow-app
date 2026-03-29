import React, { useState, useEffect } from "react";
import {
  Users,
  UserPlus,
  Activity,
  ClipboardList,
  Stethoscope,
  User,
  LayoutDashboard,
  Settings,
  HelpCircle,
  FileText,
  UsersRound,
  Calendar,
  UserPlus2,
  Clock,
} from "lucide-react";
import WelcomeBanner from "../components/WelcomeBanner";
import { useAdminStore } from "../store/adminStore";
import { useUserProfile } from "../hooks/useUserProfile";
import { api } from "../utils/api";

const Dashboard = () => {
  const { users, fetchUsers, isLoading, adminError } = useAdminStore();
  const userProfile = useUserProfile();
  const [error, setError] = useState(null);
  const [clinicStats, setClinicStats] = useState({
    totalPatients: 0,
    visitsToday: 0,
    newRegistrationsThisMonth: 0,
    doctorQueue: 0,
  });
  const [statsLoading, setStatsLoading] = useState(true);

  // Calculate stats dynamically from the user list
  const stats = {
    doctors: users.filter((u) => u.role?.toLowerCase() === "doctor").length,
    nurses: users.filter((u) => u.role?.toLowerCase() === "nurse").length,
    officers: users.filter(
      (u) =>
        u.role?.toLowerCase() === "record officer" ||
        u.role?.toLowerCase() === "record_officer",
    ).length,
  };

  // --- API INTERACTION ---

  // 1. Fetch Users on Component Mount
  useEffect(() => {
    if (!users[0]) {
      fetchUsers();
    }
  }, []);

  // 2. Fetch clinic stats (patients, visits, registrations, doctor queue)
  useEffect(() => {
    let mounted = true;
    setStatsLoading(true);
    api
      .get("/admin/stats")
      .then((data) => {
        if (mounted && data) {
          setClinicStats({
            totalPatients: data.totalPatients ?? 0,
            visitsToday: data.visitsToday ?? 0,
            newRegistrationsThisMonth: data.newRegistrationsThisMonth ?? 0,
            doctorQueue: data.doctorQueue ?? 0,
          });
        }
      })
      .catch(() => {
        if (mounted) setClinicStats({ totalPatients: 0, visitsToday: 0, newRegistrationsThisMonth: 0, doctorQueue: 0 });
      })
      .finally(() => {
        if (mounted) setStatsLoading(false);
      });
    return () => { mounted = false; };
  }, []);

  const menuItems = [
    {
      id: "dashboard",
      label: "Dashboard",
      icon: <LayoutDashboard size={20} />,
    },
    { id: "doctors", label: "Users", icon: <Users size={20} /> },
    { id: "records", label: "Records", icon: <FileText size={20} /> },
    { id: "settings", label: "Settings", icon: <Settings size={20} /> },
    { id: "help", label: "Help & Support", icon: <HelpCircle size={20} /> },
  ];


  // 2. Add User Function
  // const handleAddUser = async (e) => {
  //   e.preventDefault();
  //   try {
  //     const response = await fetch("/add_users", {
  //       method: "POST",
  //       headers: { "Content-Type": "application/json" },
  //       body: JSON.stringify(formData),
  //     });

  //     if (response.ok) {
  //       // Refresh list to show new user and update counts
  //       fetchUsers();
  //       setFormData({ ...formData, name: "" }); // Reset name field only
  //       alert(`${formData.role} added successfully!`);
  //     } else {
  //       alert("Failed to add user.");
  //     }
  //   } catch (err) {
  //     console.error(err);
  //     alert("Error connecting to server.");
  //   }
  // };

  return (
    <div className="transition-all duration-300 p-4 overflow-auto w-full">
      {/* Header */}
      <header className="mb-8">
        <WelcomeBanner user={userProfile} />
        <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-2">
          <Activity className="text-blue-600" />
          Hospital Admin Dashboard
        </h1>
        <p className="text-gray-500 mt-1">
          Overview of hospital staff and personnel management.
        </p>
        {adminError && (
          <div className="mt-4 p-4 bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700">
            {adminError}
          </div>
        )}
      </header>

      {/* Clinic Metrics */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-700 mb-4">Clinic Metrics</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <StatCard
            title="Total Patients"
            count={statsLoading ? "—" : clinicStats.totalPatients}
            icon={<UsersRound size={28} />}
            color="bg-indigo-500"
          />
          <StatCard
            title="Visits Today"
            count={statsLoading ? "—" : clinicStats.visitsToday}
            icon={<Calendar size={28} />}
            color="bg-teal-500"
          />
          <StatCard
            title="New This Month"
            count={statsLoading ? "—" : clinicStats.newRegistrationsThisMonth}
            icon={<UserPlus2 size={28} />}
            color="bg-violet-500"
          />
          <StatCard
            title="Doctor Queue"
            count={statsLoading ? "—" : clinicStats.doctorQueue}
            icon={<Clock size={28} />}
            color="bg-rose-500"
          />
        </div>
      </div>

      {/* Staff Metrics */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-700 mb-4">Staff</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <StatCard
            title="Doctors"
            count={stats.doctors}
            icon={<Stethoscope size={32} />}
            color="bg-blue-500"
          />
          <StatCard
            title="Nurses"
            count={stats.nurses}
            icon={<UserPlus size={32} />}
            color="bg-emerald-500"
          />
          <StatCard
            title="Record Officers"
            count={stats.officers}
            icon={<ClipboardList size={32} />}
            color="bg-amber-500"
          />
        </div>
      </div>

      {/* User list table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold mb-4">Staff Directory</h2>
        {isLoading ? (
          <p className="text-gray-500">Loading users...</p>
        ) : adminError ? (
          <p className="text-gray-500">Unable to load staff data.</p>
        ) : users.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-gray-50 text-gray-600 text-sm uppercase">
                <tr>
                  <th className="px-6 py-3">Name</th>
                  <th className="px-6 py-3">Role</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {users.map((u, index) => (
                  <tr key={u.id || index} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      {u.display_name || u.name || u.email || "Not Available"}
                    </td>
                    <td className="px-6 py-4">
                      {u.role === "record_officer"
                        ? "Record Officer"
                        : String(u.role)[0].toUpperCase() +
                          String(u.role).slice(1, u.length)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500">No users available.</p>
        )}
      </div>
    </div>
  );
};

// --- Sub-Components for Cleanliness ---

const StatCard = ({ title, count, icon, color }) => (
  <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 relative overflow-hidden group">
    <div
      className={`absolute right-0 top-0 w-24 h-24 transform translate-x-8 -translate-y-8 rounded-full opacity-10 ${color}`}
    ></div>
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

const RoleBadge = ({ role }) => {
  const styles = {
    Doctor: "bg-blue-100 text-blue-800 border-blue-200",
    Nurse: "bg-emerald-100 text-emerald-800 border-emerald-200",
    "Record Officer": "bg-amber-100 text-amber-800 border-amber-200",
  };

  // Default fallback style
  const activeStyle =
    styles[role] || "bg-gray-100 text-gray-800 border-gray-200";

  return (
    <span
      className={`px-3 py-1 rounded-full text-xs font-semibold border ${activeStyle}`}
    >
      {role}
    </span>
  );
};

export default Dashboard;
