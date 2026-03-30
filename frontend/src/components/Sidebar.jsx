import React, { useState } from "react";
import { Menu, X, ChevronLeft, ChevronRight, LogOut } from "lucide-react";
import { useAuthStore } from "../store/authStore";
import { Link, NavLink } from "react-router";
import { useAdminStore } from "../store/adminStore";

const Sidebar = ({
  logo,
  menuItems = [],
  activeItem,
  onNavigate,
  userProfile,
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const { logout } = useAuthStore();
  const { reset } = useAdminStore()

  // Toggle sidebar width (Desktop)
  const toggleSidebar = () => setIsExpanded(!isExpanded);

  // Toggle sidebar visibility (Mobile)
  const toggleMobileMenu = () => setIsMobileOpen(!isMobileOpen);

  return (
    <>
      {/* --- MOBILE TRIGGER BUTTON --- */}
      <button
        onClick={toggleMobileMenu}
        className="sm:hidden fixed top-4 right-4 z-50 p-2 rounded-md bg-white shadow-md text-gray-700"
      >
        {isMobileOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* --- SIDEBAR CONTAINER --- */}
      <aside
        className={`
          z-40 h-screen bg-white border-r border-gray-200 transition-all duration-300 ease-in-out max-[480px]:fixed max-[480px]:top-0 max-[480px]:left-0 
          ${isExpanded ? "w-64" : "w-20"} 
          ${isMobileOpen ? "translate-x-0" : "-translate-x-full sm:translate-x-0"}
        `}
      >
        <div className="h-full flex flex-col justify-between">
          {/* 1. HEADER / LOGO */}
          <div className="h-16 flex items-center justify-center border-b border-gray-100">
            {isExpanded ? (
              <span className="text-xl font-bold text-blue-600 truncate px-4">
                {logo || "Cliniq Flow"}
              </span>
            ) : (
              <span className="text-xl font-bold text-blue-600">CF</span>
            )}
          </div>

          {/* 2. NAVIGATION LINKS */}
          <nav className="flex-1 overflow-y-auto overflow-x-hidden py-4">
            <ul className="space-y-1 px-3">
              {menuItems.map((item, index) => {
                return (
                  <li key={item.id || index}>
                    <NavLink
                      to={item?.url || "#"}
                      end
                      title={item.label}
                      onClick={() => {
                        onNavigate(item.id);
                        setIsMobileOpen(false); // Close mobile menu on click
                      }}
                      className={({ isActive }) => {
                        const active = activeItem != null ? activeItem === item.id : isActive;
                        return `relative flex items-center w-full p-3 rounded-lg transition-colors group ${active ? "bg-blue-50 text-blue-600" : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"}`;
                      }}
                    >
                      <span className="flex items-center justify-center">
                        {item.icon}
                      </span>

                      <span
                        className={`
                          ml-3 font-medium transition-all duration-200 overflow-hidden whitespace-nowrap
                          ${isExpanded ? "w-auto opacity-100" : "w-0 opacity-0 sm:hidden"}
                        `}
                      >
                        {item.label}
                      </span>

                      {/* Tooltip for collapsed mode */}
                      {!isExpanded && (
                        <div className="absolute left-full rounded-md px-2 py-1 ml-6 bg-gray-900 text-white text-xs opacity-0 -translate-x-3 transition-all group-hover:visible group-hover:opacity-100 group-hover:translate-x-0 whitespace-nowrap z-50 invisible sm:block">
                          {item.label}
                        </div>
                      )}
                    </NavLink>
                  </li>
                );
              })}
            </ul>
          </nav>

          {/* 3. FOOTER / USER PROFILE */}
          <div className="mt-auto border-t border-gray-100 p-3 bg-gray-50/50">
            <div
              className={`
      group flex items-center p-2 rounded-xl transition-all duration-300
      ${isExpanded ? "hover:bg-white hover:shadow-sm" : "justify-center"}
    `}
            >
              {/* Avatar Section */}
              <div className="relative shrink-0">
                <img
                  src={
                    userProfile?.avatar ||
                    "https://ui-avatars.com/api/?name=User&background=random"
                  }
                  alt="Avatar"
                  className="w-10 h-10 rounded-xl object-cover ring-2 ring-white shadow-sm"
                />
                {/* Online Status Indicator */}
                <span className="absolute bottom-0 right-0 block h-2.5 w-2.5 rounded-full bg-green-500 ring-2 ring-white"></span>
              </div>

              {/* Text Info - Smooth Expansion */}
              <div
                className={`
        flex flex-col ml-3 transition-all duration-300 ease-in-out
        ${isExpanded ? "w-40 opacity-100" : "w-0 opacity-0 overflow-hidden"}
      `}
              >
                <span className="text-sm font-bold text-gray-900 truncate leading-tight">
                  {userProfile?.name || "User"}
                </span>
                <span className="text-[11px] font-medium text-blue-600 uppercase tracking-wider leading-tight">
                  {userProfile?.role || "Administrator"}
                </span>
              </div>

              {/* Logout Action */}
              <button
                onClick={() => {
                  logout();
                  reset();
                }}
                className={`
        transition-all duration-200 rounded-lg flex items-center justify-center
        ${
          isExpanded
            ? "p-2 text-gray-400 hover:text-red-600 hover:bg-red-50"
            : "absolute left-full ml-4 opacity-0 group-hover:opacity-100 bg-white shadow-lg p-3 text-red-600 border border-gray-100"
        }
      `}
                title="Logout"
              >
                <LogOut size={isExpanded ? 18 : 20} strokeWidth={2.5} />
              </button>
            </div>
          </div>

          {/* 4. COLLAPSE TOGGLE (Desktop Only) */}
          <button
            onClick={toggleSidebar}
            className="hidden sm:flex absolute -right-3 top-20 bg-white border border-gray-200 rounded-full p-1 shadow-sm hover:bg-gray-50 text-gray-500"
          >
            {isExpanded ? (
              <ChevronLeft size={14} />
            ) : (
              <ChevronRight size={14} />
            )}
          </button>
        </div>
      </aside>

      {/* OVERLAY for Mobile */}
      {isMobileOpen && (
        <div
          className="sm:hidden fixed inset-0 z-30 bg-black/20 backdrop-blur-sm"
          onClick={() => setIsMobileOpen(false)}
        />
      )}
    </>
  );
};

export default Sidebar;
