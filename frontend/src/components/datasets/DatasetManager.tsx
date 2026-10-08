import React, { useState } from 'react';
import {
  UploadCloud,
  FileText,
  CheckCircle,
  AlertTriangle,
  Search,
  Filter,
  ShieldAlert,
  Sparkles,
  Layers,
  Trash2,
  CheckSquare,
  Square,
  X,
  ArrowRight,
  Database
} from 'lucide-react';
import { Dataset, DatasetProfile } from '../../types';

interface DatasetManagerProps {
  datasets: Dataset[];
  selectedDataset: Dataset | null;
  profile: DatasetProfile | null;
  previewData: { columns: string[]; total_rows: number; preview_rows: any[] } | null;
  onSelectDataset: (ds: Dataset) => void;
  onUploadCSV: (file: File) => void;
  onCombineDatasets?: (params: { dataset_ids?: string[]; combined_name?: string; merge_strategy?: string }) => Promise<void>;
  onDeleteDataset?: (datasetId: string) => Promise<void>;
  onNavigateToAnalyst?: () => void;
}

export const DatasetManager: React.FC<DatasetManagerProps> = ({
  datasets,
  selectedDataset,
  profile,
  previewData,
  onSelectDataset,
  onUploadCSV,
  onCombineDatasets,
  onDeleteDataset,
  onNavigateToAnalyst,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  // Combine modal state
  const [isCombineModalOpen, setIsCombineModalOpen] = useState(false);
  const [selectedIdsToCombine, setSelectedIdsToCombine] = useState<string[]>([]);
  const [combinedName, setCombinedName] = useState('');
  const [mergeStrategy, setMergeStrategy] = useState<'concat' | 'merge'>('concat');
  const [isCombining, setIsCombining] = useState(false);

  const isCurrentDatasetCombined =
    selectedDataset?.filename.startsWith('Combined_') ||
    profile?.profile.columns.some((c) => c.name === '_source_dataset');

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setIsUploading(true);
      try {
        await onUploadCSV(e.target.files[0]);
      } catch (err) {
        alert('Failed to upload dataset.');
      } finally {
        setIsUploading(false);
      }
    }
  };

  const openCombineModal = () => {
    setSelectedIdsToCombine(datasets.map((d) => d.id));
    setCombinedName(`Combined_Workbench_${datasets.length}_Datasets.csv`);
    setMergeStrategy('concat');
    setIsCombineModalOpen(true);
  };

  const handleToggleSelectId = (id: string) => {
    if (selectedIdsToCombine.includes(id)) {
      setSelectedIdsToCombine(selectedIdsToCombine.filter((i) => i !== id));
    } else {
      setSelectedIdsToCombine([...selectedIdsToCombine, id]);
    }
  };

  const handleSelectAll = () => {
    setSelectedIdsToCombine(datasets.map((d) => d.id));
  };

  const handleDeselectAll = () => {
    setSelectedIdsToCombine([]);
  };

  const handleExecuteCombine = async () => {
    if (!onCombineDatasets) return;
    if (selectedIdsToCombine.length < 2) {
      alert('Please select at least 2 datasets to combine.');
      return;
    }

    setIsCombining(true);
    try {
      await onCombineDatasets({
        dataset_ids: selectedIdsToCombine,
        combined_name: combinedName.trim() || undefined,
        merge_strategy: mergeStrategy,
      });
      setIsCombineModalOpen(false);
    } catch (err) {
      // Error is handled in onCombineDatasets
    } finally {
      setIsCombining(false);
    }
  };

  const handleDelete = async (e: React.MouseEvent, datasetId: string, filename: string) => {
    e.stopPropagation();
    if (!onDeleteDataset) return;
    if (window.confirm(`Are you sure you want to delete dataset "${filename}"?`)) {
      await onDeleteDataset(datasetId);
    }
  };

  const filteredPreviewRows =
    previewData?.preview_rows.filter((row) =>
      Object.values(row).some((val) =>
        String(val).toLowerCase().includes(searchTerm.toLowerCase())
      )
    ) || [];

  const totalSelectedRows = datasets
    .filter((d) => selectedIdsToCombine.includes(d.id))
    .reduce((sum, d) => sum + d.row_count, 0);

  return (
    <div className="space-y-6">
      {/* Upload & Combine Banner */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
            <FileText className="w-5 h-5 text-indigo-600" />
            <span>Dataset Intelligence & Quality Profiler</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Automated dataset profiling, multi-dataset unification, column data-type detection, and health scoring.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Combine All Datasets Button */}
          {datasets.length >= 2 && onCombineDatasets && (
            <button
              type="button"
              onClick={openCombineModal}
              className="px-4 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-semibold text-xs rounded-xl shadow-md shadow-purple-600/20 flex items-center gap-2 transition-all cursor-pointer"
              title="Combine all datasets in this workbench into a single unified dataset for AI analysis"
            >
              <Layers className="w-4 h-4" />
              <span>Combine Datasets to Single</span>
              <span className="px-1.5 py-0.5 rounded-full bg-white/20 text-[10px] font-bold">
                {datasets.length} files
              </span>
            </button>
          )}

          {/* Upload New CSV Button */}
          <label className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl shadow-md shadow-indigo-600/20 flex items-center gap-2 cursor-pointer transition-all">
            <UploadCloud className="w-4 h-4" />
            <span>{isUploading ? 'Uploading & Profiling...' : 'Upload New CSV'}</span>
            <input type="file" accept=".csv" onChange={handleFileChange} className="hidden" disabled={isUploading} />
          </label>
        </div>
      </div>

      {/* Dataset Selector Tabs */}
      {datasets.length > 0 && (
        <div className="flex gap-2 border-b border-slate-200 pb-2 overflow-x-auto items-center">
          {datasets.map((ds) => {
            const isCombined =
              ds.filename.startsWith('Combined_') || ds.filename.includes('combined');
            const isSelected = selectedDataset?.id === ds.id;

            return (
              <div
                key={ds.id}
                onClick={() => onSelectDataset(ds)}
                className={`group px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 border transition-all whitespace-nowrap cursor-pointer ${
                  isSelected
                    ? isCombined
                      ? 'bg-purple-50 text-purple-900 border-purple-300 shadow-xs'
                      : 'bg-indigo-50 text-indigo-700 border-indigo-200 shadow-xs'
                    : 'bg-white text-slate-600 border-slate-200 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                {isCombined ? (
                  <Sparkles className="w-3.5 h-3.5 text-purple-600 shrink-0" />
                ) : (
                  <FileText className="w-3.5 h-3.5 shrink-0" />
                )}
                <span>{ds.filename}</span>
                {isCombined && (
                  <span className="px-1.5 py-0.2 rounded-md bg-purple-100 text-purple-700 text-[10px] font-bold">
                    Combined
                  </span>
                )}
                <span className="text-[10px] text-slate-400">
                  ({ds.row_count.toLocaleString()} rows)
                </span>

                {onDeleteDataset && (
                  <button
                    type="button"
                    onClick={(e) => handleDelete(e, ds.id, ds.filename)}
                    className="opacity-0 group-hover:opacity-100 ml-1 p-1 rounded-md text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-all"
                    title="Delete dataset"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Combined Dataset Notice Banner */}
      {isCurrentDatasetCombined && (
        <div className="p-4 rounded-2xl bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-purple-600 text-white flex items-center justify-center shrink-0 shadow-sm">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs font-bold text-purple-900 flex items-center gap-1.5">
                <span>Single Combined Dataset Active</span>
                <span className="px-1.5 py-0.5 rounded-full bg-purple-200 text-purple-800 text-[10px]">
                  All Workbench Data
                </span>
              </div>
              <p className="text-[11px] text-purple-700 mt-0.5">
                This unified dataset aggregates records from across your workbench tables with source tracking (<code className="font-mono font-semibold">_source_dataset</code>).
              </p>
            </div>
          </div>

          {onNavigateToAnalyst && (
            <button
              type="button"
              onClick={onNavigateToAnalyst}
              className="px-3.5 py-2 bg-purple-600 hover:bg-purple-700 text-white font-semibold text-xs rounded-xl shadow-sm flex items-center gap-1.5 transition-all shrink-0"
            >
              <span>Ask AI on Combined Data</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      )}

      {/* Dataset Quality & Profiling Overview */}
      {profile && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Health Score & Recommendations Card */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 space-y-4 shadow-sm">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-emerald-600" />
              <span>Data Quality & Health Score</span>
            </h3>

            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-200">
              <div>
                <div className="text-3xl font-black text-emerald-600">
                  {profile.profile.data_quality.quality_score}%
                </div>
                <span className="text-[11px] text-slate-500 font-medium">Dataset Quality Score</span>
              </div>
              <div className="text-right text-xs space-y-0.5 text-slate-500">
                <div>Missing Cells: <span className="text-slate-800 font-semibold">{profile.profile.data_quality.missing_percentage}%</span></div>
                <div>Duplicates: <span className="text-slate-800 font-semibold">{profile.profile.data_quality.duplicate_rows}</span></div>
              </div>
            </div>

            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">AI Recommendations</h4>
              <ul className="space-y-1.5 text-xs text-slate-700">
                {profile.profile.data_quality.recommendations.map((rec, idx) => (
                  <li key={idx} className="flex items-start gap-2 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Column Definitions & Statistics */}
          <div className="lg:col-span-2 p-6 rounded-2xl bg-white border border-slate-200 space-y-4 shadow-sm">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-600" />
              <span>Column Profiling & Statistical Summary</span>
            </h3>

            <div className="overflow-x-auto max-h-80">
              <table className="w-full text-left text-xs text-slate-700 border-collapse">
                <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider sticky top-0 border-b border-slate-200">
                  <tr>
                    <th className="p-2.5">Column Name</th>
                    <th className="p-2.5">Type</th>
                    <th className="p-2.5">Unique</th>
                    <th className="p-2.5">Null %</th>
                    <th className="p-2.5">Summary Statistics / Samples</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {profile.profile.columns.map((col, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/80">
                      <td className="p-2.5 font-semibold text-slate-900 flex items-center gap-1.5">
                        {col.name === '_source_dataset' && (
                          <span className="px-1.5 py-0.5 rounded bg-purple-100 text-purple-700 text-[10px] font-bold">Source</span>
                        )}
                        <span>{col.name}</span>
                      </td>
                      <td className="p-2.5 font-mono text-indigo-600">{col.data_type}</td>
                      <td className="p-2.5">{col.unique_values.toLocaleString()}</td>
                      <td className="p-2.5">{col.null_percentage}%</td>
                      <td className="p-2.5 text-slate-500">
                        {col.numeric_stats ? (
                          <span>min: {col.numeric_stats.min}, max: {col.numeric_stats.max}, mean: {col.numeric_stats.mean}</span>
                        ) : (
                          <span>{col.example_values.slice(0, 3).join(', ')}</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Dataset Preview Table with Search & Filter */}
      {previewData && (
        <div className="p-6 rounded-2xl bg-white border border-slate-200 space-y-4 shadow-sm">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Dataset Data Preview (First 50 Rows)</h3>
              <p className="text-xs text-slate-500">Total {previewData.total_rows.toLocaleString()} rows loaded on server.</p>
            </div>

            <div className="relative w-full sm:w-64">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search table rows..."
                className="w-full bg-slate-50 border border-slate-300 rounded-xl pl-9 pr-4 py-1.5 text-xs text-slate-900 outline-none focus:bg-white focus:border-indigo-600 transition-colors placeholder:text-slate-400"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>

          <div className="overflow-x-auto max-h-96 rounded-xl border border-slate-200">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-slate-700 font-semibold sticky top-0 border-b border-slate-200">
                <tr>
                  {previewData.columns.map((col, idx) => (
                    <th key={idx} className="p-3 whitespace-nowrap">
                      {col === '_source_dataset' ? 'Dataset Source' : col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredPreviewRows.map((row, rIdx) => (
                  <tr key={rIdx} className="hover:bg-slate-50/80">
                    {previewData.columns.map((col, cIdx) => (
                      <td key={cIdx} className="p-3 whitespace-nowrap font-mono text-[11px] text-slate-700">
                        {col === '_source_dataset' ? (
                          <span className="px-2 py-0.5 rounded-md bg-purple-50 text-purple-700 border border-purple-200 text-[10px] font-semibold">
                            {String(row[col])}
                          </span>
                        ) : (
                          String(row[col])
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Combine Datasets Modal */}
      {isCombineModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-xl w-full p-6 space-y-5 animate-in fade-in zoom-in duration-150">
            {/* Modal Header */}
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-purple-600 to-indigo-600 text-white flex items-center justify-center shadow-md shadow-purple-600/20">
                  <Layers className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-extrabold text-slate-900">
                    Combine Workbench Datasets into Single Dataset
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Unify multiple tables into a single dataset so AI can answer across all tables.
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsCombineModalOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Checklist of Datasets */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-700">
                  Select Datasets to Combine ({selectedIdsToCombine.length} of {datasets.length} selected):
                </span>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={handleSelectAll}
                    className="text-indigo-600 hover:underline font-semibold"
                  >
                    Select All
                  </button>
                  <span className="text-slate-300">|</span>
                  <button
                    type="button"
                    onClick={handleDeselectAll}
                    className="text-slate-500 hover:underline"
                  >
                    Clear All
                  </button>
                </div>
              </div>

              <div className="max-h-48 overflow-y-auto space-y-1.5 border border-slate-200 rounded-xl p-2 bg-slate-50/50">
                {datasets.map((ds) => {
                  const isChecked = selectedIdsToCombine.includes(ds.id);
                  return (
                    <div
                      key={ds.id}
                      onClick={() => handleToggleSelectId(ds.id)}
                      className={`flex items-center justify-between p-2.5 rounded-lg border text-xs cursor-pointer transition-all ${
                        isChecked
                          ? 'bg-indigo-50/80 border-indigo-200 text-indigo-900 font-semibold'
                          : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        {isChecked ? (
                          <CheckSquare className="w-4 h-4 text-indigo-600 shrink-0" />
                        ) : (
                          <Square className="w-4 h-4 text-slate-400 shrink-0" />
                        )}
                        <span className="truncate max-w-xs">{ds.filename}</span>
                      </div>
                      <div className="text-[11px] text-slate-400 font-normal">
                        {ds.row_count.toLocaleString()} rows • {ds.column_count} cols
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Combined Dataset Name */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700">
                Combined Dataset File Name
              </label>
              <input
                type="text"
                value={combinedName}
                onChange={(e) => setCombinedName(e.target.value)}
                placeholder="e.g. Combined_Workbench_Data.csv"
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-xs font-mono text-slate-900 outline-none focus:bg-white focus:border-indigo-600 transition-colors"
              />
            </div>

            {/* Combination Strategy */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-700">
                Combination Mode
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                <label
                  className={`p-3 rounded-xl border cursor-pointer flex flex-col gap-1 transition-all ${
                    mergeStrategy === 'concat'
                      ? 'bg-indigo-50/80 border-indigo-300 text-indigo-950 font-semibold'
                      : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="strategy"
                      checked={mergeStrategy === 'concat'}
                      onChange={() => setMergeStrategy('concat')}
                      className="text-indigo-600"
                    />
                    <span>Unified Table (Union)</span>
                  </div>
                  <span className="text-[10px] text-slate-500 font-normal leading-tight pl-5">
                    Stacks rows, aligns columns, and adds <code className="font-mono">_source_dataset</code> to trace each file (Recommended).
                  </span>
                </label>

                <label
                  className={`p-3 rounded-xl border cursor-pointer flex flex-col gap-1 transition-all ${
                    mergeStrategy === 'merge'
                      ? 'bg-indigo-50/80 border-indigo-300 text-indigo-950 font-semibold'
                      : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="strategy"
                      checked={mergeStrategy === 'merge'}
                      onChange={() => setMergeStrategy('merge')}
                      className="text-indigo-600"
                    />
                    <span>Merge on Shared Keys</span>
                  </div>
                  <span className="text-[10px] text-slate-500 font-normal leading-tight pl-5">
                    Joins tables on matching key columns (e.g. ID, date). Falls back to union if no keys match.
                  </span>
                </label>
              </div>
            </div>

            {/* Summary preview */}
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-600 flex items-center justify-between">
              <span>Resulting Dataset Size:</span>
              <span className="font-bold text-indigo-600">
                ~{totalSelectedRows.toLocaleString()} rows from {selectedIdsToCombine.length} tables
              </span>
            </div>

            {/* Modal Actions */}
            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setIsCombineModalOpen(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
                disabled={isCombining}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleExecuteCombine}
                disabled={isCombining || selectedIdsToCombine.length < 2}
                className="px-5 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 disabled:opacity-50 text-white font-semibold text-xs rounded-xl shadow-md shadow-purple-600/20 flex items-center gap-2 transition-all cursor-pointer"
              >
                <Layers className="w-4 h-4" />
                <span>{isCombining ? 'Combining & Profiling...' : 'Combine into Single Dataset'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
