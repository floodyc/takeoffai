import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'

export default function DashboardPage() {
  const navigate = useNavigate()
  const [jobs, setJobs] = useState([])
  const [showClearConfirm, setShowClearConfirm] = useState(false)

  useEffect(() => {
    api.listJobs().then(setJobs).catch(console.error)
    const interval = setInterval(() => {
      api.listJobs().then(setJobs).catch(console.error)
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  const completed = jobs.filter(j => j.status === 'completed')
  const processing = jobs.filter(j => j.status === 'processing')
  const failed = jobs.filter(j => j.status === 'failed')
  const totalLabels = 0 // Would need backend aggregation

  const handleClearHistory = async () => {
    try {
      await api.clearJobs()
      setJobs([])
    } catch (err) {
      alert(err.message)
    }
    setShowClearConfirm(false)
  }

  return (
    <div>
      {/* Page header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-xl font-bold text-slate-800">Dashboard</h1>
          <p className="text-sm text-slate-400 mt-0.5">Overview of your fixture counting projects</p>
        </div>
        <button
          onClick={() => navigate('/new')}
          className="text-white text-sm font-semibold px-5 py-2.5 rounded-xl transition-all hover:shadow-lg hover:shadow-blue-500/20"
          style={{ background: 'linear-gradient(135deg, #1e3a5f, #1e40af)' }}
        >
          + New Job
        </button>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Jobs" value={jobs.length} icon={
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M2 12h4l2-4 2 8 2-4h4" />
          </svg>
        } color="blue" />
        <StatCard label="Completed" value={completed.length} icon={
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        } color="green" />
        <StatCard label="Processing" value={processing.length} icon={
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        } color="amber" />
        <StatCard label="Failed" value={failed.length} icon={
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        } color="red" />
      </div>

      {/* Recent jobs table */}
      <div className="bg-white rounded-2xl border border-slate-100 overflow-hidden">
        <div className="px-6 py-4 flex items-center justify-between border-b border-slate-50">
          <h2 className="text-sm font-semibold text-slate-700">Recent Jobs</h2>
          {jobs.length > 0 && (
            <div className="flex items-center gap-2">
              {showClearConfirm ? (
                <>
                  <span className="text-xs text-slate-400">Clear all jobs?</span>
                  <button onClick={handleClearHistory} className="text-xs font-semibold text-red-500 hover:text-red-600 transition">Yes, clear</button>
                  <button onClick={() => setShowClearConfirm(false)} className="text-xs text-slate-400 hover:text-slate-600 transition">Cancel</button>
                </>
              ) : (
                <button onClick={() => setShowClearConfirm(true)} className="text-xs text-slate-400 hover:text-slate-600 transition">
                  Clear history
                </button>
              )}
            </div>
          )}
        </div>

        {jobs.length === 0 ? (
          <div className="px-6 py-16 text-center">
            <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
            <p className="text-slate-400 text-sm mb-4">No jobs yet</p>
            <button
              onClick={() => navigate('/new')}
              className="text-sm text-blue-600 font-semibold hover:text-blue-700 transition"
            >
              Create your first job →
            </button>
          </div>
        ) : (
          <div className="divide-y divide-slate-50">
            {jobs.map((job) => (
              <div
                key={job.id}
                onClick={() => navigate(`/jobs/${job.id}`)}
                className="px-6 py-3.5 flex items-center justify-between hover:bg-slate-50/50 cursor-pointer transition group"
              >
                <div className="flex items-center gap-4 flex-1 min-w-0">
                  <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    job.status === 'completed' ? 'bg-green-50' :
                    job.status === 'processing' ? 'bg-blue-50' :
                    job.status === 'failed' ? 'bg-red-50' : 'bg-slate-50'
                  }`}>
                    {job.status === 'completed' ? (
                      <svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7"/></svg>
                    ) : job.status === 'processing' ? (
                      <svg className="w-4 h-4 text-blue-500 animate-spin" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
                    ) : job.status === 'failed' ? (
                      <svg className="w-4 h-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>
                    ) : (
                      <svg className="w-4 h-4 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/></svg>
                    )}
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-slate-700 truncate group-hover:text-slate-900 transition">{job.filename}</p>
                    <p className="text-xs text-slate-400">
                      {new Date(job.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <span className="text-xs text-slate-400 font-mono hidden sm:inline">{job.label_pattern.replace(/\\/g, '')}</span>
                  {job.status === 'processing' ? (
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-slate-100 rounded-full h-1.5">
                        <div className="bg-blue-500 h-1.5 rounded-full transition-all duration-700" style={{ width: `${job.progress * 100}%` }} />
                      </div>
                      <span className="text-xs font-medium text-blue-600 w-8">{Math.round(job.progress * 100)}%</span>
                    </div>
                  ) : (
                    <StatusBadge status={job.status} />
                  )}
                  <svg className="w-4 h-4 text-slate-300 group-hover:text-slate-500 transition" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({ label, value, icon, color }) {
  const colors = {
    blue: { bg: 'bg-blue-50', text: 'text-blue-600', value: 'text-blue-700' },
    green: { bg: 'bg-green-50', text: 'text-green-600', value: 'text-green-700' },
    amber: { bg: 'bg-amber-50', text: 'text-amber-600', value: 'text-amber-700' },
    red: { bg: 'bg-red-50', text: 'text-red-500', value: 'text-red-600' },
  }
  const c = colors[color]

  return (
    <div className="bg-white rounded-2xl border border-slate-100 p-5">
      <div className="flex items-center justify-between mb-3">
        <div className={`w-9 h-9 rounded-lg ${c.bg} ${c.text} flex items-center justify-center`}>
          {icon}
        </div>
      </div>
      <p className={`text-2xl font-bold ${c.value}`}>{value}</p>
      <p className="text-xs text-slate-400 mt-0.5">{label}</p>
    </div>
  )
}

function StatusBadge({ status }) {
  const config = {
    completed: { label: 'Completed', cls: 'bg-green-50 text-green-600 border-green-100' },
    failed: { label: 'Failed', cls: 'bg-red-50 text-red-500 border-red-100' },
    pending: { label: 'Pending', cls: 'bg-slate-50 text-slate-500 border-slate-100' },
  }
  const c = config[status] || config.pending
  return (
    <span className={`text-xs font-medium px-2.5 py-1 rounded-lg border ${c.cls}`}>{c.label}</span>
  )
}
