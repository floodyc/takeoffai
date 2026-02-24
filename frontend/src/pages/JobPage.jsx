import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'

export default function JobPage() {
  const { jobId } = useParams()
  const navigate = useNavigate()
  const [job, setJob] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const load = () => {
      api.getJob(jobId).then(setJob).catch((e) => setError(e.message))
    }
    load()
    const interval = setInterval(() => {
      api.getJob(jobId).then((j) => {
        setJob(j)
        if (j.status === 'completed' || j.status === 'failed') clearInterval(interval)
      })
    }, 3000)
    return () => clearInterval(interval)
  }, [jobId])

  if (error) return (
    <div className="flex items-center justify-center py-20">
      <div className="bg-red-50 border border-red-100 rounded-xl p-6">
        <p className="text-red-600 text-sm">{error}</p>
      </div>
    </div>
  )

  if (!job) return (
    <div className="flex items-center justify-center py-20">
      <svg className="animate-spin h-6 w-6 text-blue-500" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
      </svg>
    </div>
  )

  const aggregated = {}
  let grandTotal = 0
  job.sheets?.forEach((s) => {
    Object.entries(s.final_counts).forEach(([type, count]) => {
      aggregated[type] = (aggregated[type] || 0) + count
    })
    grandTotal += s.total
  })
  const sortedTypes = Object.entries(aggregated).sort((a, b) => b[1] - a[1])

  return (
    <div>
      {/* Breadcrumb */}
      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={() => navigate('/')}
          className="w-8 h-8 rounded-lg bg-white border border-slate-150 flex items-center justify-center text-slate-400 hover:text-slate-600 hover:border-slate-300 transition"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <div>
          <h1 className="text-lg font-bold text-slate-800">{job.filename}</h1>
          <p className="text-xs text-slate-400">Job #{job.id} · {job.label_pattern}</p>
        </div>
      </div>

      {/* Processing */}
      {job.status === 'processing' && (
        <div className="bg-white rounded-2xl border border-slate-100 p-6 mb-6">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-semibold text-blue-600 flex items-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
              Processing
            </span>
            <span className="text-sm text-slate-500 font-mono">{Math.round(job.progress * 100)}%</span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-2.5">
            <div className="h-2.5 rounded-full transition-all duration-700" style={{ width: `${job.progress * 100}%`, background: 'linear-gradient(90deg, #1e3a5f, #3b82f6)' }} />
          </div>
          <p className="text-xs text-slate-400 mt-2">{job.progress_message}</p>
        </div>
      )}

      {job.status === 'pending' && (
        <div className="bg-white rounded-2xl border border-slate-100 p-8 text-center mb-6">
          <p className="text-slate-400 text-sm">Waiting to start...</p>
        </div>
      )}

      {job.status === 'failed' && (
        <div className="bg-red-50 border border-red-100 rounded-2xl p-6 mb-6">
          <p className="text-red-600 font-semibold text-sm">Job failed</p>
          <p className="text-red-500 text-xs mt-1">{job.error_message}</p>
        </div>
      )}

      {/* Results */}
      {job.status === 'completed' && (
        <div className="space-y-6">
          {/* Stats */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white rounded-2xl border border-slate-100 p-5 text-center">
              <p className="text-3xl font-bold text-blue-700 font-mono">{grandTotal}</p>
              <p className="text-xs text-slate-400 mt-1">Total Labels</p>
            </div>
            <div className="bg-white rounded-2xl border border-slate-100 p-5 text-center">
              <p className="text-3xl font-bold text-slate-700 font-mono">{sortedTypes.length}</p>
              <p className="text-xs text-slate-400 mt-1">Types Found</p>
            </div>
            <div className="bg-white rounded-2xl border border-slate-100 p-5 text-center">
              <p className="text-3xl font-bold text-slate-700 font-mono">{job.sheets?.length || 0}</p>
              <p className="text-xs text-slate-400 mt-1">Sheets</p>
            </div>
          </div>

          {/* Table */}
          <div className="bg-white rounded-2xl border border-slate-100 overflow-hidden">
            <div className="px-6 py-4 flex items-center justify-between border-b border-slate-50">
              <h2 className="text-sm font-semibold text-slate-700">Breakdown</h2>
              <a
                href={api.getDownloadUrl(job.id)}
                className="inline-flex items-center gap-1.5 text-white text-xs font-semibold px-4 py-2 rounded-lg transition hover:shadow-md"
                style={{ background: 'linear-gradient(135deg, #1e3a5f, #1e40af)' }}
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Download XLSX
              </a>
            </div>

            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-50">
                  <th className="text-left px-6 py-2.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Label</th>
                  <th className="text-right px-6 py-2.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Count</th>
                  <th className="text-right px-6 py-2.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Share</th>
                  <th className="px-6 py-2.5 w-32"></th>
                </tr>
              </thead>
              <tbody>
                {sortedTypes.map(([type, count]) => {
                  const pct = (count / grandTotal) * 100
                  return (
                    <tr key={type} className="border-b border-slate-50 last:border-0 hover:bg-slate-50/50 transition">
                      <td className="px-6 py-3 text-sm font-mono font-semibold text-slate-700">{type}</td>
                      <td className="px-6 py-3 text-sm text-right text-slate-600 font-mono">{count}</td>
                      <td className="px-6 py-3 text-sm text-right text-slate-400">{pct.toFixed(1)}%</td>
                      <td className="px-6 py-3">
                        <div className="w-full bg-slate-100 rounded-full h-1.5">
                          <div className="h-1.5 rounded-full" style={{ width: `${pct}%`, background: 'linear-gradient(90deg, #1e3a5f, #3b82f6)' }} />
                        </div>
                      </td>
                    </tr>
                  )
                })}
                <tr className="bg-slate-50/50">
                  <td className="px-6 py-3 text-sm font-semibold text-slate-700">TOTAL</td>
                  <td className="px-6 py-3 text-sm text-right font-bold text-blue-700 font-mono">{grandTotal}</td>
                  <td className="px-6 py-3 text-sm text-right text-slate-400">100%</td>
                  <td className="px-6 py-3"></td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Per-sheet */}
          {job.sheets?.length > 1 && (
            <div className="bg-white rounded-2xl border border-slate-100 p-6">
              <h3 className="text-sm font-semibold text-slate-700 mb-4">Per-Sheet Breakdown</h3>
              <div className="space-y-3">
                {job.sheets.map((sheet) => (
                  <div key={sheet.page_index} className="bg-slate-50 rounded-xl p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-slate-700">{sheet.page_label}</span>
                      <span className="text-xs text-slate-400 font-mono">{sheet.total} labels</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {Object.entries(sheet.final_counts)
                        .sort((a, b) => b[1] - a[1])
                        .map(([type, count]) => (
                          <span key={type} className="inline-flex items-center gap-1 bg-white border border-slate-150 rounded-lg px-2 py-0.5 text-xs">
                            <span className="font-mono font-semibold text-slate-600">{type}</span>
                            <span className="text-slate-400">×{count}</span>
                          </span>
                        ))}
                    </div>
                    <div className="flex gap-3 mt-2">
                      {sheet.boundary_additions > 0 && (
                        <p className="text-xs text-green-600">+{sheet.boundary_additions} boundary recovered</p>
                      )}
                      {sheet.boundary_removals > 0 && (
                        <p className="text-xs text-amber-600">−{sheet.boundary_removals} deduped</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
