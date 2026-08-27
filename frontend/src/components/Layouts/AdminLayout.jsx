import { useState, useEffect } from "react";
import { Outlet, useLocation } from "react-router-dom";
import {
  Users,
  LayoutDashboard,
  Building2,
  HelpCircle,
  FileText,
  BadgeDollarSign,
  ClipboardPenLine,
} from "lucide-react";
import { useAdminStore } from "../../store/adminStore";
import { useUserProfile } from "../../hooks/useUserProfile";
import Sidebar from "../Sidebar";

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
    {
      id: "users",
      label: "Users",
      icon: <Users size={20} />,
      url: "/dashboard/users",
      disabled: !!adminError,
      disabledReason: "User service temporarily unavailable",
    },
    {
      id: "records",
      label: "Records",
      icon: <FileText size={20} />,
      url: "/dashboard/records",
    },
    {
      id: "settings",
      label: "Hospital Setup",
      icon: <Building2 size={20} />,
      url: "/dashboard/settings",
    },
    {
      id: "payments",
      label: "Payment Confirmation",
      icon: <BadgeDollarSign size={20} />,
      url: "/dashboard/payments",
    },
    {
      id: "clinical-templates",
      label: "Clinical Templates",
      icon: <ClipboardPenLine size={20} />,
      url: "/dashboard/clinical-templates",
    },
    {
      id: "help",
      label: "Help & Support",
      icon: <HelpCircle size={20} />,
      url: "/dashboard/help",
    },
  ];

  const location = useLocation();
  const [activePage, setActivePage] = useState("dashboard");

  useEffect(() => {
    const path = location.pathname;
    if (path === "/dashboard" || path === "/dashboard/")
      setActivePage("dashboard");
    else if (path.startsWith("/dashboard/users")) setActivePage("users");
    else if (path.startsWith("/dashboard/records")) setActivePage("records");
    else if (path.startsWith("/dashboard/settings")) setActivePage("settings");
    else if (path.startsWith("/dashboard/payments")) setActivePage("payments");
    else if (path.startsWith("/dashboard/clinical-templates")) setActivePage("clinical-templates");
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
        warningMessage={adminError}
      />
      <Outlet />
    </div>
  );
}
