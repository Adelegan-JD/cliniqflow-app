import { useState, useEffect } from "react";
import { Outlet, useLocation } from "react-router-dom";
import {
  Users,
  LayoutDashboard,
  Settings,
  HelpCircle,
  FileText,
} from "lucide-react";
import { useAdminStore } from "../store/adminStore";
import { useUserProfile } from "../hooks/useUserProfile";
import Sidebar from "../components/Sidebar";

export default function Layout() {
  const { adminError } = useAdminStore();
  const userProfile = useUserProfile();

  const menuItems = [
    {
      id: "dashboard",
      label: "Dashboard",
      icon: <LayoutDashboard size={20} />,
      url: "/dashboard",
    },
    // hide user management link if admin service is offline
    ...(!adminError
      ? [{ id: "users", label: "Users", icon: <Users size={20} />, url: "/dashboard/users" }]
      : []),
    { id: "records", label: "Records", icon: <FileText size={20} />, url: "/dashboard/records" },
    { id: "settings", label: "Settings", icon: <Settings size={20} />, url: "/dashboard/settings" },
    { id: "help", label: "Help & Support", icon: <HelpCircle size={20} />, url: "/dashboard/help" },
  ];

  const location = useLocation();
  const [activePage, setActivePage] = useState("dashboard");

  useEffect(() => {
    const path = location.pathname;
    if (path === "/dashboard" || path === "/dashboard/") setActivePage("dashboard");
    else if (path.startsWith("/dashboard/users")) setActivePage("users");
    else if (path.startsWith("/dashboard/records")) setActivePage("records");
    else if (path.startsWith("/dashboard/settings")) setActivePage("settings");
    else if (path.startsWith("/dashboard/help")) setActivePage("help");
  }, [location.pathname]);

  return (
    <div className="h-screen flex bg-gray-50 overflow-hidden">
      <Sidebar
        logo="CLINIQ FLOW"
        menuItems={menuItems}
        activeItem={activePage}
        onNavigate={setActivePage}
        userProfile={userProfile}
      />
      <Outlet />
    </div>
  );
}
