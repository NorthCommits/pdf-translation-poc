/**
 * PDFViewer Component
 * Renders PDF files using react-pdf with optional text overlay for editing
 */

import React, { useState } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { TextSegment } from '../types';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

interface PDFViewerProps {
  file: File | string;
  textSegments?: TextSegment[];
  onTextClick?: (segment: TextSegment) => void;
  showOverlay?: boolean;
}

export const PDFViewer: React.FC<PDFViewerProps> = ({
  file,
  textSegments,
  onTextClick,
  showOverlay = true,
}) => {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setIsLoading(false);
  };

  const onDocumentLoadError = (error: Error) => {
    console.error('PDF load error:', error);
    setIsLoading(false);
  };

  const goToPreviousPage = () => {
    setPageNumber((prev) => Math.max(1, prev - 1));
  };

  const goToNextPage = () => {
    setPageNumber((prev) => Math.min(numPages, prev + 1));
  };

  return (
    <div className="flex flex-col items-center space-y-4 w-full">
      {/* PDF Document */}
      <div className="relative border border-gray-300 shadow-lg rounded-lg overflow-hidden bg-gray-100">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-90 z-10">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              <p className="mt-2 text-gray-600">Loading PDF...</p>
            </div>
          </div>
        )}

        <Document
          file={file}
          onLoadSuccess={onDocumentLoadSuccess}
          onLoadError={onDocumentLoadError}
          loading={
            <div className="flex items-center justify-center p-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
          }
        >
          <Page
            pageNumber={pageNumber}
            renderTextLayer={true}
            renderAnnotationLayer={true}
            loading={
              <div className="flex items-center justify-center p-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              </div>
            }
          />
        </Document>

        {/* Text overlay for editing - only if textSegments provided and showOverlay is true */}
        {showOverlay && textSegments && textSegments.length > 0 && (
          <div className="absolute inset-0 pointer-events-none">
            {textSegments
              .filter((seg) => seg.page === pageNumber)
              .map((segment, idx) => (
                <div
                  key={idx}
                  className={`
                    absolute cursor-pointer pointer-events-auto
                    transition-all duration-150
                    hover:bg-yellow-200 hover:bg-opacity-40 hover:ring-2 hover:ring-yellow-400
                    ${segment.isEdited ? 'bg-yellow-300 bg-opacity-50 ring-2 ring-yellow-500' : ''}
                  `}
                  style={{
                    left: `${segment.x0}px`,
                    top: `${segment.y0}px`,
                    width: `${segment.x1 - segment.x0}px`,
                    height: `${segment.y1 - segment.y0}px`,
                  }}
                  onClick={() => onTextClick?.(segment)}
                  title={segment.isEdited ? `Edited: ${segment.editedText}` : 'Click to edit'}
                />
              ))}
          </div>
        )}
      </div>

      {/* Page navigation */}
      {numPages > 0 && (
        <div className="flex items-center space-x-4 bg-white px-6 py-3 rounded-lg shadow">
          <button
            onClick={goToPreviousPage}
            disabled={pageNumber <= 1}
            className={`
              px-4 py-2 rounded font-medium transition-colors
              ${
                pageNumber <= 1
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-blue-500 text-white hover:bg-blue-600'
              }
            `}
          >
            Previous
          </button>

          <span className="text-gray-700 font-medium">
            Page <span className="font-bold">{pageNumber}</span> of{' '}
            <span className="font-bold">{numPages}</span>
          </span>

          <button
            onClick={goToNextPage}
            disabled={pageNumber >= numPages}
            className={`
              px-4 py-2 rounded font-medium transition-colors
              ${
                pageNumber >= numPages
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-blue-500 text-white hover:bg-blue-600'
              }
            `}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};
