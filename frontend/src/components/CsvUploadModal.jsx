import { useState, useRef, useCallback } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { Upload, FileSpreadsheet, CheckCircle2, AlertCircle, X, Loader2 } from 'lucide-react';
import api from '../services/api';

export default function CsvUploadModal() {
  const [open, setOpen] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
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
    if (droppedFile) {
      const ext = droppedFile.name.toLowerCase();
      if (ext.endsWith('.xlsx') || ext.endsWith('.xls')) {
        handleFile(droppedFile);
      } else {
        setError('Please drop an Excel file (.xlsx or .xls)');
      }
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
      const response = await api.previewBankTransactions(selectedFile);
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
      const response = await api.uploadBankTransactions(file);
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
      handleClear();
    }
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: 'GBP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(num);
  };

  return (
    <Dialog.Root open={open} onOpenChange={handleOpenChange}>
      <Dialog.Trigger asChild>
        <button
          className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-zinc-700 bg-white border border-zinc-300 rounded-md hover:bg-zinc-50 transition-colors dark:bg-zinc-800 dark:text-zinc-200 dark:border-zinc-700 dark:hover:bg-zinc-700"
          title="Import bank transactions from Excel"
        >
          <Upload className="h-4 w-4" />
          Import Excel
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 z-40 backdrop-blur-sm" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white dark:bg-zinc-900 rounded-xl shadow-2xl z-50 w-full max-w-2xl max-h-[85vh] overflow-y-auto">
          <div className="p-6">
            <div className="flex items-start gap-4 mb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-100 dark:bg-indigo-900/30">
                <FileSpreadsheet className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
              </div>
              <div>
                <Dialog.Title className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                  Import Bank Transactions
                </Dialog.Title>
                <Dialog.Description className="text-sm text-zinc-500 dark:text-zinc-400 mt-1">
                  Upload your Xero Account Transactions export (Excel format) to import historical cash flow data.
                </Dialog.Description>
              </div>
            </div>

            {/* Instructions */}
            <div className="mb-4 p-3 bg-zinc-50 dark:bg-zinc-800/50 rounded-lg text-sm">
              <p className="font-medium text-zinc-700 dark:text-zinc-300 mb-1">How to export from Xero:</p>
              <ol className="list-decimal list-inside text-zinc-600 dark:text-zinc-400 space-y-0.5">
                <li>Go to Accounting → Bank Accounts → Select Account</li>
                <li>Click Account Transactions</li>
                <li>Set date range (e.g., Dec 2020 - Dec 2025)</li>
                <li>Click Export → Export All to Excel</li>
              </ol>
            </div>

            {/* Drop Zone */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`
                border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all
                ${isDragging
                  ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                  : 'border-zinc-300 dark:border-zinc-700 hover:border-zinc-400 dark:hover:border-zinc-600 hover:bg-zinc-50 dark:hover:bg-zinc-800/50'
                }
              `}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileSelect}
                className="hidden"
              />
              <Upload className="mx-auto h-10 w-10 text-zinc-400 dark:text-zinc-500" />
              <p className="mt-3 text-sm text-zinc-600 dark:text-zinc-400">
                <span className="font-medium text-indigo-600 dark:text-indigo-400">Click to upload</span> or drag and drop
              </p>
              <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-500">Excel files only (.xlsx, .xls) - Max 10MB</p>
            </div>

            {/* Error Display */}
            {error && (
              <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
              </div>
            )}

            {/* Preview */}
            {preview && (
              <div className="mt-4 border border-zinc-200 dark:border-zinc-700 rounded-lg overflow-hidden">
                <div className="bg-zinc-50 dark:bg-zinc-800 px-4 py-3 border-b border-zinc-200 dark:border-zinc-700">
                  <h4 className="font-medium text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                    <FileSpreadsheet className="h-4 w-4" />
                    {file?.name}
                  </h4>
                </div>
                <div className="p-4 space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="p-3 bg-zinc-50 dark:bg-zinc-800/50 rounded-lg">
                      <span className="text-zinc-500 dark:text-zinc-400 block text-xs">Transactions</span>
                      <span className="font-semibold text-zinc-900 dark:text-zinc-100 text-lg">{preview.transaction_rows?.toLocaleString()}</span>
                    </div>
                    <div className="p-3 bg-zinc-50 dark:bg-zinc-800/50 rounded-lg">
                      <span className="text-zinc-500 dark:text-zinc-400 block text-xs">Bank Accounts</span>
                      <span className="font-semibold text-zinc-900 dark:text-zinc-100 text-lg">{preview.accounts?.length || 0}</span>
                    </div>
                  </div>

                  {preview.date_range && (
                    <div className="text-sm text-zinc-600 dark:text-zinc-400">
                      Date range: <span className="font-medium">{preview.date_range.earliest}</span> to <span className="font-medium">{preview.date_range.latest}</span>
                    </div>
                  )}

                  {preview.accounts?.length > 0 && (
                    <div>
                      <h5 className="text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wide mb-2">Bank Accounts Found</h5>
                      <div className="flex flex-wrap gap-2">
                        {preview.accounts.map((account, i) => (
                          <span key={i} className="px-2 py-1 text-xs bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 rounded">
                            {account}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {preview.sample_rows?.length > 0 && (
                    <div>
                      <h5 className="text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wide mb-2">Sample Transactions</h5>
                      <div className="overflow-x-auto">
                        <table className="min-w-full text-xs">
                          <thead className="bg-zinc-50 dark:bg-zinc-800">
                            <tr>
                              <th className="px-2 py-1.5 text-left font-medium text-zinc-600 dark:text-zinc-400">Date</th>
                              <th className="px-2 py-1.5 text-left font-medium text-zinc-600 dark:text-zinc-400">Type</th>
                              <th className="px-2 py-1.5 text-left font-medium text-zinc-600 dark:text-zinc-400">Description</th>
                              <th className="px-2 py-1.5 text-right font-medium text-zinc-600 dark:text-zinc-400">In</th>
                              <th className="px-2 py-1.5 text-right font-medium text-zinc-600 dark:text-zinc-400">Out</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
                            {preview.sample_rows.map((row, i) => (
                              <tr key={i}>
                                <td className="px-2 py-1.5 font-mono text-zinc-700 dark:text-zinc-300">{row.date}</td>
                                <td className="px-2 py-1.5 text-zinc-600 dark:text-zinc-400">{row.source}</td>
                                <td className="px-2 py-1.5 truncate max-w-[200px] text-zinc-700 dark:text-zinc-300">{row.description}</td>
                                <td className="px-2 py-1.5 text-right text-emerald-600 dark:text-emerald-400">
                                  {row.debit_gbp > 0 ? formatNumber(row.debit_gbp) : '-'}
                                </td>
                                <td className="px-2 py-1.5 text-right text-red-600 dark:text-red-400">
                                  {row.credit_gbp > 0 ? formatNumber(row.credit_gbp) : '-'}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  <div className="flex gap-3 pt-2 border-t border-zinc-200 dark:border-zinc-700">
                    <button
                      onClick={handleImport}
                      disabled={importing}
                      className={`
                        flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-white font-medium transition-all
                        ${importing
                          ? 'bg-zinc-400 dark:bg-zinc-600 cursor-not-allowed'
                          : 'bg-indigo-600 hover:bg-indigo-700'
                        }
                      `}
                    >
                      {importing ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          Importing...
                        </>
                      ) : (
                        <>
                          <Upload className="h-4 w-4" />
                          Import {preview.transaction_rows?.toLocaleString()} Transactions
                        </>
                      )}
                    </button>
                    <button
                      onClick={handleClear}
                      className="px-4 py-2.5 border border-zinc-300 dark:border-zinc-600 rounded-lg text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Import Result */}
            {result && (
              <div className="mt-4 p-4 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg">
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="h-6 w-6 text-emerald-500 flex-shrink-0" />
                  <div className="flex-1">
                    <h4 className="font-semibold text-emerald-800 dark:text-emerald-200 mb-2">Import Complete!</h4>
                    <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm text-emerald-700 dark:text-emerald-300">
                      <div>Transactions imported: <span className="font-semibold">{result.stats?.transactions_created?.toLocaleString()}</span></div>
                      <div>Bank accounts: <span className="font-semibold">{result.stats?.accounts_found?.length}</span></div>
                      <div>Monthly snapshots: <span className="font-semibold">{result.stats?.snapshots_calculated}</span></div>
                      {result.stats?.date_range && (
                        <div>Date range: <span className="font-semibold">{result.stats.date_range.earliest} to {result.stats.date_range.latest}</span></div>
                      )}
                    </div>
                    {result.stats?.accounts_found?.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-emerald-200 dark:border-emerald-700">
                        <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400">Accounts:</span>
                        <p className="text-sm text-emerald-700 dark:text-emerald-300 mt-1">
                          {result.stats.accounts_found.join(', ')}
                        </p>
                      </div>
                    )}
                    <button
                      onClick={() => {
                        setOpen(false);
                        window.location.reload(); // Refresh to see new data
                      }}
                      className="mt-4 w-full px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors font-medium"
                    >
                      Done - Refresh Dashboard
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Close button */}
          <Dialog.Close asChild>
            <button
              className="absolute top-4 right-4 p-1 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300 rounded-full hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
              aria-label="Close"
            >
              <X className="h-5 w-5" />
            </button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
