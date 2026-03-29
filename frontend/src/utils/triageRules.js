export function getTriageResult({ symptoms }) {
  const text = symptoms.toLowerCase();

  const breathingIssues = [
    "difficulty breathing",
    "difficult breathing",
    "difficult in breathing",
    "shortness of breath",
    "breathing problem",
  ];

  const hasBreathingIssue = breathingIssues.some(keyword =>
    text.includes(keyword)
  );

  const hasFever = text.includes("fever");

  // 🔴 RED: breathing issue OR fever + breathing issue
  if (hasBreathingIssue || text.includes("chest pain") || text.includes("bleeding")) {
    return {
      level: "RED",
      reason: "Breathing difficulty or other severe symptoms detected.",
    };
  }

  // 🟡 YELLOW: fever without breathing distress
  if (hasFever || text.includes("vomiting") || text.includes("pain")) {
    return {
      level: "YELLOW",
      reason: "Symptoms suggest urgent care is needed but not life-threatening.",
    };
  }

  // 🟢 GREEN: stable
  return {
    level: "GREEN",
    reason: "No critical symptoms detected. Patient appears stable.",
  };
}
