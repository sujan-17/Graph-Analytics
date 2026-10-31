import API from './api';

export interface VoiceOption {
  id: string;
  name: string;
  gender: string;
  locale: string;
  engine: string;
  recommended?: boolean;
}

export interface VoiceStatus {
  status: string;
  stt: {
    engine: string;
    model: string;
    compute_type: string;
    device: string;
    vad_enabled: boolean;
  };
  tts: {
    primary_engine: string;
    fallback_engine: string;
    default_voice: string;
    total_voices: number;
  };
}

export interface TranscribeResult {
  text: string;
  duration: number;
  language: string;
  latency_ms: number;
  confidence: number;
  segments?: Array<{ start: number; end: number; text: string }>;
}

// In-memory cache for synthesized audio URLs to prevent repeat network latency
const audioCache = new Map<string, string>();

export const voiceService = {
  /**
   * Transcribe an audio recording using open-source faster-whisper.
   */
  async transcribeAudio(audioBlob: Blob): Promise<TranscribeResult> {
    const formData = new FormData();
    const ext = audioBlob.type.includes('wav') ? 'wav' : 'webm';
    formData.append('file', audioBlob, `recording.${ext}`);

    const res = await API.post<TranscribeResult>('/voice/transcribe', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  /**
   * Synthesize text to spoken audio using low-latency open-source neural TTS.
   * Returns a playback URL (Blob URL).
   */
  async synthesizeSpeech(
    text: string,
    voice: string = 'en-US-ChristopherNeural',
    rate: string = '+0%',
    engine: string = 'auto'
  ): Promise<string> {
    const cacheKey = `${voice}_${rate}_${text.trim()}`;
    if (audioCache.has(cacheKey)) {
      return audioCache.get(cacheKey)!;
    }

    const res = await API.post(
      '/voice/synthesize',
      {
        text,
        voice,
        rate,
        engine,
      },
      {
        responseType: 'blob',
      }
    );

    const contentType = (res.headers['content-type'] as string) || 'audio/mpeg';
    const blob = new Blob([res.data], { type: contentType });
    const url = URL.createObjectURL(blob);
    audioCache.set(cacheKey, url);
    return url;
  },

  /**
   * Fetch list of available open-source voices.
   */
  async getVoices(): Promise<VoiceOption[]> {
    try {
      const res = await API.get<VoiceOption[]>('/voice/voices');
      return res.data;
    } catch {
      return [
        {
          id: 'en-US-ChristopherNeural',
          name: 'Christopher (US Male - Professional Analyst)',
          gender: 'Male',
          locale: 'en-US',
          engine: 'edge-tts',
          recommended: true,
        },
      ];
    }
  },

  /**
   * Get operational status of STT and TTS models.
   */
  async getStatus(): Promise<VoiceStatus> {
    const res = await API.get<VoiceStatus>('/voice/status');
    return res.data;
  },
};
