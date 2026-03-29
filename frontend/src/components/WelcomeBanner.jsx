import React, { useState, useEffect } from "react";
import { Clock, Calendar } from "lucide-react";

const WelcomeBanner = ({ user }) => {
  const [currentDate, setCurrentDate] = useState(new Date());

  // Update the time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentDate(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Format options for the date
  const dateOptions = {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  };
  const timeOptions = { hour: "2-digit", minute: "2-digit" };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8 flex flex-col md:flex-row justify-between items-center gap-4">
      {/* Left Side: User Info */}
      <div className="flex items-center gap-4 w-full md:w-auto">
        <div className="relative">
          <img
            src={user?.avatar || "https://via.placeholder.com/150"}
            alt={user?.name}
            className="w-16 h-16 rounded-full object-cover border-4 border-blue-50"
          />
          <span className="absolute bottom-0 right-0 w-4 h-4 bg-green-500 border-2 border-white rounded-full"></span>
        </div>
        <div>
          <h2 className="text-2xl font-bold text-gray-800">
            Welcome back, {user?.name?.split(" ")[0] || "User"}! 👋
          </h2>
          <p className="text-gray-500 text-sm font-medium bg-gray-100 px-2 py-0.5 rounded inline-block mt-1">
            {user?.role}
          </p>
        </div>
      </div>

      {/* Right Side: Date & Time */}
      <div className="flex flex-col items-end gap-1 w-full md:w-auto text-right">
        {/* Date Display */}
        <div className="flex items-center gap-2 text-gray-500">
          <Calendar size={16} className="text-blue-500" />
          <span className="text-sm font-medium">
            {currentDate.toLocaleDateString("en-US", dateOptions)}
          </span>
        </div>

        {/* Time Display */}
        <div className="flex items-center gap-2 text-gray-800">
          <Clock size={20} className="text-blue-600" />
          <span className="text-3xl font-bold tracking-tight">
            {currentDate.toLocaleTimeString("en-US", timeOptions)}
          </span>
        </div>
      </div>
    </div>
  );
};

export default WelcomeBanner;
