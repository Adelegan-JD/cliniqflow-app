import React, { useRef, useState, useEffect } from "react";
import {
  Mic,
  MicOff,
  BotMessageSquare,
  AudioLines,
  X,
  Loader2,
  CheckCircle,
  AlertCircle,
  User,
  Clock,
} from "lucide-react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { toast } from "react-toastify";
import { api } from "../../utils/api";
import { getToken } from "../../utils/uitils";

const normalizePatient = (p, fallbackPatientId) => {
  const fullName =
    p?.patient_name ||
    p?.name ||
    p?.full_name ||
    [p?.firstName || p?.first_name, p?.lastName || p?.last_name]
      .filter(Boolean)
      .join(" ") ||
    null;

  return {
    ...p,
    patientId: p?.patientId || p?.patient_id || p?.pid || fallbackPatientId,
    name: fullName || "Unknown Patient",
  };
};

const RecordingSession = () => {
  const navigate = useNavigate();
  const { patientId, sessionId } = useParams();
  const visitId = sessionId; // route uses :sessionId for the visit/session identifier
  const location = useLocation();

  const [patient, setPatient] = useState(
    normalizePatient(
      location.state?.patient || {
        patientId,
        name: "Selected Patient",
        age: "—",
        sex: "—",
      },
      patientId,
    ),
  );

  // Session management
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [sessionPath, setSessionPath] = useState("");
  const [sessionLoading, setSessionLoading] = useState(true);
  const [sessionError, setSessionError] = useState("");

  // Recording state
  const [isRecording, setIsRecording] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isEnding, setIsEnding] = useState(false);
  const [error, setError] = useState("");
  const [interimText, setInterimText] = useState("");
  const [messages, setMessages] = useState([]);
  const [audioUrl, setAudioUrl] = useState("");
  const [recordingDuration, setRecordingDuration] = useState(0);

  const mediaRecorderRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const chunksRef = useRef([]);
  const recordingTimerRef = useRef(null);
  const chunkQueueRef = useRef([]);
  const chunkIndexRef = useRef(0);
  const isUploadingChunkRef = useRef(false);
  const retryTimerRef = useRef(null);
  const aiUnavailableNotifiedRef = useRef(false);

  const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

  // Initialize consultation session on mount
  useEffect(() => {
    const initializeSession = async () => {
      if (!patientId || !visitId) {
        setSessionError("Patient ID or Visit ID missing");
        setSessionLoading(false);
        return;
      }

      // If patient was not passed in navigation state, fetch it and normalize name
      if (!location.state?.patient) {
        try {
          const p = await api.get(`/patients/${patientId}`);
          if (p) {
            setPatient((prev) =>
              normalizePatient(
                {
                  ...prev,
                  ...p,
                },
                patientId,
              ),
            );
          }
        } catch (e) {
          // non-fatal: continue with minimal patient info
          console.warn("Could not load patient info", e?.message || e);
        }
      }

      try {
        setSessionLoading(true);
        const response = await api.post("/consultation/session/start", {
          patient_id: patientId,
          visit_id: visitId,
          doctor_id: "current_user", // Will be from auth context
        });

        setActiveSessionId(response.session_id);
        setSessionPath(response.session_path);
        setSessionError("");
        toast.success(`Session started: ${response.session_id}`);
      } catch (err) {
        const errMsg =
          err?.message ||
          err?.response?.error?.message ||
          err?.response?.detail ||
          "Failed to start session";
        setSessionError(errMsg);
        toast.error(errMsg);
      } finally {
        setSessionLoading(false);
      }
    };

    initializeSession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [patientId, visitId]);

  // Recording timer effect
  useEffect(() => {
    if (isRecording) {
      recordingTimerRef.current = setInterval(() => {
        setRecordingDuration((d) => d + 1);
      }, 1000);
    } else {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
      setRecordingDuration(0);
    }

    return () => {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
    };
  }, [isRecording]);

  const stopTracks = () => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
  };

  const handleStartRecording = async () => {
    if (!activeSessionId) {
      setError("Session not initialized");
      return;
    }

    setError("");
    setIsStarting(true);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      chunksRef.current = [];
      chunkQueueRef.current = [];
      chunkIndexRef.current = 0;
      setInterimText("Whisper AI is transcribing in near real-time...");

      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = async (event) => {
        if (event.data && event.data.size > 0) {
          chunksRef.current.push(event.data);
          chunkQueueRef.current.push({
            blob: event.data,
            chunkIndex: chunkIndexRef.current++,
          });
          await processChunkQueue();
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        if (blob.size > 0) {
          const localAudioUrl = URL.createObjectURL(blob);
          setAudioUrl(localAudioUrl);
        }
      };

      // 4s chunked recording for near-live Whisper transcription.
      recorder.start(4000);

      setIsRecording(true);
    } catch (err) {
      setError(
        err?.message ||
          "Unable to access microphone. Please allow mic permission and try again.",
      );
    } finally {
      setIsStarting(false);
    }
  };

  const processChunkQueue = async () => {
    if (isUploadingChunkRef.current) return;
    if (!activeSessionId) {
      setError("Session ID missing");
      return;
    }

    if (!chunkQueueRef.current.length) return;

    isUploadingChunkRef.current = true;
    setIsTranscribing(true);

    try {
      while (chunkQueueRef.current.length > 0) {
        const currentChunk = chunkQueueRef.current.shift();
        const { blob, chunkIndex } = currentChunk;
        const token = await getToken();
        if (!token) throw new Error("Please sign in to transcribe audio");

        const formData = new FormData();
        formData.append("file", blob, `recording-${chunkIndex}.webm`);

        const res = await fetch(
          `${apiUrl}/consultation/session/${activeSessionId}/transcribe`,
          {
            method: "POST",
            headers: {
              Authorization: `Bearer ${token}`,
            },
            body: formData,
          },
        );

        const text = await res.text();
        let response = {};
        try {
          response = text ? JSON.parse(text) : {};
        } catch {
          response = {};
        }

        if (!res.ok) {
          const msg =
            response?.error?.message ||
            response?.detail ||
            `Whisper transcription failed (${res.status})`;

          // If AI is warming up/unavailable, put chunk back and retry later.
          if (res.status === 503 || msg.toLowerCase().includes("unavailable")) {
            chunkQueueRef.current.unshift(currentChunk);
            setInterimText("Whisper AI is warming up… retrying queued audio chunks.");
            if (!aiUnavailableNotifiedRef.current) {
              toast.info("Whisper service is warming up. Audio chunks will retry automatically.");
              aiUnavailableNotifiedRef.current = true;
            }
            break;
          }

          throw new Error(msg);
        }

        // Clear warm-up state once we get a successful chunk response.
        aiUnavailableNotifiedRef.current = false;
        if (interimText) {
          setInterimText("");
        }

        if (response.segments && response.segments.length > 0) {
          const aiSegments = response.segments
            .map((seg, idx) => ({
              id: `ai-${chunkIndex}-${idx}-${Date.now()}`,
              text: seg.translation || seg.text || "",
              speaker: seg.speaker || "SPEAKER_00",
              start: seg.start,
              end: seg.end,
              confidence: 0.98,
              source: "ai-whisper",
            }))
            .filter((m) => m.text && m.text.trim());

          if (aiSegments.length) {
            setMessages((prev) => [...prev, ...aiSegments]);
          }
        } else if (response.transcript?.trim()) {
          setMessages((prev) => [
            ...prev,
            {
              id: `ai-${chunkIndex}-${Date.now()}`,
              text: response.transcript,
              speaker: "SPEAKER_00",
              confidence: 0.98,
              source: "ai-whisper",
            },
          ]);
        }
      }
    } catch (err) {
      const errMsg =
        err?.message ||
        err?.response?.error?.message ||
        err?.response?.detail ||
        "Failed to transcribe audio";
      setError(errMsg);
      toast.error(errMsg);
    } finally {
      isUploadingChunkRef.current = false;
      setIsTranscribing(false);

      // Schedule retry if chunks remain (e.g., AI temporarily unavailable).
      if (chunkQueueRef.current.length > 0) {
        if (retryTimerRef.current) clearTimeout(retryTimerRef.current);
        retryTimerRef.current = setTimeout(() => {
          processChunkQueue();
        }, 5000);
      } else if (!isRecording) {
        setInterimText("");
      }
    }
  };

  const handleStopRecording = () => {
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state !== "inactive"
    ) {
      mediaRecorderRef.current.stop();
    }

    stopTracks();
    setIsRecording(false);
    if (!isUploadingChunkRef.current) {
      setInterimText("");
    }
  };

  useEffect(() => {
    return () => {
      if (retryTimerRef.current) {
        clearTimeout(retryTimerRef.current);
      }
    };
  }, []);

  const handleEndConsultation = async () => {
    if (!activeSessionId || !patientId) {
      toast.error("Session or Patient ID is missing");
      return;
    }

    setIsEnding(true);
    try {
      // End the consultation session on backend
      await api.post(`/consultation/session/${activeSessionId}/end`, {
        transcript: messages.map((m) => m.text).join("\n"),
        transcript_segments: messages,
        duration_seconds: recordingDuration,
      });

      // End the visit in the main system
      await api.post(
        `/doctor/end-consultation?visit_id=${encodeURIComponent(visitId)}`,
      );

      toast.success("Consultation ended successfully");
      setTimeout(() => {
        navigate("/doctors-dashboard", { replace: true });
      }, 1000);
    } catch (err) {
      toast.error(err?.message || "Failed to end consultation");
    } finally {
      setIsEnding(false);
    }
  };

  return (
    <div className="flex flex-col flex-1 p-4 overflow-auto gap-6">
      {/* Session Loading or Error */}
      {sessionLoading && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-center gap-3">
          <Loader2 size={20} className="text-blue-600 animate-spin" />
          <div>
            <p className="font-semibold text-blue-900">Initializing session...</p>
            <p className="text-sm text-blue-700">Creating consultation session</p>
          </div>
        </div>
      )}

      {sessionError && !sessionLoading && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3">
          <AlertCircle size={20} className="text-red-600 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-red-900">Session Error</p>
            <p className="text-sm text-red-700">{sessionError}</p>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-800">
          Recording Session
        </h1>
        <div className="text-gray-600 mt-3 space-y-2">
          <p className="flex items-center gap-2">
            <User size={16} className="text-gray-400" />
            Patient:{" "}
            <span className="font-semibold">
              {normalizePatient(patient, patientId).name}
            </span>
          </p>
          <p className="text-sm font-mono bg-gray-50 p-2 rounded">
            Session Path: <span className="font-bold text-blue-600">{sessionPath || "—"}</span>
          </p>
          {activeSessionId && (
            <p className="text-xs text-gray-500">
              Session ID: <span className="font-mono">{activeSessionId}</span>
            </p>
          )}
        </div>
        <p className="text-sm text-gray-500 mt-3">
          Start recording to capture doctor-patient conversation. Audio will be transcribed using AI.
        </p>
      </header>

      {/* Recording Controls */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex flex-wrap items-center gap-3 mb-4">
          <button
            onClick={handleStartRecording}
            disabled={isRecording || isStarting || !activeSessionId || isTranscribing}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            <Mic size={18} />
            {isStarting ? "Starting..." : "Start Recording"}
          </button>

          <button
            onClick={handleStopRecording}
            disabled={!isRecording}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-red-600 text-white text-sm font-semibold hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            <MicOff size={18} />
            Stop Recording
          </button>

          <span
            className={`text-sm font-medium px-3 py-1 rounded-full border flex items-center gap-2 ${
              isRecording
                ? "bg-red-50 text-red-700 border-red-200"
                : "bg-gray-50 text-gray-600 border-gray-200"
            }`}
          >
            <Clock size={14} />
            {isRecording ? "Recording in progress" : "Idle"}
          </span>

          {recordingDuration > 0 && (
            <span className="text-sm text-gray-600 font-mono">
              {Math.floor(recordingDuration / 60)}:{(recordingDuration % 60).toString().padStart(2, "0")}
            </span>
          )}
        </div>

        {isTranscribing && (
          <div className="mt-4 p-3 bg-amber-50 border-l-4 border-amber-500 text-amber-700 rounded flex items-center gap-2">
            <Loader2 size={16} className="animate-spin" />
            <span>Processing audio with AI transcription...</span>
          </div>
        )}

        {error ? (
          <div className="mt-4 p-3 bg-yellow-50 border-l-4 border-yellow-500 text-yellow-700 rounded">
            {error}
          </div>
        ) : null}

        {audioUrl ? (
          <div className="mt-4">
            <p className="text-sm font-medium text-gray-700 mb-2">
              Latest Recording
            </p>
            <audio controls src={audioUrl} className="w-full" />
          </div>
        ) : null}
      </section>

      {/* Transcript Display */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <BotMessageSquare size={20} className="text-blue-600" />
          Consultation Transcript
          {messages.length > 0 && (
            <span className="ml-auto text-xs font-normal text-green-600 flex items-center gap-1">
              <CheckCircle size={14} />
              {messages.length} segments
            </span>
          )}
        </h2>

        <div className="h-96 overflow-y-auto rounded-lg border border-gray-200 p-4 bg-gray-50 space-y-3">
          {messages.length === 0 && !interimText ? (
            <div className="text-sm text-gray-500 italic">
              Transcript will appear here from Whisper AI as recording chunks are processed.
            </div>
          ) : null}

          {messages.map((message) => (
            <div key={message.id} className="flex gap-2">
              <div
                className={`max-w-[80%] rounded-xl px-3 py-2 text-sm shadow-sm ${
                  message.source === "ai-whisper"
                    ? "bg-blue-50 border border-blue-200 text-blue-900"
                    : "bg-white border border-gray-200 text-gray-800"
                }`}
              >
                <p className="text-xs font-semibold text-gray-500 mb-1">
                  {message.speaker} {message.source === "ai-whisper" && "📋"}
                </p>
                <p>{message.text}</p>
                {message.start !== undefined && (
                  <p className="text-xs text-gray-400 mt-1">
                    {message.start.toFixed(1)}s - {message.end?.toFixed(1)}s
                  </p>
                )}
              </div>
            </div>
          ))}

          {interimText ? (
            <div className="flex gap-2">
              <div className="max-w-[80%] rounded-xl px-3 py-2 bg-blue-50 border border-blue-200 text-blue-800 text-sm italic inline-flex items-center gap-2">
                <AudioLines size={14} className="animate-pulse" />
                {interimText}
              </div>
            </div>
          ) : null}
        </div>

        <div className="mt-4 flex justify-end gap-3">
          <button
            onClick={handleEndConsultation}
            disabled={isEnding || !activeSessionId}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-red-600 text-white font-semibold hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isEnding ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Ending...
              </>
            ) : (
              <>
                <X size={18} />
                End Consultation
              </>
            )}
          </button>
          <button
            onClick={() =>
              navigate(
                `/doctors-dashboard/soap/${patientId}/${activeSessionId}`,
                {
                  state: {
                    patient,
                    transcript: messages,
                  },
                },
              )
            }
            disabled={messages.length === 0}
            className="px-5 py-2.5 rounded-lg bg-emerald-600 text-white font-semibold hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Generate SOAP
          </button>
        </div>
      </section>
    </div>
  );
};

export default RecordingSession;
