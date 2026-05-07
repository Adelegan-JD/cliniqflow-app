import React from "react";
import { MapPin, Phone } from "lucide-react";
import Input from "../../../components/ui/Input";
import Select from "../../../components/ui/Select";

export const Step2Contact = ({
  formData,
  handleChange,
  errors = {},
  stateOptions = [],
  lgaOptions = [],
}) => {
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
          <Input
            label="Primary Phone"
            name="phone"
            type="tel"
            value={formData.phone}
            onChange={handleChange}
            placeholder="08012345678"
            error={errors.phone}
            required
          />
          <Input
            label="Alt. Phone (Optional)"
            name="altPhone"
            type="tel"
            value={formData.altPhone}
            onChange={handleChange}
            placeholder="09012345678"
            error={errors.altPhone}
          />
          <div className="md:col-span-2">
            <Input
              label="Email Address (Optional)"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="patient@email.com"
              error={errors.email}
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
            <Input
              label="Full Address"
              name="address"
              value={formData.address}
              onChange={handleChange}
              placeholder="e.g. 12 Adeola Street, Victoria Island"
              error={errors.address}
              required
            />
          </div>
          <div>
            <Select
              label="State of Residence"
              name="state"
              value={formData.state}
              onChange={handleChange}
              options={stateOptions}
              error={errors.state}
              required
            />
          </div>
          <div>
            <Select
              label="Local Govt. Area (LGA)"
              name="lga"
              value={formData.lga}
              onChange={handleChange}
              options={lgaOptions}
              error={errors.lga}
              required
              disabled={!formData.state}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
