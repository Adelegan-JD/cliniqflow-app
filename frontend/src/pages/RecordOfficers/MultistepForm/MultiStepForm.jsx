import React, { useEffect, useMemo, useState } from "react";
import {
  User,
  Map,
  FileText,
  Users,
  ChevronRight,
  ChevronLeft,
  Check,
} from "lucide-react";
import { toast } from "react-toastify";
import { useAuth } from "../../../contexts/AuthContext";
import { useRegistrationStore } from "../../../store/RegistrationStore";
import {
  validateStep1,
  validateStep2,
  validateStep3,
  validateStep4,
} from "../../../utils/registrationValidation";
import { getLgaOptions, STATE_OPTIONS } from "../../../data/nigerianStatesLgas";

import { Step1BioData } from "./StepOne";
import { Step2Contact } from "./StepTwo";
import { Step3Statutory } from "./StepThree";
import { Step4NextOfKin } from "./StepFour";

const steps = [
  {
    id: 1,
    title: "Bio-data",
    description: "Primary identity details",
    icon: User,
  },
  { id: 2, title: "Contact", description: "Location and phone", icon: Map },
  {
    id: 3,
    title: "Statutory",
    description: "IDs & Socio-Economic",
    icon: FileText,
  },
  {
    id: 4,
    title: "Next of Kin",
    description: "Emergency contact",
    icon: Users,
  },
];

const initialData = {
  lastName: "",
  firstName: "",
  otherNames: "",
  pid: "",
  passport: null,
  tribe: "",
  religion: "",
  gender: "",
  dob: "",
  age: "",
  nationality: "Nigerian",
  civilStatus: "",
  phone: "",
  altPhone: "",
  email: "",
  address: "",
  state: "",
  lga: "",
  nin: "",
  nhisNumber: "",
  militaryNumber: "",
  education: "",
  regDate: new Date().toISOString().split("T")[0],
  regBy: "",
  occupation: "",
  nokName: "",
  nokPhone: "",
  nokRelationship: "",
  nokAddress: "",
};

const calcAge = (dob) => {
  if (!dob) return "";
  const birthDate = new Date(dob);
  if (Number.isNaN(birthDate.getTime())) return "";
  const today = new Date();
  let age = today.getFullYear() - birthDate.getFullYear();
  const m = today.getMonth() - birthDate.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
    age--;
  }
  return age > 0 ? String(age) : "0";
};

