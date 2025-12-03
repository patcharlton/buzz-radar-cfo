import { useState, useRef, useCallback } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { api } from '../services/api';

export default function CsvUploadModal() {
  const [open, setOpen] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [importType, setImportType] = useState('invoices');
  const fileInputRef = useRef(null);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.name.toLowerCase().endsWith('.csv')) {
      handleFile(droppedFile);
    } else {
      setError('Please drop a CSV file');
    }
  }, []);

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      handleFile(selectedFile);
    }
  };

  const handleFile = async (selectedFile) => {
    setFile(selectedFile);
    setError(null);
    setResult(null);
    setPreview(null);

    try {
      const response = await api.previewCsv(selectedFile);
      if (response.success) {
        setPreview(response.preview);
      } else {
        setError(response.error || 'Failed to preview file');
      }
    } catch (err) {
      setError(err.message || 'Failed to preview file');
    }
  };

  const handleImport = async () => {
    if (!file) return;

    setImporting(true);
    setError(null);

    try {
      const response = await api.uploadCsv(file, importType);
      if (response.success) {
        setResult(response);
        setFile(null);
        setPreview(null);
      } else {
        setError(response.error || 'Import failed');
      }
    } catch (err) {
      setError(err.message || 'Import failed');
    } finally {
      setImporting(false);
    }
  };

  const handleClear = () => {
    setFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleOpenChange = (newOpen) => {
    setOpen(newOpen);
    if (!newOpen) {
      // Reset state when closing
      handleClear();
    }
  };

  return (
    <Dialog.Root open={open} onOpenChange={handleOpenChange}>
      <Dialog.Trigger asChild>
        <button className="btn btn-secondary" title="Import historical data from CSV">
          Import CSV
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 z-40" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-lg shadow-xl z-50 w-full max-w-2xl max-h-[85vh] overflow-y-auto p-6">
          <Dialog.Title className="text-xl font-semibold text-gray-900 mb-2">
            Import Historical Data
          </Dialog.Title>
          <Dialog.Description className="text-sm text-gray-600 mb-4">
            Upload Xero CSV exports to import historical invoice data. Export from Xero via
            Business &rarr; Invoices &rarr; Export.
          </Dialog.Description>

          {/* Import Type Selection */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Import Type
            </label>
            <div className="flex gap-4">
              <label className="flex items-center cursor-pointer">
                <input
                  type="radio"
                  name="importType"
                  value="invoices"
                  checked={importType === 'invoices'}
                  onChange={(e) => setImportType(e.target.value)}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">Sales Invoices (Receivables)</span>
              </label>
              <label className="flex items-center cursor-pointer">
                <input
                  type="radio"
                  name="importType"
                  value="bills"
                  checked={importType === 'bills'}
                  onChange={(e) => setImportType(e.target.value)}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">Bills (Payables)</span>
              </label>
            </div>
          </div>

          {/* Drop Zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`
              border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
              ${isDragging
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
              }
            `}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileSelect}
              className="hidden"
            />
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
            <p className="mt-2 text-sm text-gray-600">
              <span className="font-medium text-blue-600">Click to upload</span> or drag and drop
            </p>
            <p className="mt-1 text-xs text-gray-500">CSV files only (max 10MB)</p>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Preview */}
          {preview && (
            <div className="mt-4 border border-gray-200 rounded-lg overflow-hidden">
              <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                <h4 className="font-medium text-gray-900">Preview: {file?.name}</h4>
              </div>
              <div className="p-4 space-y-3">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Total rows:</span>
                    <span className="ml-2 font-medium">{preview.total_rows}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Unique invoices:</span>
                    <span className="ml-2 font-medium">{preview.unique_invoices}</span>
                  </div>
                  {preview.date_range && (
                    <>
                      <div>
                        <span className="text-gray-500">Earliest date:</span>
                        <span className="ml-2 font-medium">{preview.date_range.earliest}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Latest date:</span>
                        <span className="ml-2 font-medium">{preview.date_range.latest}</span>
                      </div>
                    </>
                  )}
                </div>

                {preview.missing_columns?.length > 0 && (
                  <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                    <p className="text-sm text-yellow-700">
                      Missing columns: {preview.missing_columns.join(', ')}
                    </p>
                  </div>
                )}

                {preview.sample_rows?.length > 0 && (
                  <div>
                    <h5 className="text-sm font-medium text-gray-700 mb-2">Sample data:</h5>
                    <div className="overflow-x-auto">
                      <table className="min-w-full text-xs">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-2 py-1 text-left">Invoice #</th>
                            <th className="px-2 py-1 text-left">Contact</th>
                            <th className="px-2 py-1 text-left">Date</th>
                            <th className="px-2 py-1 text-right">Total</th>
                            <th className="px-2 py-1 text-left">Type</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {preview.sample_rows.map((row, i) => (
                            <tr key={i}>
                              <td className="px-2 py-1 font-mono">{row.invoice_number}</td>
                              <td className="px-2 py-1 truncate max-w-[150px]">{row.contact}</td>
                              <td className="px-2 py-1">{row.date}</td>
                              <td className="px-2 py-1 text-right">{row.total}</td>
                              <td className="px-2 py-1 text-gray-500">{row.type}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                <div className="flex gap-3 pt-2">
                  <button
                    onClick={handleImport}
                    disabled={importing || !preview.is_valid}
                    className={`
                      flex-1 px-4 py-2 rounded-md text-white font-medium transition-colors
                      ${importing || !preview.is_valid
                        ? 'bg-gray-400 cursor-not-allowed'
                        : 'bg-blue-600 hover:bg-blue-700'
                      }
                    `}
                  >
                    {importing ? 'Importing...' : `Import ${preview.unique_invoices} Invoices`}
                  </button>
                  <button
                    onClick={handleClear}
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Import Result */}
          {result && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <h4 className="font-medium text-green-800 mb-2">Import Complete</h4>
              <div className="grid grid-cols-2 gap-2 text-sm text-green-700">
                <div>Invoices created: {result.stats.invoices_created}</div>
                <div>Invoices updated: {result.stats.invoices_updated}</div>
                <div>Line items: {result.stats.line_items_created}</div>
                <div>Credit notes: {result.stats.credit_notes}</div>
              </div>
              {result.stats.errors?.length > 0 && (
                <div className="mt-2 text-sm text-yellow-700">
                  {result.stats.errors.length} warnings/errors during import
                </div>
              )}
              <div className="mt-3 pt-3 border-t border-green-200 text-sm text-green-700">
                <strong>Database totals:</strong> {result.totals.receivables} receivables, {result.totals.payables} payables
              </div>
              <button
                onClick={() => setOpen(false)}
                className="mt-3 w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
              >
                Done
              </button>
            </div>
          )}

          {/* Close button */}
          <Dialog.Close asChild>
            <button
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
              aria-label="Close"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
