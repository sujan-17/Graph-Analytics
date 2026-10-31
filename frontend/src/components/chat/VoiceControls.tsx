import React, { useState, useRef } from 'react';
import { Mic, Square, X } from 'lucide-react';
import { voiceService } from '../../services/voice';

interface VoiceControlsProps {
  onTranscribedText: (text: string, autoSubmit?: boolean) => void;
  isAnalyzing?: boolean;
}

export const VoiceControls: React.FC<VoiceControlsProps> = ({
  onTranscribedText,
  isAnalyzing = false,
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [interimText, setInterimText] = useState('');
  const [latencyMs, setLatencyMs] = useState<number | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);
  const speechRecognitionRef = useRef<any>(null);
  const spokenTextRef = useRef<string>('');

  // Start Voice Recording
  const startRecording = async () => {
    if (isRecording || isAnalyzing) return;
    setInterimText('');
    setLatencyMs(null);
    spokenTextRef.current = '';
    audioChunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      // Browser Web Speech interim preview (instant feedback while speaking)
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        try {
          const recognition = new SpeechRecognition();
          recognition.continuous = true;
          recognition.interimResults = true;
          recognition.lang = 'en-US';

          recognition.onresult = (event: any) => {
            let fullTranscript = '';
            for (let i = 0; i < event.results.length; ++i) {
              fullTranscript += event.results[i][0].transcript + ' ';
            }
            fullTranscript = fullTranscript.trim();
            if (fullTranscript) {
              spokenTextRef.current = fullTranscript;
              setInterimText(fullTranscript);
              // Live update into the input box so the user sees their speech!
              onTranscribedText(fullTranscript, false);
            }
          };

          recognition.onerror = (e: any) => {
            console.warn('[VoiceControls] WebSpeech error:', e);
          };

          recognition.start();
          speechRecognitionRef.current = recognition;
        } catch (e) {
          console.warn('[VoiceControls] SpeechRecognition not initialized:', e);
        }
      }

      // MediaRecorder captures raw audio blob for open-source Whisper transcription
      let mimeType = 'audio/webm;codecs=opus';
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = MediaRecorder.isTypeSupported('audio/webm')
          ? 'audio/webm'
          : MediaRecorder.isTypeSupported('audio/mp4')
          ? 'audio/mp4'
          : '';
      }

      const mediaRecorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        // Stop audio tracks
        stream.getTracks().forEach((track) => track.stop());

        // Process audio recording with faster-whisper
        const actualMime = mediaRecorder.mimeType || mimeType || 'audio/webm';
        const audioBlob = new Blob(audioChunksRef.current, { type: actualMime });
        console.log('[VoiceControls] Recording ended. Blob size:', audioBlob.size, 'type:', actualMime);

        setIsTranscribing(true);
        let finalText = '';

        try {
          if (audioBlob.size > 100) {
            const result = await voiceService.transcribeAudio(audioBlob);
            console.log('[VoiceControls] Whisper server response:', result);
            if (result && result.text && result.text.trim()) {
              finalText = result.text.trim();
              setLatencyMs(result.latency_ms);
            }
          }
        } catch (err) {
          console.error('[VoiceControls] Whisper transcription failed, checking fallback:', err);
        } finally {
          // If Whisper didn't return text, use live speech transcript fallback
          if (!finalText && spokenTextRef.current.trim()) {
            finalText = spokenTextRef.current.trim();
            console.log('[VoiceControls] Using live transcript fallback:', finalText);
          }

          setIsTranscribing(false);

          if (finalText) {
            console.log('[VoiceControls] Submitting transcribed question to LLM:', finalText);
            onTranscribedText(finalText, true);
          } else {
            console.warn('[VoiceControls] No speech detected in recording.');
            alert('No speech was detected. Please ensure your microphone is enabled and speak clearly.');
          }
        }
      };

      mediaRecorder.start(200); // 200ms slice
      setIsRecording(true);
      setRecordingSeconds(0);

      timerRef.current = window.setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } catch (err: any) {
      console.error('[VoiceControls] Microphone access error:', err);
      alert('Unable to access microphone. Please check your browser microphone permissions.');
    }
  };

  // Stop Recording & Send Audio to faster-whisper
  const stopRecording = () => {
    if (!isRecording) return;

    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    if (speechRecognitionRef.current) {
      try {
        speechRecognitionRef.current.stop();
      } catch {}
      speechRecognitionRef.current = null;
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try {
        // Request any remaining audio data before stopping
        mediaRecorderRef.current.requestData();
      } catch {}
      mediaRecorderRef.current.stop();
    }

    setIsRecording(false);
  };

  const cancelRecording = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    if (speechRecognitionRef.current) {
      try {
        speechRecognitionRef.current.stop();
      } catch {}
      speechRecognitionRef.current = null;
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      audioChunksRef.current = [];
      mediaRecorderRef.current.stop();
    }

    setIsRecording(false);
    setInterimText('');
    setRecordingSeconds(0);
    spokenTextRef.current = '';
  };

  const formatTimer = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  return (
    <div className="flex items-center gap-2 shrink-0">
      {/* Active Recording Overlay Pill */}
      {isRecording && (
        <div className="flex items-center gap-2.5 bg-rose-50 border border-rose-200 text-rose-700 px-3 py-1.5 rounded-xl text-xs font-semibold animate-pulse shadow-xs">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-600 animate-ping" />
          <span className="font-mono">{formatTimer(recordingSeconds)}</span>
          <span className="truncate max-w-[160px] font-normal text-rose-900">
            {interimText || 'Listening...'}
          </span>
          <button
            type="button"
            onClick={cancelRecording}
            className="text-rose-400 hover:text-rose-700 p-0.5 rounded transition-colors"
            title="Cancel recording"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Whisper Transcribing Spinner */}
      {isTranscribing && (
        <div className="flex items-center gap-2 bg-indigo-50 border border-indigo-200 text-indigo-700 px-3 py-1.5 rounded-xl text-xs font-medium shadow-xs animate-pulse">
          <div className="w-3.5 h-3.5 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
          <span>Transcribing via Whisper...</span>
        </div>
      )}

      {/* STT Latency Badge */}
      {latencyMs !== null && !isRecording && !isTranscribing && (
        <div
          className="hidden md:flex items-center gap-1.5 px-2 py-1 rounded-lg bg-emerald-50 border border-emerald-200 text-[11px] text-emerald-700 font-medium"
          title={`Transcribed in ${latencyMs}ms via open-source faster-whisper`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          <span>Whisper: {latencyMs}ms</span>
        </div>
      )}

      {/* Clean Single Microphone Button */}
      <button
        type="button"
        onClick={isRecording ? stopRecording : startRecording}
        disabled={isAnalyzing || isTranscribing}
        className={`relative p-2.5 rounded-xl flex items-center justify-center transition-all cursor-pointer ${
          isRecording
            ? 'bg-rose-600 hover:bg-rose-700 text-white shadow-lg shadow-rose-600/30 scale-105 ring-4 ring-rose-200'
            : 'bg-slate-100 hover:bg-indigo-50 text-slate-700 hover:text-indigo-600 border border-slate-200 hover:border-indigo-300'
        }`}
        title={isRecording ? 'Click to stop & ask LLM' : 'Ask question with voice (faster-whisper STT)'}
      >
        {isRecording ? (
          <Square className="w-4 h-4 fill-current" />
        ) : (
          <Mic className="w-4 h-4" />
        )}
      </button>
    </div>
  );
};