export const MultiStepRegistration = () => {
  const { user } = useAuth();
  const [currentStep, setCurrentStep] = useState(1);
  const [errors, setErrors] = useState({});
  const [submitStatus, setSubmitStatus] = useState({
    type: "idle",
    message: "",
  });

  const formData = useRegistrationStore((state) => state.formData);
  const setField = useRegistrationStore((state) => state.setField);
  const setFormData = useRegistrationStore((state) => state.setFormData);
  const submit = useRegistrationStore((state) => state.submit);
  const isSubmitting = useRegistrationStore((state) => state.isSubmitting);

  useEffect(() => {
    if (user) {
      setField("regBy", user.email || user.user_metadata?.full_name || "");
    }
  }, [user, setField]);

  const stateLgaOptions = useMemo(
    () => getLgaOptions(formData.state),
    [formData.state],
  );

  const handleChange = (e) => {
    const { name, value } = e.target;
    setField(name, value);
    setErrors((prev) => {
      const next = { ...prev };
      delete next[name];
      if (name === "state") delete next.lga;
      return next;
    });
    if (name === "dob") {
      setField("age", calcAge(value));
    }
    if (name === "state") {
      setField("lga", "");
    }
  };

  const validateCurrentStep = (step) => {
    switch (step) {
      case 1:
        return validateStep1(formData);
      case 2:
        return validateStep2(formData);
      case 3:
        return validateStep3(formData);
      case 4:
        return validateStep4(formData);
      default:
        return { valid: true, errors: {} };
    }
  };

  const handleNext = () => {
    const result = validateCurrentStep(currentStep);
    if (!result.valid) {
      setErrors(result.errors);
      setSubmitStatus({
        type: "error",
        message: "Please fix the highlighted fields before continuing.",
      });
      return;
    }
    setErrors({});
    setSubmitStatus({ type: "idle", message: "" });
    setCurrentStep((prev) => Math.min(prev + 1, 4));
  };

  const handlePrev = () => {
    setErrors({});
    setSubmitStatus({ type: "idle", message: "" });
    setCurrentStep((prev) => Math.max(prev - 1, 1));
  };

  const handleFinish = async () => {
    const result = validateCurrentStep(4);
    if (!result.valid) {
      setErrors(result.errors);
      setSubmitStatus({
        type: "error",
        message: "Please fix the highlighted fields before submitting.",
      });
      return;
    }

    setErrors({});
    setSubmitStatus({
      type: "pending",
      message: "Submitting patient registration...",
    });

    try {
      console.log("[MultiStepRegistration] payload before submit:", formData);
      const response = await submit();
      console.log("[MultiStepRegistration] submit response:", response);

      if (!response.success) {
        throw response.error || new Error("Registration failed");
      }

      toast.success(
        response.data?.pid
          ? `Patient ${response.data.pid} registered successfully!`
          : "Patient registered successfully!",
      );
      setSubmitStatus({
        type: "success",
        message: response.data?.pid
          ? `Saved successfully as ${response.data.pid}`
          : "Saved successfully",
      });
      setCurrentStep(1);
      setFormData(initialData);
    } catch (err) {
      console.error("[MultiStepRegistration] submit error:", err);
      setSubmitStatus({
        type: "error",
        message: err?.status
          ? `${err.message} (HTTP ${err.status})`
          : err?.message || "Registration failed",
      });
      toast.error(err?.message || "Registration failed");
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <Step1BioData
            formData={formData}
            handleChange={handleChange}
            errors={errors}
          />
        );
      case 2:
        return (
          <Step2Contact
            formData={formData}
            handleChange={handleChange}
            errors={errors}
            stateOptions={STATE_OPTIONS}
            lgaOptions={stateLgaOptions}
          />
        );
      case 3:
        return (
          <Step3Statutory
            formData={formData}
            handleChange={handleChange}
            errors={errors}
          />
        );
      case 4:
        return (
          <Step4NextOfKin
            formData={formData}
            handleChange={handleChange}
            errors={errors}
          />
        );
      default:
        return (
          <Step1BioData
            formData={formData}
            handleChange={handleChange}
            errors={errors}
          />
        );
    }
  };

  return (
    <div className="bg-gray-50 p-4 lg:p-8 font-sans w-full overflow-auto">
      <div className="w-full bg-white rounded-2xl shadow-xl overflow-hidden flex flex-col">
        <header className="w-full border-b border-gray-100 px-8 py-8 lg:px-12 bg-white z-10 relative">
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-gray-900">
                Registration
              </h1>
              <p className="text-gray-500 text-sm mt-1">Patient Onboarding</p>
            </div>
            <div className="hidden sm:block text-xs font-medium px-3 py-1.5 bg-indigo-50 text-indigo-700 rounded-full border border-indigo-100">
              Step {currentStep} of {steps.length}
            </div>
          </div>

          <nav aria-label="Progress">
            <div className="flex items-center w-full">
              {steps.map((step, index) => {
                const isActive = currentStep === step.id;
                const isCompleted = currentStep > step.id;
                const Icon = step.icon;

                return (
                  <React.Fragment key={step.id}>
                    <div className="flex flex-col items-center relative z-10 w-24 sm:w-32 group">
                      <div
                        className={`relative w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 border-4 ${
                          isActive
                            ? "bg-indigo-600 text-white border-indigo-100 shadow-lg shadow-indigo-600/30"
                            : isCompleted
                              ? "bg-indigo-600 text-white border-indigo-50"
                              : "bg-white border-gray-100 text-gray-400"
                        }`}
                      >
                        {isCompleted ? (
                          <Check size={20} strokeWidth={3} />
                        ) : (
                          <Icon size={20} />
                        )}
                      </div>

                      <div className="mt-3 text-center">
                        <h4
                          className={`text-sm font-semibold transition-colors ${
                            isActive
                              ? "text-indigo-600"
                              : isCompleted
                                ? "text-gray-900"
                                : "text-gray-400"
                          }`}
                        >
                          {step.title}
                        </h4>
                        <p className="text-[11px] text-gray-500 mt-0.5 hidden sm:block">
                          {step.description}
                        </p>
                      </div>
                    </div>

                    {index !== steps.length - 1 && (
                      <div className="flex-1 flex items-center -mt-10 px-2 sm:px-4">
                        <div
                          className={`h-1 w-full rounded-full transition-colors duration-500 ${isCompleted ? "bg-indigo-600" : "bg-gray-100"}`}
                        />
                      </div>
                    )}
                  </React.Fragment>
                );
              })}
            </div>
          </nav>
        </header>

        {submitStatus.type !== "idle" && (
          <div
            className={`mx-8 mt-4 rounded-lg border px-4 py-3 text-sm ${
              submitStatus.type === "success"
                ? "border-green-200 bg-green-50 text-green-700"
                : submitStatus.type === "error"
                  ? "border-red-200 bg-red-50 text-red-700"
                  : "border-blue-200 bg-blue-50 text-blue-700"
            }`}
          >
            {submitStatus.message}
          </div>
        )}

        <main className="flex-1 flex flex-col p-8 lg:p-12 overflow-y-auto bg-slate-50/50">
          <div className="flex-1 max-w-4xl mx-auto w-full">
            {renderStepContent()}
          </div>

          <div className="mt-8 pt-6 border-t border-gray-200 flex items-center justify-between max-w-4xl mx-auto w-full">
            <button
              type="button"
              onClick={handlePrev}
              disabled={currentStep === 1}
              className={`flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                currentStep === 1
                  ? "text-gray-300 cursor-not-allowed"
                  : "text-gray-600 hover:bg-gray-200 bg-white border border-gray-200 shadow-sm"
              }`}
            >
              <ChevronLeft size={18} />
              Previous
            </button>

            {currentStep < 4 ? (
              <button
                type="button"
                onClick={handleNext}
                className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 hover:shadow-lg hover:shadow-indigo-500/30 transition-all active:scale-95"
              >
                Next Step
                <ChevronRight size={18} />
              </button>
            ) : (
              <button
                type="button"
                onClick={handleFinish}
                disabled={isSubmitting}
                className="flex items-center gap-2 px-8 py-2.5 rounded-lg bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 hover:shadow-lg hover:shadow-emerald-500/30 transition-all active:scale-95 disabled:opacity-50"
              >
                <Check size={18} />
                {isSubmitting ? "Submitting..." : "Finish & Register"}
              </button>
            )}
          </div>
        </main>
      </div>
    </div>
  );
};

export default MultiStepRegistration;
