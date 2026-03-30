import React from "react";
import { ShieldCheck, Briefcase } from "lucide-react";

export const Step3Statutory = () => {
  return (
    <div className="animate-fadeIn">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800">
          Statutory & Socio-Economic
        </h2>
        <p className="text-gray-500 text-sm mt-1">
          Official government and insurance records.
        </p>
      </div>

      <div className="mb-8">
        <div className="flex items-center gap-2 mb-4 text-gray-800">
          <ShieldCheck size={18} className="text-indigo-600" />
          <h3 className="font-semibold">Identification Documents</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              NIN
            </label>
            <input
              type="text"
              placeholder="11 digits"
              className="w-full rounded-lg border-gray-300 border px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              NHIS Number
            </label>
            <input
              type="text"
              placeholder="Optional"
              className="w-full rounded-lg border-gray-300 border px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Military Number
            </label>
            <input
              type="text"
              placeholder="If applicable"
              className="w-full rounded-lg border-gray-300 border px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>
        </div>
      </div>

      <div className="mb-8">
        <div className="flex items-center gap-2 mb-4 text-gray-800">
          <Briefcase size={18} className="text-indigo-600" />
          <h3 className="font-semibold">Socio-Economic Info</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Highest Education
            </label>
            <select className="w-full rounded-lg border-gray-300 border px-4 py-2.5 text-gray-700 focus:ring-2 focus:ring-indigo-500 outline-none">
              <option>Select Education</option>
              <option>BSc</option>
              <option>Masters</option>
              <option>SSCE</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Occupation
            </label>
            <input
              type="text"
              placeholder="e.g. Software Engineer"
              className="w-full rounded-lg border-gray-300 border px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>
        </div>
      </div>

      {/* Admin Block */}
      <div className="bg-blue-50/50 border border-blue-100 rounded-xl p-5">
        <p className="text-xs text-blue-600 mb-3 font-medium uppercase tracking-wider">
          Administrative (Auto-filled)
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">
              Date of Registration
            </label>
            <input
              type="text"
              disabled
              defaultValue="30/03/2026"
              className="w-full rounded-lg bg-white border border-blue-100 px-4 py-2.5 text-gray-500 cursor-not-allowed shadow-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">
              Registered By
            </label>
            <input
              type="text"
              disabled
              defaultValue="Faith Peace"
              className="w-full rounded-lg bg-white border border-blue-100 px-4 py-2.5 text-gray-500 cursor-not-allowed shadow-sm"
            />
          </div>
        </div>
      </div>
    </div>
  );
};
