import React from "react";

const Sidebars = () => {
    const menu = [
    { name: 'Dashboard', icon: '📊' },
    { name: 'Register Patient', icon: '📝', active: true },
    { name: 'Patient Records', icon: '📁' },
    { name: 'Appointments', icon: '📅' },
    ];
    return (
        <div className="w-64 h-screen bg-slate-900 text-white flex flex-col">
            <div className="p-6 text-xl font-bold border-b border-slate-800 text-blue-400">
                Cliniq-Flow
            </div>
            <nav className="flex-1 mt-4">
                {menu.map((item) => (
                    <div
                        key={item.name}
                        className={`p-4 flex items-center gap-3 cursor-pointer hover:bg-slate-800 ${item.active ? "bg-slate-800" : ""}`}
                    >
                        <span className="text-lg">{item.icon}</span>
                        <span>{item.name}</span>
                    </div>
                ))}
            </nav>
            <div className="p-6 border-t border-slate-800 text-sm text-slate-400">
               Record Officer portal
            </div>
        </div>
    )
}

export default Sidebars