import { z } from "zod";

const blankToUndefined = (value) =>
  value === "" || value === null || value === undefined ? undefined : value;

const optionalText = z.preprocess(blankToUndefined, z.string().optional());
const optionalEmail = z.preprocess(
  blankToUndefined,
  z.string().email("Invalid email").optional(),
);

// Schema aligned with backend app.schemas.workflows.RegisterPatientBody
export const registrationSchema = z.object({
  // Required personal info
  firstName: z.string().min(2, "First name required"),
  lastName: z.string().min(2, "Last name required"),
  otherNames: z.preprocess(blankToUndefined, z.string().min(2).optional()),
  dob: z.string().min(1, "Date of birth is required"),
  gender: z.string().min(1, "Gender is required"),

  // Administrative / optional
  civilStatus: optionalText,
  religion: optionalText,
  tribe: optionalText,
  nationality: optionalText,

  // Contact info
  phone: z.string().min(10, "Invalid phone number"),
  altPhone: optionalText,
  email: optionalEmail,
  address: z.string().min(5, "Address too short"),
  state: optionalText,
  lga: optionalText,

  // Identifiers / statutory
  nin: optionalText,
  nhisNumber: optionalText,
  militaryNumber: optionalText,
  education: optionalText,
  occupation: optionalText,

  // Next of kin — backend requires name, relationship, phone; address optional
  nokName: z.string().min(2, "Next of kin name required"),
  nokRelationship: z.string().min(1, "Relationship required"),
  nokPhone: z.string().min(10, "Next of kin phone required"),
  nokAddress: optionalText,
});
