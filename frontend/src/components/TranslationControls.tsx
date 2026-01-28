/**
 * TranslationControls Component
 * Language selection and translation trigger controls
 */

import React, { useState } from 'react';
import { SUPPORTED_LANGUAGES } from '../types';

interface TranslationControlsProps {
  onTranslate: (sourceLanguage: string, targetLanguage: string) => void;
  isTranslating: boolean;
  disabled: boolean;
  editedSegmentsCount?: number;
}

export const TranslationControls: React.FC<TranslationControlsProps> = ({
  onTranslate,
  isTranslating,
  disabled,
  editedSegmentsCount = 0,
}) => {
  const [sourceLanguage, setSourceLanguage] = useState('EN');
  const [targetLanguage, setTargetLanguage] = useState('ES');

  const handleTranslate = () => {
    if (sourceLanguage !== targetLanguage) {
      onTranslate(sourceLanguage, targetLanguage);
    }
  };

  const isButtonDisabled = disabled || isTranslating || sourceLanguage === targetLanguage;

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-800">Translation Settings</h2>
        {editedSegmentsCount > 0 && (
          <span className="px-3 py-1 bg-yellow-100 text-yellow-800 text-sm rounded-full">
            {editedSegmentsCount} edit{editedSegmentsCount !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      {/* Language Selection */}
      <div className="flex items-center space-x-4">
        {/* Source Language */}
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Source Language
          </label>
          <select
            value={sourceLanguage}
            onChange={(e) => setSourceLanguage(e.target.value)}
            disabled={disabled || isTranslating}
            className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            {SUPPORTED_LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.name}
              </option>
            ))}
          </select>
        </div>

        {/* Arrow Icon */}
        <div className="pt-6">
          <svg
            className="h-8 w-8 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M14 5l7 7m0 0l-7 7m7-7H3"
            />
          </svg>
        </div>

        {/* Target Language */}
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Target Language
          </label>
          <select
            value={targetLanguage}
            onChange={(e) => setTargetLanguage(e.target.value)}
            disabled={disabled || isTranslating}
            className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            {SUPPORTED_LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Warning if same language */}
      {sourceLanguage === targetLanguage && (
        <div className="flex items-center space-x-2 text-amber-600 text-sm bg-amber-50 p-3 rounded">
          <svg className="h-5 w-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
          <span>Source and target languages must be different</span>
        </div>
      )}

      {/* Translate Button */}
      <button
        onClick={handleTranslate}
        disabled={isButtonDisabled}
        className={`
          w-full py-3 px-6 rounded-lg font-medium text-white transition-all duration-200
          flex items-center justify-center space-x-2
          ${
            isButtonDisabled
              ? 'bg-gray-300 cursor-not-allowed'
              : 'bg-blue-500 hover:bg-blue-600 hover:shadow-lg transform hover:scale-105'
          }
        `}
      >
        {isTranslating ? (
          <>
            <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <span>Translating...</span>
          </>
        ) : (
          <>
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"
              />
            </svg>
            <span>Translate PDF</span>
          </>
        )}
      </button>

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800">
        <div className="flex items-start space-x-2">
          <svg className="h-5 w-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
              clipRule="evenodd"
            />
          </svg>
          <div>
            <p className="font-medium">Layout Preservation</p>
            <p className="text-xs mt-1">
              This system uses Apryse XLIFF Reflow technology to maintain the original PDF layout,
              fonts, and formatting after translation.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
