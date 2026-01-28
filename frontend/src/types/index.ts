/**
 * TypeScript types and interfaces for the PDF Translation System
 */

export interface TextSegment {
  text: string;
  page: number;
  x0: number;
  y0: number;
  x1: number;
  y1: number;
  segment_id?: string;
  isEdited?: boolean;
  editedText?: string;
}

export interface UploadResponse {
  session_id: string;
  filename: string;
  message: string;
}

export interface ExtractTextResponse {
  segments: TextSegment[];
  total_segments: number;
}

export interface TranslationRequest {
  source_lang: string;
  target_lang: string;
  manual_edits?: Record<string, string>;
}

export interface TranslationResponse {
  success: boolean;
  message: string;
  pdf_url?: string;
  error?: string;
}

export interface AppState {
  sessionId: string | null;
  originalFile: File | null;
  originalFilename: string | null;
  translatedPdfUrl: string | null;
  textSegments: TextSegment[];
  editedSegments: Record<string, string>;
  isUploading: boolean;
  isTranslating: boolean;
  translationProgress: number;
  currentView: 'upload' | 'original' | 'translated';
  sourceLanguage: string;
  targetLanguage: string;
}

export interface Language {
  code: string;
  name: string;
}

export const SUPPORTED_LANGUAGES: Language[] = [
  { code: 'EN', name: 'English' },
  { code: 'ES', name: 'Spanish' },
  { code: 'FR', name: 'French' },
  { code: 'DE', name: 'German' },
  { code: 'IT', name: 'Italian' },
  { code: 'PT', name: 'Portuguese' },
  { code: 'ZH', name: 'Chinese' },
  { code: 'JA', name: 'Japanese' },
  { code: 'KO', name: 'Korean' },
  { code: 'RU', name: 'Russian' },
  { code: 'AR', name: 'Arabic' },
  { code: 'NL', name: 'Dutch' },
  { code: 'PL', name: 'Polish' },
];
