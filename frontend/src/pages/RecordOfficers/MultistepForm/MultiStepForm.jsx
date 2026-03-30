import React, { useState } from 'react';
import { User, Map, FileText, Users, ChevronRight, ChevronLeft, Check } from 'lucide-react';

// Import the steps above here if in separate files.
import { Step1BioData } from './StepOne';
import { Step2Contact } from './StepTwo';
import { Step3Statutory } from './StepThree';
import { Step4NextOfKin } from './StepFour';

const steps = [
  { id: 1, title: 'Bio-data', description: 'Primary identity details', icon: User },
  { id: 2, title: 'Contact', description: 'Location and phone', icon: Map },
  { id: 3, title: 'Statutory', description: 'IDs & Socio-Economic', icon: FileText },
  { id: 4, title: 'Next of Kin', description: 'Emergency contact', icon: Users },
];

export const MultiStepRegistration = () => {
  const [currentStep, setCurrentStep] = useState(1);

  const handleNext = () => currentStep < 4 && setCurrentStep((prev) => prev + 1);
  const handlePrev = () => currentStep > 1 && setCurrentStep((prev) => prev - 1);

  const renderStepContent = () => {
    switch (currentStep) {
      case 1: return <Step1BioData />;
      case 2: return <Step2Contact />;
      case 3: return <Step3Statutory />;
      case 4: return <Step4NextOfKin />;
      default: return <Step1BioData />;
    }
  };

  return (
    <div className="bg-gray-50 p-4 lg:p-8 font-sans w-full overflow-auto">
      <div className="w-full bg-white rounded-2xl shadow-xl overflow-hidden flex flex-col">
        
        {/* Top Header & Navigation */}
        <header className="w-full border-b border-gray-100 px-8 py-8 lg:px-12 bg-white z-10 relative">
          {/* Logo & Title */}
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-gray-900">Registeration</h1>
              <p className="text-gray-500 text-sm mt-1">Patient Onboarding</p>
            </div>
            <div className="hidden sm:block text-xs font-medium px-3 py-1.5 bg-indigo-50 text-indigo-700 rounded-full border border-indigo-100">
              Step {currentStep} of {steps.length}
            </div>
          </div>

          {/* Horizontal Stepper */}
          <nav aria-label="Progress">
            <div className="flex items-center w-full">
              {steps.map((step, index) => {
                const isActive = currentStep === step.id;
                const isCompleted = currentStep > step.id;
                const Icon = step.icon;

                return (
                  <React.Fragment key={step.id}>
                    {/* Step Node */}
                    <div className="flex flex-col items-center relative z-10 w-24 sm:w-32 group">
                      <div className={`relative w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 border-4 ${
                        isActive ? 'bg-indigo-600 text-white border-indigo-100 shadow-lg shadow-indigo-600/30' : 
                        isCompleted ? 'bg-indigo-600 text-white border-indigo-50' : 'bg-white border-gray-100 text-gray-400'
                      }`}>
                        {isCompleted ? <Check size={20} strokeWidth={3} /> : <Icon size={20} />}
                      </div>
                      
                      {/* Step Text */}
                      <div className="mt-3 text-center">
                        <h4 className={`text-sm font-semibold transition-colors ${isActive ? 'text-indigo-600' : isCompleted ? 'text-gray-900' : 'text-gray-400'}`}>
                          {step.title}
                        </h4>
                        <p className="text-[11px] text-gray-500 mt-0.5 hidden sm:block">
                          {step.description}
                        </p>
                      </div>
                    </div>

                    {/* Connecting Line */}
                    {index !== steps.length - 1 && (
                      <div className="flex-1 flex items-center -mt-10 px-2 sm:px-4">
                        <div className={`h-1 w-full rounded-full transition-colors duration-500 ${
                          isCompleted ? 'bg-indigo-600' : 'bg-gray-100'
                        }`} />
                      </div>
                    )}
                  </React.Fragment>
                );
              })}
            </div>
          </nav>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 flex flex-col p-8 lg:p-12 overflow-y-auto bg-slate-50/50">
          {/* Dynamic Form Step */}
          <div className="flex-1 max-w-4xl mx-auto w-full">
            {renderStepContent()}
          </div>

          {/* Footer Navigation Controls */}
          <div className="mt-8 pt-6 border-t border-gray-200 flex items-center justify-between max-w-4xl mx-auto w-full">
            <button
              onClick={handlePrev}
              disabled={currentStep === 1}
              className={`flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                currentStep === 1 
                  ? 'text-gray-300 cursor-not-allowed' 
                  : 'text-gray-600 hover:bg-gray-200 bg-white border border-gray-200 shadow-sm'
              }`}
            >
              <ChevronLeft size={18} />
              Previous
            </button>

            {currentStep < 4 ? (
              <button
                onClick={handleNext}
                className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 hover:shadow-lg hover:shadow-indigo-500/30 transition-all active:scale-95"
              >
                Next Step
                <ChevronRight size={18} />
              </button>
            ) : (
              <button
                className="flex items-center gap-2 px-8 py-2.5 rounded-lg bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 hover:shadow-lg hover:shadow-emerald-500/30 transition-all active:scale-95"
              >
                <Check size={18} />
                Finish & Register
              </button>
            )}
          </div>
        </main>
      </div>
    </div>
  );
};

export default MultiStepRegistration;