import React from "react";
import { MapPin, Phone } from "lucide-react";

export const Step2Contact = () => {
  return (
    <div className="animate-fadeIn">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Contact & Location</h2>
        <p className="text-gray-500 text-sm mt-1">
          How can we reach the patient?
        </p>
      </div>

      {/* Contact Card Group */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 mb-6 shadow-sm">
        <div className="flex items-center gap-2 mb-4 text-indigo-600">
          <Phone size={18} />
          <h3 className="font-semibold text-gray-800">Communication</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Primary Phone *
            </label>
            <input
              type="tel"
              placeholder="08012345678"
              className="w-full rounded-lg border-gray-300 border px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Alt. Phone (Optional)
            </label>
            <input
              type="tel"
              placeholder="09012345678"
              className="w-full rounded-lg border-gray-300 border px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email Address (Optional)
            </label>
            <input
              type="email"
              placeholder="patient@email.com"
              className="w-full rounded-lg border-gray-300 border px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>
        </div>
      </div>

      {/* Location Card Group */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
        <div className="flex items-center gap-2 mb-4 text-indigo-600">
          <MapPin size={18} />
          <h3 className="font-semibold text-gray-800">Residential Address</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Full Address *
            </label>
            <input
              type="text"
              placeholder="e.g. 12 Adeola Street, Victoria Island"
              className="w-full rounded-lg border-gray-300 border px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              State of Residence *
            </label>
            <select className="w-full rounded-lg border-gray-300 border px-4 py-2.5 text-gray-700 focus:ring-2 focus:ring-indigo-500 outline-none">
              <option>Select State</option>
              <option>Lagos</option>
              <option>Abuja</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Local Govt. Area (LGA) *
            </label>
            <select className="w-full rounded-lg border-gray-300 border px-4 py-2.5 text-gray-700 focus:ring-2 focus:ring-indigo-500 outline-none">
              <option>Select LGA</option>
              <option>Eti-Osa</option>
              <option>Ikeja</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );
};
