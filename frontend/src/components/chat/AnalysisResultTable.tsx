import React, { useState, useMemo } from 'react';
import {
  Table as TableIcon,
  Download,
  Search,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  ChevronLeft,
  ChevronRight,
  FileSpreadsheet,
  FileJson,
  FileText,
  X
} from 'lucide-react';

interface AnalysisResultTableProps {
  data: Record<string, any>[];
  analysisId: string;
}

export const AnalysisResultTable: React.FC<AnalysisResultTableProps> = ({ data, analysisId }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState<number | 'all'>(10);
  const [showExportMenu, setShowExportMenu] = useState(false);

  if (!data || data.length === 0) return null;

  const columns = Object.keys(data[0]);

  const handleSort = (col: string) => {
    if (sortColumn === col) {
      if (sortDirection === 'asc') {
        setSortDirection('desc');
      } else {
        setSortColumn(null);
        setSortDirection('asc');
      }
    } else {
      setSortColumn(col);
      setSortDirection('asc');
    }
    setCurrentPage(1);
  };

  const filteredAndSortedData = useMemo(() => {
    let result = [...data];

    // Filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      result = result.filter((row) =>
        columns.some((col) => {
          const val = row[col];
          return val !== null && val !== undefined && String(val).toLowerCase().includes(q);
        })
      );
    }

    // Sort
    if (sortColumn) {
      result.sort((a, b) => {
        const valA = a[sortColumn];
        const valB = b[sortColumn];
        if (valA === null || valA === undefined) return 1;
        if (valB === null || valB === undefined) return -1;

        const numA = Number(valA);
        const numB = Number(valB);
        if (!isNaN(numA) && !isNaN(numB) && typeof valA !== 'boolean' && typeof valB !== 'boolean') {
          return sortDirection === 'asc' ? numA - numB : numB - numA;
        }

        return sortDirection === 'asc'
          ? String(valA).localeCompare(String(valB))
          : String(valB).localeCompare(String(valA));
      });
    }

    return result;
  }, [data, columns, searchQuery, sortColumn, sortDirection]);

  // Pagination calculation
  const totalRows = filteredAndSortedData.length;
  const isAll = pageSize === 'all';
  const numericPageSize = typeof pageSize === 'number' ? pageSize : totalRows;
  const totalPages = isAll ? 1 : Math.max(1, Math.ceil(totalRows / numericPageSize));
  const safePage = Math.min(Math.max(1, currentPage), totalPages);
  const startIndex = isAll ? 0 : (safePage - 1) * numericPageSize;
  const endIndex = isAll ? totalRows : Math.min(startIndex + numericPageSize, totalRows);
  const displayedRows = isAll ? filteredAndSortedData : filteredAndSortedData.slice(startIndex, endIndex);

  const downloadBlob = (content: string, filename: string, mimeType: string) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    setShowExportMenu(false);
  };

  const exportCSV = () => {
    const csvContent = [
      columns.join(','),
      ...filteredAndSortedData.map((row) =>
        columns.map((k) => `"${String(row[k] ?? '').replace(/"/g, '""')}"`).join(',')
      )
    ].join('\n');
    downloadBlob(csvContent, `analysis_${analysisId}.csv`, 'text/csv;charset=utf-8;');
  };

  const exportJSON = () => {
    const jsonStr = JSON.stringify(filteredAndSortedData, null, 2);
    downloadBlob(jsonStr, `analysis_${analysisId}.json`, 'application/json;charset=utf-8;');
  };

  const exportExcel = () => {
    let tableHtml = `<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
<head><!--[if gte mso 9]><xml><x:ExcelWorkbook><x:ExcelWorksheets><x:ExcelWorksheet><x:Name>Analysis Output</x:Name><x:WorksheetOptions><x:DisplayGridlines/></x:WorksheetOptions></x:ExcelWorksheet></x:ExcelWorksheets></x:ExcelWorkbook></xml><![endif]--><meta http-equiv="content-type" content="text/plain; charset=UTF-8"/></head>
<body><table border="1"><thead><tr>`;
    columns.forEach((h) => {
      tableHtml += `<th style="background-color:#312e81;color:#ffffff;font-weight:bold;padding:8px;">${h}</th>`;
    });
    tableHtml += '</tr></thead><tbody>';
    filteredAndSortedData.forEach((row) => {
      tableHtml += '<tr>';
      columns.forEach((h) => {
        const val = row[h] !== null && row[h] !== undefined ? String(row[h]) : '';
        tableHtml += `<td style="padding:6px;">${val}</td>`;
      });
      tableHtml += '</tr>';
    });
    tableHtml += '</tbody></table></body></html>';
    downloadBlob(tableHtml, `analysis_${analysisId}.xls`, 'application/vnd.ms-excel;charset=utf-8;');
  };

  return (
    <div className="space-y-3">
      {/* Controls Bar: Search Filter & Export Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
        {/* Left: Table Title & Quick Status */}
        <div className="flex items-center gap-2">
          <span className="font-bold text-slate-800 flex items-center gap-1.5">
            <TableIcon className="w-4 h-4 text-indigo-600" />
            <span>Output Table</span>
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
            {totalRows} {totalRows === 1 ? 'row' : 'rows'}
            {searchQuery && ` (of ${data.length})`}
          </span>
        </div>

        {/* Right: Search Filter & Export Buttons */}
        <div className="flex items-center gap-2">
          {/* Search Filter Box */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Search table..."
              className="pl-8 pr-7 py-1 rounded-lg bg-white border border-slate-300 focus:border-indigo-600 text-slate-900 placeholder-slate-400 text-[11px] w-36 sm:w-48 outline-none transition-all shadow-xs"
            />
            {searchQuery && (
              <button
                onClick={() => {
                  setSearchQuery('');
                  setCurrentPage(1);
                }}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                title="Clear search"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </div>

          {/* Export Dropdown / Group */}
          <div className="relative">
            <button
              onClick={() => setShowExportMenu(!showExportMenu)}
              className="px-2.5 py-1 rounded-lg bg-white hover:bg-slate-50 text-indigo-700 hover:text-indigo-800 border border-slate-200 font-medium flex items-center gap-1 text-[11px] transition-colors shadow-xs"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export</span>
            </button>

            {showExportMenu && (
              <div
                className="absolute right-0 mt-1 w-36 bg-white border border-slate-200 rounded-xl shadow-xl py-1 z-30 space-y-0.5"
                onMouseLeave={() => setShowExportMenu(false)}
              >
                <button
                  onClick={exportCSV}
                  className="w-full text-left px-3 py-1.5 hover:bg-indigo-50 text-slate-700 hover:text-indigo-700 text-xs flex items-center gap-2 transition-colors"
                >
                  <FileText className="w-3.5 h-3.5 text-indigo-600" />
                  <span>Export CSV</span>
                </button>
                <button
                  onClick={exportExcel}
                  className="w-full text-left px-3 py-1.5 hover:bg-emerald-50 text-slate-700 hover:text-emerald-700 text-xs flex items-center gap-2 transition-colors"
                >
                  <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Export Excel</span>
                </button>
                <button
                  onClick={exportJSON}
                  className="w-full text-left px-3 py-1.5 hover:bg-amber-50 text-slate-700 hover:text-amber-700 text-xs flex items-center gap-2 transition-colors"
                >
                  <FileJson className="w-3.5 h-3.5 text-amber-600" />
                  <span>Export JSON</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Table Container */}
      <div className="overflow-x-auto max-h-72 rounded-xl border border-slate-200 bg-white shadow-xs">
        <table className="w-full text-left text-xs text-slate-700 border-collapse">
          <thead className="bg-slate-50 text-slate-700 font-semibold sticky top-0 z-10 border-b border-slate-200 select-none">
            <tr>
              {columns.map((k, kIdx) => {
                const isSorted = sortColumn === k;
                return (
                  <th
                    key={kIdx}
                    onClick={() => handleSort(k)}
                    className="p-2.5 whitespace-nowrap hover:bg-slate-100/80 cursor-pointer transition-colors group"
                    title={`Sort by ${k}`}
                  >
                    <div className="flex items-center gap-1.5">
                      <span className={isSorted ? 'text-indigo-700 font-bold' : 'group-hover:text-slate-900'}>
                        {k}
                      </span>
                      {isSorted ? (
                        sortDirection === 'asc' ? (
                          <ArrowUp className="w-3.5 h-3.5 text-indigo-600 font-bold" />
                        ) : (
                          <ArrowDown className="w-3.5 h-3.5 text-indigo-600 font-bold" />
                        )
                      ) : (
                        <ArrowUpDown className="w-3 h-3 text-slate-400 group-hover:text-slate-600 transition-colors opacity-60" />
                      )}
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {displayedRows.length > 0 ? (
              displayedRows.map((row, rIdx) => (
                <tr
                  key={rIdx}
                  className="hover:bg-slate-50 font-mono text-[11px] transition-colors"
                >
                  {columns.map((k, cIdx) => (
                    <td key={cIdx} className="p-2.5 whitespace-nowrap text-slate-700">
                      {row[k] !== null && row[k] !== undefined ? String(row[k]) : '-'}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={columns.length} className="p-6 text-center text-slate-400">
                  No records match "{searchQuery}".
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Table Footer: Rows Info, Page Size Selector & Pagination */}
      <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-500 pt-1">
        {/* Row count range */}
        <div>
          {totalRows > 0 ? (
            <span>
              Showing <strong className="text-slate-700">{startIndex + 1}</strong> to{' '}
              <strong className="text-slate-700">{endIndex}</strong> of{' '}
              <strong className="text-slate-700">{totalRows}</strong> rows
            </span>
          ) : (
            <span>0 rows</span>
          )}
        </div>

        {/* Page Size & Navigation Controls */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="text-slate-500">Page size:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                const val = e.target.value;
                setPageSize(val === 'all' ? 'all' : Number(val));
                setCurrentPage(1);
              }}
              className="bg-white border border-slate-300 rounded px-1.5 py-0.5 text-slate-700 outline-none focus:border-indigo-600 cursor-pointer shadow-xs"
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value="all">All</option>
            </select>
          </div>

          {!isAll && totalPages > 1 && (
            <div className="flex items-center gap-1">
              <button
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={safePage <= 1}
                className="p-1 rounded bg-white hover:bg-slate-50 disabled:opacity-40 disabled:hover:bg-white text-slate-700 border border-slate-200 transition-colors shadow-xs"
                title="Previous page"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
              </button>
              <span className="px-2 py-0.5 rounded bg-white border border-slate-200 font-mono text-[10px] text-slate-700 shadow-xs">
                {safePage} / {totalPages}
              </span>
              <button
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={safePage >= totalPages}
                className="p-1 rounded bg-white hover:bg-slate-50 disabled:opacity-40 disabled:hover:bg-white text-slate-700 border border-slate-200 transition-colors shadow-xs"
                title="Next page"
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
