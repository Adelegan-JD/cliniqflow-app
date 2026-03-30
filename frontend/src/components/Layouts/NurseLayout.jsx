import { Outlet } from "react-router-dom";
import Sidebar from "../Sidebar";
import { HelpCircle, LayoutDashboard } from "lucide-react";
import { useState, useEffect } from "react";
import { useUserProfile } from "../../hooks/useUserProfile";

export default function NurseLayout() {
  const userProfile = useUserProfile();
  const menuItems = [
    {
      id: "nurse-dashboard",
      label: "Dashboard",
      icon: <LayoutDashboard size={20} />,
      url: "/nurse-dashboard",
    },
    {
      id: "help",
      label: "Help & Support",
      icon: <HelpCircle size={20} />,
      url: "/nurse-dashboard/help",
    },
  ];

  const [activePage, setActivePage] = useState("nurse-dashboard");

  useEffect(() => {
    const path = location.pathname;
    if (path === "/nurse-dashboard" || path === "/nurse-dashboard/")
      setActivePage("nurse-dashboard");
    else if (path.startsWith("/nurse-dashboard/users")) setActivePage("users");
    else if (path.startsWith("/nurse-dashboard/records"))
      setActivePage("records");
    else if (path.startsWith("/nurse-dashboard/settings"))
      setActivePage("settings");
    else if (path.startsWith("/nurse-dashboard/help")) setActivePage("help");
  }, [location.pathname]);

  return (
    <div className="h-screen flex bg-gray-50 overflow-hidden">
      <Sidebar
        logo="Nurse Dashboard"
        menuItems={menuItems}
        activeItem={activePage}
        onNavigate={setActivePage}
        userProfile={userProfile}
      />
      <Outlet />
    </div>
  );
}
