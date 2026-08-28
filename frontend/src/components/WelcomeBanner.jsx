import React, { useState, useEffect } from "react";
import { Clock3, CalendarDays, ShieldCheck } from "lucide-react";

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
    <section className="mb-7 flex flex-col justify-between gap-5 rounded-lg border border-slate-200 bg-white px-6 py-5 shadow-sm md:flex-row md:items-center">
      <div className="flex items-center gap-4">
        <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-blue-950 text-white">
          <ShieldCheck size={22} aria-hidden="true" />
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Clinical operations</p>
          <h2 className="mt-1 text-xl font-semibold text-slate-900">{user?.name || "Staff workspace"}</h2>
          <p className="mt-1 text-sm text-slate-500">{user?.role || "Authenticated staff member"}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-x-6 gap-y-1 border-t border-slate-100 pt-4 text-right md:border-l md:border-t-0 md:pl-6 md:pt-0">
        <div className="flex items-center justify-end gap-2 text-slate-500">
          <CalendarDays size={15} aria-hidden="true" />
          <span className="text-sm font-medium">
            {currentDate.toLocaleDateString("en-US", dateOptions)}
          </span>
        </div>
        <div className="flex items-center justify-end gap-2 text-slate-900">
          <Clock3 size={16} className="text-blue-800" aria-hidden="true" />
          <span className="text-base font-semibold tabular-nums">
            {currentDate.toLocaleTimeString("en-US", timeOptions)}
          </span>
        </div>
      </div>
    </section>
  );
};

export default WelcomeBanner;
