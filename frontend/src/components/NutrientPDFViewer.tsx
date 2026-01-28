/**
 * NutrientPDFViewer Component
 * Professional PDF viewer with built-in editing using Nutrient Web SDK
 */

import React, { useEffect, useRef } from 'react';

// PSPDFKit (Nutrient) will be loaded dynamically
declare const PSPDFKit: any;

interface NutrientPDFViewerProps {
  file: File | string;
  onPDFExport?: (pdfBlob: Blob) => void;
  showExportButton?: boolean;
}

export const NutrientPDFViewer: React.FC<NutrientPDFViewerProps> = ({
  file,
  onPDFExport,
  showExportButton = true,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const instanceRef = useRef<any>(null);
  const [isExporting, setIsExporting] = React.useState(false);
  const [isViewerReady, setIsViewerReady] = React.useState(false);

  useEffect(() => {
    const loadPSPDFKit = async () => {
      if (!containerRef.current) return;

      // Reset viewer ready state when loading new file
      setIsViewerReady(false);

      try {
        // Dynamically import PSPDFKit
        const PSPDFKit = (await import('pspdfkit')).default;

        // Unload previous instance if exists
        if (instanceRef.current) {
          await PSPDFKit.unload(instanceRef.current);
          instanceRef.current = null;
        }

        // Convert File to ArrayBuffer or use URL string
        let document: ArrayBuffer | string;
        if (file instanceof File) {
          document = await file.arrayBuffer();
        } else {
          document = file;
        }

        // Load PSPDFKit instance
        const instance = await PSPDFKit.load({
          container: containerRef.current,
          document: document,
          baseUrl: `${window.location.protocol}//${window.location.host}/`,

          // Toolbar configuration
          toolbarItems: [
            { type: 'sidebar-thumbnails' },
            { type: 'sidebar-document-outline' },
            { type: 'pager' },
            { type: 'zoom-out' },
            { type: 'zoom-in' },
            { type: 'spacer' },
            { type: 'search' },
            { type: 'print' },
            { type: 'export-pdf' },
          ],

          // Disable automatic license validation (demo mode)
          licenseKey: undefined,
        });

        instanceRef.current = instance;
        setIsViewerReady(true);

        console.log('✓ Nutrient PDF Viewer loaded successfully');

        // Listen for text selection events
        instance.addEventListener('textSelection.change', (textSelection: any) => {
          if (textSelection) {
            console.log('Text selected:', textSelection.text);
          }
        });

        // Listen for annotation changes (for tracking edits)
        instance.addEventListener('annotations.create', (annotations: any) => {
          console.log('Annotation created:', annotations);
        });

      } catch (error) {
        console.error('Failed to load Nutrient PDF Viewer:', error);
      }
    };

    loadPSPDFKit();

    // Cleanup on unmount
    return () => {
      const cleanup = async () => {
        if (instanceRef.current) {
          const PSPDFKit = (await import('pspdfkit')).default;
          await PSPDFKit.unload(instanceRef.current);
          instanceRef.current = null;
        }
      };
      cleanup();
    };
  }, [file]);

  // Function to export edited PDF
  const handleExportPDF = async () => {
    if (!instanceRef.current) {
      alert('PDF viewer not loaded');
      return;
    }

    setIsExporting(true);
    try {
      // Export the current PDF with all edits/annotations
      const arrayBuffer = await instanceRef.current.exportPDF();
      const blob = new Blob([arrayBuffer], { type: 'application/pdf' });

      // Call the callback with the exported blob
      if (onPDFExport) {
        onPDFExport(blob);
      }

      console.log('✓ PDF exported successfully');
    } catch (error) {
      console.error('Failed to export PDF:', error);
      alert('Failed to export PDF. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="w-full h-full">
      {/* Export Button */}
      {showExportButton && onPDFExport && (
        <div className="mb-4 flex justify-end">
          <button
            onClick={handleExportPDF}
            disabled={isExporting || !isViewerReady}
            className={`
              px-4 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2
              ${
                isExporting || !isViewerReady
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-500 text-white hover:bg-blue-600'
              }
            `}
          >
            {isExporting ? (
              <>
                <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span>Exporting...</span>
              </>
            ) : (
              <>
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                </svg>
                <span>Save Edits</span>
              </>
            )}
          </button>
        </div>
      )}

      <div
        ref={containerRef}
        className="w-full rounded-lg overflow-hidden shadow-lg"
        style={{ height: '600px' }}
      />

      {/* Instructions */}
      <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-start space-x-2">
          <svg className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
              clipRule="evenodd"
            />
          </svg>
          <div className="text-sm text-blue-800">
            <p className="font-medium">Nutrient PDF Viewer (Demo Mode)</p>
            <ul className="mt-2 space-y-1 list-disc list-inside text-xs">
              <li>Select text to copy or search</li>
              <li>Use the toolbar for zoom, navigation, and search</li>
              <li>For text editing: Note down changes manually before translation</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
