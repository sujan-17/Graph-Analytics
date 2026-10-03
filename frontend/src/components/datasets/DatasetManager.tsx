import React, { useState } from 'react';
import { UploadCloud, FileText, CheckCircle, AlertTriangle, Search, Filter, ShieldAlert, Sparkles } from 'lucide-react';
import { Dataset, DatasetProfile } from '../../types';

interface DatasetManagerProps {
  datasets: Dataset[];
  selectedDataset: Dataset | null;
  profile: DatasetProfile | null;
  previewData: { columns: string[]; total_rows: number; preview_rows: any[] } | null;
  onSelectDataset: (ds: Dataset) => void;
  onUploadCSV: (file: File) => void;
}

export const DatasetManager: React.FC<DatasetManagerProps> = ({
  datasets,
  selectedDataset,
  profile,
  previewData,
  onSelectDataset,
  onUploadCSV,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [isUploading, setIsUploading] = useState(false);

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

  const filteredPreviewRows = previewData?.preview_rows.filter((row) =>
    Object.values(row).some((val) =>
      String(val).toLowerCase().includes(searchTerm.toLowerCase())
    )
  ) || [];

  return (
    <div className="space-y-6">
      {/* Upload & Dataset Selector Banner */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
            <FileText className="w-5 h-5 text-indigo-600" />
            <span>Dataset Intelligence & Quality Profiler</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Automated dataset profiling, column data-type detection, missing value analysis, and health scoring.
          </p>
        </div>

        <label className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl shadow-md shadow-indigo-600/20 flex items-center gap-2 cursor-pointer transition-all">
          <UploadCloud className="w-4 h-4" />
          <span>{isUploading ? 'Uploading & Profiling...' : 'Upload New CSV'}</span>
          <input type="file" accept=".csv" onChange={handleFileChange} className="hidden" disabled={isUploading} />
        </label>
      </div>

      {/* Dataset Selector Tabs */}
      {datasets.length > 0 && (
        <div className="flex gap-2 border-b border-slate-200 pb-2 overflow-x-auto">
          {datasets.map((ds) => (
            <button
              key={ds.id}
              onClick={() => onSelectDataset(ds)}
              className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 border transition-all whitespace-nowrap ${
                selectedDataset?.id === ds.id
                  ? 'bg-indigo-50 text-indigo-700 border-indigo-200 shadow-xs'
                  : 'bg-white text-slate-600 border-slate-200 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>{ds.filename}</span>
              <span className="text-[10px] text-slate-400">({ds.row_count.toLocaleString()} rows)</span>
            </button>
          ))}
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
                      <td className="p-2.5 font-semibold text-slate-900">{col.name}</td>
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
                    <th key={idx} className="p-3 whitespace-nowrap">{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredPreviewRows.map((row, rIdx) => (
                  <tr key={rIdx} className="hover:bg-slate-50/80">
                    {previewData.columns.map((col, cIdx) => (
                      <td key={cIdx} className="p-3 whitespace-nowrap font-mono text-[11px] text-slate-700">{String(row[col])}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
