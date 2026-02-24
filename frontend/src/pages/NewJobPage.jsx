import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'

const LABEL_PRESETS = [
  { label: 'LT', desc: 'Lighting fixtures', pattern: 'LT\\d{2,3}[A-Z]?' },
  { label: 'FS', desc: 'Fire safety', pattern: 'FS\\d{2,3}[A-Z]?' },
  { label: 'EM', desc: 'Emergency', pattern: 'EM[B]?-?\\d{0,3}[A-Z]?' },
  { label: 'EF', desc: 'Exhaust fans', pattern: 'EF-?[A-Z0-9]+' },
  { label: 'Custom', desc: 'Your regex', pattern: '' },
]

const MODES = [
  { id: 'thorough', name: 'Thorough', icon: '\u{1F50D}', desc: 'Full agentic refinement', detail: '~25 calls/page \u00B7 ~60s' },
  { id: 'fast', name: 'Fast', icon: '\u26A1', desc: 'Context + coarse scan only', detail: '~13 calls/page \u00B7 ~15s' },
]

export default function NewJobPage() {
  const nav = useNavigate()
  const [info, setInfo] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [pages, setPages] = useState([])
  const [preset, setPreset] = useState(0)
  const [custom, setCustom] = useState('')
  const [mode, setMode] = useState('thorough')
  const [submitting, setSubmitting] = useState(false)
  const [drag, setDrag] = useState(false)

  const upload = async (f) => {
    if (!f?.name.toLowerCase().endsWith('.pdf')) return
    setUploading(true)
    try { setInfo(await api.uploadPDF(f)); setPages([]) } catch(e) { alert(e.message) } finally { setUploading(false) }
  }

  const submit = async () => {
    if (!info || !pages.length) return
    setSubmitting(true)
    try {
      const pat = preset < LABEL_PRESETS.length - 1 ? LABEL_PRESETS[preset].pattern : custom
      await api.createJob(info.upload_id, { pages, label_pattern: pat, detection_mode: mode })
      nav('/')
    } catch(e) { alert(e.message) } finally { setSubmitting(false) }
  }

  const toggle = (i) => setPages(p => p.includes(i) ? p.filter(x=>x!==i) : [...p,i].sort())
  const calls = (mode === 'thorough' ? 25 : 13) * pages.length

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-xl font-bold text-slate-800">New Takeoff</h1>
        <p className="text-sm text-slate-400 mt-0.5">Upload electrical drawings and configure detection</p>
      </div>
      <div className="bg-white rounded-2xl border border-slate-100 overflow-hidden">
        <div className="p-6 space-y-6">
          {!info ? (
            <div onDragOver={e=>{e.preventDefault();setDrag(true)}} onDragLeave={()=>setDrag(false)}
              onDrop={e=>{e.preventDefault();setDrag(false);upload(e.dataTransfer.files[0])}}
              className={`border-2 border-dashed rounded-xl p-10 text-center transition-all ${drag?'border-blue-400 bg-blue-50/50':'border-slate-200 hover:border-slate-300'}`}>
              <input type="file" accept=".pdf" onChange={e=>upload(e.target.files[0])} className="hidden" id="pdf-up"/>
              <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"/>
                </svg>
              </div>
              <label htmlFor="pdf-up" className="cursor-pointer">
                <span className="inline-block text-white text-sm font-semibold px-6 py-2.5 rounded-xl transition hover:shadow-lg hover:shadow-blue-500/20"
                  style={{background:'linear-gradient(135deg,#1e3a5f,#1e40af)'}}>
                  {uploading?'Uploading...':'Choose PDF'}
                </span>
              </label>
              <p className="text-slate-400 text-xs mt-3">or drag and drop</p>
            </div>
          ) : (<>
            <div className="flex items-center gap-3 bg-slate-50 rounded-xl p-4">
              <div className="w-10 h-10 bg-red-50 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"/></svg>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-700 truncate">{info.filename}</p>
                <p className="text-xs text-slate-400">{info.num_pages} pages</p>
              </div>
              <button onClick={()=>{setInfo(null);setPages([])}} className="text-xs text-slate-400 hover:text-red-500 transition font-medium">Remove</button>
            </div>

            <div>
              <div className="flex items-center justify-between mb-3">
                <label className="text-sm font-semibold text-slate-700">Select Pages</label>
                <div className="flex gap-3 text-xs">
                  <button onClick={()=>setPages(Array.from({length:info.num_pages},(_,i)=>i))} className="text-blue-600 font-medium">All</button>
                  <button onClick={()=>setPages([])} className="text-slate-400 font-medium">None</button>
                </div>
              </div>
              <div className="grid grid-cols-6 gap-1.5 max-h-36 overflow-y-auto">
                {info.page_labels.map((_,i)=>(
                  <button key={i} onClick={()=>toggle(i)} className={`text-xs px-2 py-2 rounded-lg border font-medium transition ${pages.includes(i)?'bg-blue-50 border-blue-200 text-blue-700':'bg-white border-slate-150 text-slate-400 hover:border-slate-300'}`}>{i+1}</button>
                ))}
              </div>
              <p className="text-xs text-slate-400 mt-2">{pages.length} of {info.num_pages} selected</p>
            </div>

            <div>
              <label className="text-sm font-semibold text-slate-700 mb-3 block">Label Type</label>
              <div className="grid grid-cols-5 gap-2">
                {LABEL_PRESETS.map((p,i)=>(
                  <button key={i} onClick={()=>setPreset(i)} className={`rounded-xl border p-3 text-center transition ${preset===i?'bg-blue-50 border-blue-200':'bg-white border-slate-150 hover:border-slate-300'}`}>
                    <p className={`text-sm font-bold ${preset===i?'text-blue-700':'text-slate-600'}`}>{p.label}</p>
                    <p className={`text-xs mt-0.5 ${preset===i?'text-blue-500':'text-slate-400'}`}>{p.desc}</p>
                  </button>
                ))}
              </div>
              {preset===LABEL_PRESETS.length-1 && <input type="text" value={custom} onChange={e=>setCustom(e.target.value)} placeholder='e.g. LT\d{2,3}[A-Z]?' className="mt-3 w-full bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-sm font-mono"/>}
            </div>

            <div>
              <label className="text-sm font-semibold text-slate-700 mb-3 block">Detection Mode</label>
              <div className="grid grid-cols-2 gap-3">
                {MODES.map(m=>(
                  <button key={m.id} onClick={()=>setMode(m.id)} className={`rounded-xl border p-4 text-left transition ${mode===m.id?'bg-blue-50 border-blue-200':'bg-white border-slate-150 hover:border-slate-300'}`}>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-lg">{m.icon}</span>
                      <p className={`text-sm font-bold ${mode===m.id?'text-blue-700':'text-slate-600'}`}>{m.name}</p>
                    </div>
                    <p className={`text-xs ${mode===m.id?'text-blue-500':'text-slate-400'}`}>{m.desc}</p>
                    <p className={`text-xs mt-1 ${mode===m.id?'text-blue-400':'text-slate-300'}`}>{m.detail}</p>
                  </button>
                ))}
              </div>
              <p className="text-xs text-slate-400 mt-2">~{calls} API calls · ~${(calls*0.0012).toFixed(2)} est. cost</p>
            </div>
          </>)}
        </div>
        {info && (
          <div className="px-6 py-4 bg-slate-50/50 border-t border-slate-100">
            <button onClick={submit} disabled={submitting||!pages.length}
              className="w-full text-white rounded-xl py-3 text-sm font-semibold disabled:opacity-30 transition-all hover:shadow-lg hover:shadow-blue-500/20"
              style={{background:'linear-gradient(135deg,#1e3a5f,#1e40af)'}}>
              {submitting?'Creating...': `Run Takeoff — ${pages.length} page${pages.length!==1?'s':''}`}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
