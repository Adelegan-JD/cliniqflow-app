import React from 'react';
import Input from '../ui/Input';
import Select from '../ui/Select';
import { STATE_OPTIONS, LGA_BY_STATE } from '../../data/nigerianStatesLgas';

const StepTwo = ({ formData, handleChange, errors = {} }) => {
  const availableLgas = (LGA_BY_STATE[formData.state] || []).map((name) => ({ value: name, label: name }));

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="border-b border-gray-300 pb-2">
        <h3 className="text-lg font-semibold text-gray-700">Contact Information</h3>
        <p className="text-sm text-gray-500">How can we reach the patient?</p>
      </div>

      {/* Phone Numbers */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Input 
          label="Primary Phone Number" 
          name="phone" 
          type="tel"
          placeholder="e.g. 08012345678 (11 digits, starts with 07/08/09)"
          value={formData.phone} 
          onChange={handleChange} 
          error={errors?.phone}
          required 
        />
        <Input 
          label="Alternative Phone Number" 
          name="altPhone" 
          type="tel"
          placeholder="e.g. 09012345678 (optional)"
          value={formData.altPhone} 
          onChange={handleChange} 
          error={errors?.altPhone}
        />
      </div>

      {/* Email */}
      <div className="grid grid-cols-1 gap-6">
        <Input 
          label="Email Address" 
          name="email" 
          type="email"
          placeholder="e.g. patient@email.com (optional)"
          value={formData.email} 
          onChange={handleChange} 
          error={errors?.email}
        />
      </div>

      <div className="border-b border-gray-300 pb-2 pt-4">
        <h3 className="text-lg font-semibold text-gray-700">Location Details</h3>
      </div>

      {/* Address - Full Width */}
      <div className="grid grid-cols-1 gap-6">
        <Input 
          label="Residential Address" 
          name="address" 
          placeholder="e.g. 12 Adeola Street, Victoria Island, Lagos"
          value={formData.address} 
          onChange={handleChange} 
          error={errors?.address}
          required 
        />
      </div>

      {/* State and LGA */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Select 
          label="State of Residence" 
          name="state" 
          value={formData.state} 
          onChange={handleChange} 
          options={STATE_OPTIONS}
          error={errors?.state}
          required 
        />
        <Select 
          label="Local Government Area (LGA)" 
          name="lga" 
          value={formData.lga} 
          onChange={handleChange} 
          options={availableLgas}
          error={errors?.lga}
          required 
          disabled={!formData.state}
        />
      </div>
    </div>
  );
};

export default StepTwo;