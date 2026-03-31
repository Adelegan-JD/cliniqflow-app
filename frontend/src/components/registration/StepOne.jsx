import React from 'react';
import Select from '../ui/Select';
import Input from '../ui/Input';
import { User } from 'lucide-react';
import { Label } from '../ui/Label';

const StepOne = ({ formData, handleChange, errors = {} }) => {
  return (
    <div className="space-y-8">
      {/* Photo & Basic Info Row */}
      <div className="flex flex-col md:flex-row gap-8">
        {/* Passport Placeholder */}
        <Label htmlFor='upload' tabIndex={0}>
          <span className="text-2xl mb-2"><User size={32} /></span>
          <span className="text-[10px] uppercase font-bold text-gray-400">Upload Photo</span>
        </Label>

        <input type='file' className='border hidden' id='upload' />

        <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input 
            label="Patient ID (PID)" 
            name="pid" 
            value="" 
            placeholder="Auto-generated"
            readOnly
            helperText="Auto-generated"
          />
          <Select 
            label="Civil Status" 
            name="civilStatus" 
            value={formData.civilStatus} 
            onChange={handleChange}
            options={[
              {value:"single", label:"Single"},
              {value:"married", label:"Married"},
              {value:"divorced", label:"Divorced"},
              {value:"widowed", label:"Widowed"},
              {value:"separated", label:"Separated"}
            ]}
            error={errors.civilStatus}
            required 
          />
        </div>
      </div>

      {/* Name Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Input 
          label="Last Name" 
          name="lastName" 
          placeholder="e.g. Lasisi, Okafor" 
          value={formData.lastName} 
          onChange={handleChange} 
          error={errors.lastName}
          required 
        />
        <Input 
          label="First Name" 
          name="firstName" 
          placeholder="e.g. Chidi, Fatima" 
          value={formData.firstName} 
          onChange={handleChange} 
          error={errors.firstName}
          required 
        />
        <Input 
          label="Other Names" 
          name="otherNames" 
          placeholder="e.g. Adaeze, middle names (optional)" 
          value={formData.otherNames} 
          onChange={handleChange} 
          error={errors.otherNames}
        />
      </div>

      {/* Demographic Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Input
          label="Date of Birth" 
          name="dob" 
          type="date" 
          value={formData.dob} 
          onChange={handleChange} 
          error={errors.dob}
          required 
        />
        <Input
          label="Age" 
          name="age" 
          value={formData.age} 
          onChange={handleChange} 
          placeholder="Auto-calculated from date of birth"
          readOnly
        />
        <Select 
          label="Gender" 
          name="gender" 
          value={formData.gender} 
          onChange={handleChange} 
          options={[
            {value:"male", label:"Male"},
            {value:"female", label:"Female"},
            {value:"other", label:"Other"}
          ]}
          error={errors.gender}
          required 
        />
        <Input 
          label="Nationality" 
          name="nationality" 
          placeholder="e.g. Nigerian, Ghanaian" 
          value={formData.nationality} 
          onChange={handleChange} 
          error={errors.nationality}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input 
          label="Tribe" 
          name="tribe" 
          placeholder="e.g. Yoruba, Igbo, Hausa (optional)" 
          value={formData.tribe} 
          onChange={handleChange} 
          error={errors.tribe}
        />
        <Select 
          label="Religion" 
          name="religion" 
          value={formData.religion} 
          onChange={handleChange} 
          options={[
            {value:"christianity", label:"Christianity"},
            {value:"islam", label:"Islam"},
            {value:"traditional", label:"Traditional"},
            {value:"other", label:"Other"}
          ]}
        />
      </div>
    </div>
  );
};

export default StepOne;