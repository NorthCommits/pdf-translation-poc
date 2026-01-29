/**
 * API Service Layer
 * Handles all HTTP requests to the backend FastAPI server
 */

import axios from 'axios';
import {
  UploadResponse,
  ExtractTextResponse,
  TranslationRequest,
  TranslationResponse
} from '../types';

// API Base URL - update this if backend runs on different host/port
const API_BASE_URL = 'http://localhost:8001/api/v1';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Upload a PDF file to the backend
 * @param file - PDF file to upload
 * @returns Upload response with session ID
 */
export const uploadPDF = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post<UploadResponse>('/upload-pdf', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

/**
 * Extract text segments with positions from uploaded PDF
 * @param sessionId - Session ID from upload response
 * @returns Text segments with bounding box coordinates
 */
export const extractText = async (sessionId: string): Promise<ExtractTextResponse> => {
  const response = await api.get<ExtractTextResponse>(`/extract-text/${sessionId}`);
  return response.data;
};

/**
 * Update PDF with edited version
 * @param sessionId - Session ID
 * @param pdfBlob - Edited PDF as Blob
 * @returns Success response
 */
export const updatePDF = async (sessionId: string, pdfBlob: Blob): Promise<any> => {
  const formData = new FormData();
  formData.append('file', pdfBlob, 'edited.pdf');

  const response = await api.post(`/update-pdf/${sessionId}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

/**
 * Translate PDF using DeepL Document Translation API
 * @param sessionId - Session ID
 * @param request - Translation request with languages
 * @returns Translation response with PDF URL
 */
export const translatePDF = async (
  sessionId: string,
  request: TranslationRequest
): Promise<TranslationResponse> => {
  const response = await api.post<TranslationResponse>(
    `/translate/${sessionId}`,
    request
  );
  return response.data;
};

/**
 * Download PDF (original or translated)
 * @param sessionId - Session ID
 * @param pdfType - 'original' or 'translated'
 */
export const downloadPDF = async (
  sessionId: string,
  pdfType: 'original' | 'translated'
): Promise<void> => {
  const response = await api.get(`/download/${sessionId}/${pdfType}`, {
    responseType: 'blob',
  });

  // Create download link and trigger download
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `${pdfType}_document.pdf`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

/**
 * Get URL for viewing PDF in browser
 * @param sessionId - Session ID
 * @param pdfType - 'original' or 'translated'
 * @returns Full URL to PDF
 */
export const getPDFViewUrl = (
  sessionId: string,
  pdfType: 'original' | 'translated'
): string => {
  return `${API_BASE_URL}/download/${sessionId}/${pdfType}`;
};

/**
 * Cleanup session and remove temporary files
 * @param sessionId - Session ID to cleanup
 */
export const cleanupSession = async (sessionId: string): Promise<void> => {
  await api.delete(`/cleanup/${sessionId}`);
};

/**
 * Health check endpoint
 * @returns Health status
 */
export const healthCheck = async (): Promise<any> => {
  const response = await api.get('/health');
  return response.data;
};

// Error handling interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);

    if (error.response) {
      // Server responded with error status
      const errorMessage = error.response.data?.detail || error.response.data?.message || 'An error occurred';
      throw new Error(errorMessage);
    } else if (error.request) {
      // Request made but no response received
      throw new Error('No response from server. Please check if the backend is running.');
    } else {
      // Something else happened
      throw new Error(error.message || 'An unexpected error occurred');
    }
  }
);

export default api;
