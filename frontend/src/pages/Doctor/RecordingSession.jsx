import React, { useMemo, useRef, useState } from "react";
import { Mic, MicOff, BotMessageSquare, AudioLines } from "lucide-react";
import { useLocation, useNavigate, useParams } from "react-router-dom";

const RecordingSession = () => {
  const navigate = useNavigate();
  const { patientId, sessionId } = useParams();
  const location = useLocation();

  const patient = location.state?.patient || {
    patientId,
    sessionId,
    name: "Selected Patient",
    age: "—",
    sex: "—",
  };

  const [isRecording, setIsRecording] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState("");
  const [interimText, setInterimText] = useState("");
  const [messages, setMessages] = useState([]);
  const [audioUrl, setAudioUrl] = useState("");

  const mediaRecorderRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const speechRecognitionRef = useRef(null);
  const chunksRef = useRef([]);

  const supportsSpeechRecognition = useMemo(() => {
    return Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);
  }, []);

  const stopTracks = () => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
  };

  const handleStartRecording = async () => {
    setError("");
    setIsStarting(true);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      chunksRef.current = [];

      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        if (blob.size > 0) {
          const localAudioUrl = URL.createObjectURL(blob);
          setAudioUrl(localAudioUrl);
        }
      };

      recorder.start();

      if (supportsSpeechRecognition) {
        const SpeechRecognition =
          window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        speechRecognitionRef.current = recognition;

        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = "en-US";

        recognition.onresult = (event) => {
          let liveText = "";

          for (let i = event.resultIndex; i < event.results.length; i += 1) {
            const result = event.results[i];
            const text = result[0]?.transcript?.trim();
            if (!text) continue;

            if (result.isFinal) {
              setMessages((prev) => [
                ...prev,
                {
                  id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
                  text,
                  speaker: "conversation",
                },
              ]);
              setInterimText("");
            } else {
              liveText = `${liveText} ${text}`.trim();
            }
          }

          setInterimText(liveText);
        };

        recognition.onerror = (event) => {
          setError(`Speech-to-text error: ${event.error}`);
        };

        recognition.start();
      } else {
        setError(
          "Real-time speech-to-text is not supported in this browser. Recording still works.",
        );
      }

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

  const handleStopRecording = () => {
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state !== "inactive"
    ) {
      mediaRecorderRef.current.stop();
    }

    if (speechRecognitionRef.current) {
      try {
        speechRecognitionRef.current.stop();
      } catch (_) {
        // no-op
      }
      speechRecognitionRef.current = null;
    }

    stopTracks();
    setIsRecording(false);
    setInterimText("");
  };

  return (
    <div className="flex flex-col flex-1 p-4 overflow-auto gap-6">
      <header className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-800">
          Recording Session
        </h1>
        <div className="text-gray-600 mt-1 space-y-1">
          <p>
            Patient: <span className="font-semibold">{patient?.name}</span>
          </p>
          <p className="text-sm">
            Patient ID:{" "}
            <span className="font-mono">
              {patient?.patientId || patientId || "N/A"}
            </span>
            <span className="mx-2">•</span>
            Session ID:{" "}
            <span className="font-mono">
              {patient?.sessionId || sessionId || "N/A"}
            </span>
          </p>
        </div>
        <p className="text-sm text-gray-500 mt-2">
          Start recording to capture doctor-patient conversation and live
          speech-to-text.
        </p>
      </header>

      <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handleStartRecording}
            disabled={isRecording || isStarting}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Mic size={18} />
            {isStarting ? "Starting..." : "Start Recording"}
          </button>

          <button
            onClick={handleStopRecording}
            disabled={!isRecording}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-red-600 text-white text-sm font-semibold hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <MicOff size={18} />
            Stop Recording
          </button>

          <span
            className={`text-sm font-medium px-3 py-1 rounded-full border ${
              isRecording
                ? "bg-red-50 text-red-700 border-red-200"
                : "bg-gray-50 text-gray-600 border-gray-200"
            }`}
          >
            {isRecording ? "Recording in progress" : "Idle"}
          </span>
        </div>

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

      <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <BotMessageSquare size={20} className="text-blue-600" />
          Real-time Speech to Text
        </h2>

        <div className="h-[340px] overflow-y-auto rounded-lg border border-gray-200 p-4 bg-gray-50 space-y-3">
          {messages.length === 0 && !interimText ? (
            <div className="text-sm text-gray-500">
              Transcript will appear here as a chat-style conversation.
            </div>
          ) : null}

          {messages.map((message) => (
            <div key={message.id} className="flex justify-start">
              <div className="max-w-[90%] rounded-xl px-3 py-2 bg-white border border-gray-200 text-gray-800 text-sm shadow-sm">
                {message.text}
              </div>
            </div>
          ))}

          {interimText ? (
            <div className="flex justify-start opacity-80">
              <div className="max-w-[90%] rounded-xl px-3 py-2 bg-blue-50 border border-blue-200 text-blue-800 text-sm italic inline-flex items-center gap-2">
                <AudioLines size={14} />
                {interimText}
              </div>
            </div>
          ) : null}
        </div>

        <div className="mt-4 flex justify-end">
          <button
            onClick={() =>
              navigate(
                `/doctors-dashboard/soap/${patient?.patientId || patientId}/${patient?.sessionId || sessionId}`,
                {
                  state: {
                    patient,
                    transcript: messages,
                  },
                },
              )
            }
            className="px-5 py-2.5 rounded-lg bg-emerald-600 text-white font-semibold hover:bg-emerald-700 transition-colors"
          >
            Check SOAP
          </button>
        </div>
      </section>
    </div>
  );
};

export default RecordingSession;
