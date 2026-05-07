import { Outlet, useLocation } from "react-router-dom";
import Sidebar from "../Sidebar";
import { HelpCircle, LayoutDashboard, Search } from "lucide-react";
import { useState, useEffect } from "react";
import { useUserProfile } from "../../hooks/useUserProfile";

export default function RecordOfficerLayout() {
  const userProfile = useUserProfile();
  const menuItems = [
    {
      id: "record-officer",
      label: "Dashboard",
      icon: <LayoutDashboard size={20} />,
      url: "/record-officer",
    },
    {
      id: "records",
      label: "Records",
      icon: <Search size={20} />,
      url: "/record-officer/records",
    },
    {
      id: "help",
      label: "Help & Support",
      icon: <HelpCircle size={20} />,
      url: "/record-officer/help",
    },
  ];

  const [activePage, setActivePage] = useState("record-officer");
  const location = useLocation();

  useEffect(() => {
    const path = location.pathname;
    if (path === "/record-officer" || path === "/record-officer/")
      setActivePage("record-officer");
    else if (path.startsWith("/record-officer/users")) setActivePage("users");
    else if (path.startsWith("/record-officer/records"))
      setActivePage("records");
    else if (path.startsWith("/record-officer/settings"))
      setActivePage("settings");
    else if (path.startsWith("/record-officer/help")) setActivePage("help");
  }, [location.pathname]);

  return (
    <div className="h-screen flex bg-gray-50 overflow-hidden">
      <Sidebar
        logo="Record Officer Dashboard"
        menuItems={menuItems}
        activeItem={activePage}
        onNavigate={setActivePage}
        userProfile={userProfile}
      />
      {/* <Outlet /> */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-8">
          {/* <div className="w-1/3 relative">
            <input
              type="text"
              placeholder="Search existing patients (Name, PID, NIN)..."
              className="w-full pl-10 pr-4 py-2 bg-gray-100 border-transparent rounded-full text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none transition-all"
            />
            <span className="absolute left-3 top-2.5 text-gray-400">
              <Search size={16} />
            </span>
          </div> */}

          <div className="flex items-center gap-4 ml-auto">
            <div className="text-right">
              <p className="text-sm font-bold text-gray-800"></p>
              <p className="text-xs text-gray-500">{userProfile.role}</p>
            </div>
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-700 font-bold"></div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-8">
          <div className="max-w-5xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
