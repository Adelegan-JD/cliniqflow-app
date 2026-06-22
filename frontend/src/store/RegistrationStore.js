import { create } from "zustand";
import { api } from "../utils/api";
import { registrationSchema } from "../utils/RegistrationValSchema";

export const useRegistrationStore = create((set, get) => ({
  step: 1,
  formData: {
    // match the form in RegistrationForm.jsx
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
  },
  errors: {},
  isSubmitting: false,

  setField: (field, value) =>
    set((state) => ({
      formData: { ...state.formData, [field]: value },
      errors: { ...state.errors, [field]: null },
    })),
  setFormData: (data) => set({ formData: { ...get().formData, ...data } }),

  validateAll: () => {
    const { formData } = get();
    const dataForValidation = {
      firstName: formData.firstName,
      lastName: formData.lastName,
      otherNames: formData.otherNames || null,
      dob: formData.dob,
      gender: formData.gender,
      civilStatus: formData.civilStatus || null,
      religion: formData.religion || null,
      tribe: formData.tribe || null,
      nationality: formData.nationality || null,
      phone: formData.phone,
      altPhone: formData.altPhone || null,
      email: formData.email || null,
      address: formData.address,
      state: formData.state || null,
      lga: formData.lga || null,
      nin: formData.nin || null,
      nhisNumber: formData.nhisNumber || null,
      militaryNumber: formData.militaryNumber || null,
      education: formData.education || null,
      occupation: formData.occupation || null,
      nokName: formData.nokName,
      nokRelationship: formData.nokRelationship,
      nokPhone: formData.nokPhone,
      nokAddress: formData.nokAddress || null,
    };

    const result = registrationSchema.safeParse(dataForValidation);
    if (!result.success) {
      const fieldErrors = result.error.flatten().fieldErrors;
      set({ errors: fieldErrors });
      return { valid: false, errors: fieldErrors };
    }
    set({ errors: {} });
    return { valid: true, data: result.data };
  },

  submit: async () => {
    const { validateAll, formData } = get();
    const v = validateAll();
    if (!v.valid) return { success: false, errors: v.errors };

    set({ isSubmitting: true });
    try {
      // Normalize payload: convert empty-string optional fields to explicit null
      const payload = v.data;
      const normalized = Object.fromEntries(
        Object.entries(payload).map(([k, val]) => [
          k,
          val === "" || val === undefined ? null : val,
        ]),
      );

      const resp = await api.post(
        "/record-officer/register-patient",
        normalized,
      );
      // reset form on success
      set({
        formData: {
          ...get().formData,
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
          occupation: "",
          nokName: "",
          nokPhone: "",
          nokRelationship: "",
          nokAddress: "",
        },
        errors: {},
      });
      return { success: true, data: resp };
    } catch (err) {
      console.error("Registration submit error:", err);
      return { success: false, error: err };
    } finally {
      set({ isSubmitting: false });
    }
  },

  nextStep: () => set((s) => ({ step: s.step + 1 })),
  prevStep: () => set((s) => ({ step: Math.max(1, s.step - 1) })),
}));
