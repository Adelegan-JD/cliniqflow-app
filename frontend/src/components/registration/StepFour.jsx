import React from 'react';
import Input from '../ui/Input';
import Select from '../ui/Select';
import { TriangleAlert } from 'lucide-react';

const StepFour = ({ formData, handleChange, errors = {} }) => {
  const relationships = [{ value: 'Parent', label: 'Parent' }, { value: 'Sibling', label: 'Sibling' }, { value: 'Spouse', label: 'Spouse' }, { value: 'Child', label: 'Child' }, { value: 'Friend', label: 'Friend' }, { value: 'Other', label: 'Other' }];

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
      {/* Next of Kin Section */}
      <div className="bg-orange-50/50 p-6 rounded-2xl border border-orange-100">
        <div className="flex items-center gap-2 mb-6 text-orange-700">
          <span className="text-xl"><TriangleAlert size={20} /></span>
          <h3 className="text-lg font-bold">Next of Kin (Emergency Contact)</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Input 
            label="Full Name" 
            name="nokName" 
            placeholder="e.g. Adewale Johnson (full name)"
            value={formData.nokName} 
            onChange={handleChange} 
            error={errors?.nokName}
            required 
          />
          <Select 
            label="Relationship" 
            name="nokRelationship" 
            value={formData.nokRelationship} 
            onChange={handleChange} 
            options={relationships}
            error={errors?.nokRelationship}
            required 
          />
          <Input 
            label="Phone Number" 
            name="nokPhone" 
            placeholder="e.g. 08011122233 (11 digits, starts with 07/08/09)"
            value={formData.nokPhone} 
            onChange={handleChange} 
            error={errors?.nokPhone}
            required 
          />
          <Input 
            label="Residential Address" 
            name="nokAddress" 
            placeholder="e.g. 5 Ogun Street, Ikeja, Lagos"
            value={formData.nokAddress} 
            onChange={handleChange} 
            error={errors?.nokAddress}
            required 
          />
        </div>
      </div>
    </div>
  );
};

export default StepFour;