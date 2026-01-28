/**
 * Main App Component
 * Orchestrates the complete PDF translation workflow
 */

import { useState } from 'react';
import { FileUpload } from './components/FileUpload';
import { NutrientPDFViewer } from './components/NutrientPDFViewer';
import { TranslationControls } from './components/TranslationControls';
import {
  uploadPDF,
  translatePDF,
  downloadPDF,
  getPDFViewUrl,
  updatePDF,
} from './services/api';

type ViewType = 'upload' | 'original' | 'translated';

function App() {
  // Session state
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [originalFile, setOriginalFile] = useState<File | null>(null);
  const [originalFilename, setOriginalFilename] = useState<string>('');

  // PDF viewing state
  const [currentView, setCurrentView] = useState<ViewType>('upload');
  const [translatedPdfUrl, setTranslatedPdfUrl] = useState<string | null>(null);

  // Loading states
  const [isUploading, setIsUploading] = useState(false);
  const [isTranslating, setIsTranslating] = useState(false);

  // Edit tracking
  const [hasEdits, setHasEdits] = useState(false);

  /**
   * Handle PDF export from Nutrient (after editing)
   */
  const handlePDFExport = async (pdfBlob: Blob) => {
    if (!sessionId) {
      alert('No session found');
      return;
    }

    try {
      await updatePDF(sessionId, pdfBlob);
      setHasEdits(true);
      alert('✓ Edits saved! The edited PDF will be used for translation.');
    } catch (error) {
      console.error('Failed to save edits:', error);
      alert('Failed to save edits. Please try again.');
    }
  };

  /**
   * Handle PDF file upload
   */
  const handleFileUpload = async (file: File) => {
    setIsUploading(true);

    try {
      // Upload PDF to backend
      const response = await uploadPDF(file);
      setSessionId(response.session_id);
      setOriginalFile(file);
      setOriginalFilename(response.filename);

      setCurrentView('original');
    } catch (error) {
      console.error('Upload error:', error);
      alert(`Failed to upload PDF: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsUploading(false);
    }
  };

  /**
   * Handle PDF translation
   */
  const handleTranslate = async (sourceLanguage: string, targetLanguage: string) => {
    if (!sessionId) {
      alert('No session found. Please upload a PDF first.');
      return;
    }

    setIsTranslating(true);

    try {
      const response = await translatePDF(sessionId, {
        source_lang: sourceLanguage,
        target_lang: targetLanguage,
      });

      if (response.success && response.pdf_url) {
        // Create full URL for viewing translated PDF
        const fullUrl = getPDFViewUrl(sessionId, 'translated');
        setTranslatedPdfUrl(fullUrl);
        setCurrentView('translated');
      } else {
        throw new Error(response.error || 'Translation failed');
      }
    } catch (error) {
      console.error('Translation error:', error);
      alert(`Translation failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsTranslating(false);
    }
  };

  /**
   * Handle PDF download
   */
  const handleDownload = async (pdfType: 'original' | 'translated') => {
    if (!sessionId) {
      alert('No session found.');
      return;
    }

    try {
      await downloadPDF(sessionId, pdfType);
    } catch (error) {
      console.error('Download error:', error);
      alert(`Download failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  /**
   * Reset to upload a new file
   */
  const handleReset = () => {
    setSessionId(null);
    setOriginalFile(null);
    setOriginalFilename('');
    setCurrentView('upload');
    setTranslatedPdfUrl(null);
    setHasEdits(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <header className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            PDF Translation System
          </h1>
          <p className="text-lg text-gray-600">
            with <span className="font-semibold text-blue-600">Layout Preservation</span>
          </p>
          <p className="text-sm text-gray-500 mt-2">
            Powered by Apryse XLIFF Reflow + DeepL Translation
          </p>
        </header>

        {/* Upload View */}
        {currentView === 'upload' && (
          <div className="max-w-2xl mx-auto">
            <FileUpload onFileUpload={handleFileUpload} isUploading={isUploading} />
          </div>
        )}

        {/* Original PDF View */}
        {currentView === 'original' && originalFile && (
          <div className="space-y-6">
            {/* Translation Controls */}
            <TranslationControls
              onTranslate={handleTranslate}
              isTranslating={isTranslating}
              disabled={false}
            />

            {/* PDF Viewer */}
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h2 className="text-2xl font-semibold text-gray-800">Original PDF</h2>
                  <p className="text-sm text-gray-500 mt-1">{originalFilename}</p>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleDownload('original')}
                    className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors flex items-center space-x-2"
                  >
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                      />
                    </svg>
                    <span>Download</span>
                  </button>
                  <button
                    onClick={handleReset}
                    className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                  >
                    New Upload
                  </button>
                </div>
              </div>

              <NutrientPDFViewer
                file={originalFile}
                onPDFExport={handlePDFExport}
                showExportButton={true}
              />

              {/* Edit status indicator */}
              {hasEdits && (
                <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <svg className="h-5 w-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <p className="text-sm text-green-800">
                      <span className="font-medium">Edits saved!</span> The edited PDF will be used for translation.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Translated PDF View */}
        {currentView === 'translated' && sessionId && translatedPdfUrl && (
          <div className="space-y-6">
            {/* Navigation */}
            <div className="flex space-x-4">
              <button
                onClick={() => setCurrentView('original')}
                className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors flex items-center space-x-2"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10 19l-7-7m0 0l7-7m-7 7h18"
                  />
                </svg>
                <span>Back to Original</span>
              </button>
              <button
                onClick={handleReset}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                Translate Another PDF
              </button>
            </div>

            {/* Translated PDF Viewer */}
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h2 className="text-2xl font-semibold text-gray-800">Translated PDF</h2>
                  <p className="text-sm text-gray-500 mt-1">{originalFilename} (Translated)</p>
                </div>
                <button
                  onClick={() => handleDownload('translated')}
                  className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors flex items-center space-x-2 font-medium"
                >
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                    />
                  </svg>
                  <span>Download Translated PDF</span>
                </button>
              </div>

              <NutrientPDFViewer file={translatedPdfUrl} showExportButton={false} />

              {/* Success Message */}
              <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center space-x-2">
                  <svg className="h-6 w-6 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <div>
                    <p className="text-sm font-medium text-green-800">
                      Translation completed successfully!
                    </p>
                    <p className="text-xs text-green-700 mt-1">
                      The layout, fonts, and formatting have been preserved using Apryse XLIFF
                      Reflow technology.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
