export default function BillingPage() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-xl font-bold text-slate-800">Billing</h1>
        <p className="text-sm text-slate-400 mt-0.5">Manage your plan and usage</p>
      </div>

      {/* Current plan */}
      <div className="bg-white rounded-2xl border border-slate-100 p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-sm font-semibold text-slate-700">Current Plan</h2>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-lg bg-blue-50 text-blue-600 border border-blue-100">Beta</span>
            </div>
            <p className="text-xs text-slate-400">Free during beta period · All features included</p>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-slate-800">$0<span className="text-sm font-normal text-slate-400">/mo</span></p>
          </div>
        </div>
      </div>

      {/* Usage */}
      <div className="bg-white rounded-2xl border border-slate-100 overflow-hidden mb-6">
        <div className="px-6 py-4 border-b border-slate-50">
          <h2 className="text-sm font-semibold text-slate-700">Usage This Month</h2>
        </div>
        <div className="divide-y divide-slate-50">
          <UsageRow label="Jobs processed" value="—" limit="Unlimited" pct={0} />
          <UsageRow label="Sheets analysed" value="—" limit="Unlimited" pct={0} />
          <UsageRow label="API calls" value="—" limit="Unlimited" pct={0} />
        </div>
      </div>

      {/* Plans comparison */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <PlanCard
          name="Starter"
          price="Free"
          period="forever"
          features={['5 jobs/month', '10 sheets/job', 'Standard grid (8×8)', 'XLSX export']}
          current={false}
          cta="Current"
          disabled
        />
        <PlanCard
          name="Pro"
          price="$49"
          period="/month"
          features={['Unlimited jobs', 'Unlimited sheets', 'Custom grid sizes', 'Priority processing', 'API access']}
          current={false}
          cta="Coming soon"
          highlight
          disabled
        />
        <PlanCard
          name="Enterprise"
          price="Custom"
          period=""
          features={['Volume pricing', 'Dedicated support', 'SSO / SAML', 'Custom models', 'On-premise option']}
          current={false}
          cta="Contact us"
          disabled
        />
      </div>

      {/* Cost breakdown info */}
      <div className="bg-slate-50 rounded-2xl p-6">
        <h3 className="text-sm font-semibold text-slate-700 mb-3">How Costs Work</h3>
        <div className="space-y-2">
          <p className="text-xs text-slate-500 leading-relaxed">
            Each sheet is processed using a VLM (Vision Language Model) grid inspection. An 8×8 grid generates approximately 176 API calls per sheet — 64 cells for Pass 1 plus 112 boundary strips for Pass 2.
          </p>
          <div className="flex gap-6 mt-3">
            <div className="bg-white rounded-xl border border-slate-100 p-3 flex-1">
              <p className="text-lg font-bold text-slate-700 font-mono">~$0.15</p>
              <p className="text-xs text-slate-400">Per sheet (8×8)</p>
            </div>
            <div className="bg-white rounded-xl border border-slate-100 p-3 flex-1">
              <p className="text-lg font-bold text-slate-700 font-mono">~$1.50</p>
              <p className="text-xs text-slate-400">Per 10-sheet set</p>
            </div>
            <div className="bg-white rounded-xl border border-slate-100 p-3 flex-1">
              <p className="text-lg font-bold text-slate-700 font-mono">5 min</p>
              <p className="text-xs text-slate-400">Avg. processing</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function UsageRow({ label, value, limit, pct }) {
  return (
    <div className="px-6 py-4 flex items-center justify-between">
      <div className="flex-1">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-sm text-slate-600">{label}</span>
          <span className="text-xs text-slate-400">{value} / {limit}</span>
        </div>
        <div className="w-full bg-slate-100 rounded-full h-1.5">
          <div className="h-1.5 rounded-full" style={{ width: `${pct}%`, background: 'linear-gradient(90deg, #1e3a5f, #3b82f6)' }} />
        </div>
      </div>
    </div>
  )
}

function PlanCard({ name, price, period, features, cta, highlight, disabled }) {
  return (
    <div className={`rounded-2xl border p-6 ${highlight ? 'border-blue-200 bg-blue-50/30 relative' : 'border-slate-100 bg-white'}`}>
      {highlight && (
        <div className="absolute -top-2.5 left-1/2 -translate-x-1/2">
          <span className="text-xs font-semibold px-3 py-0.5 rounded-full text-white" style={{ background: 'linear-gradient(135deg, #1e3a5f, #1e40af)' }}>
            Recommended
          </span>
        </div>
      )}
      <h3 className="text-sm font-bold text-slate-700 mb-1">{name}</h3>
      <div className="mb-4">
        <span className="text-2xl font-bold text-slate-800">{price}</span>
        <span className="text-sm text-slate-400">{period}</span>
      </div>
      <ul className="space-y-2 mb-6">
        {features.map((f, i) => (
          <li key={i} className="flex items-center gap-2 text-xs text-slate-500">
            <svg className={`w-3.5 h-3.5 flex-shrink-0 ${highlight ? 'text-blue-500' : 'text-slate-300'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
            {f}
          </li>
        ))}
      </ul>
      <button
        disabled={disabled}
        className={`w-full text-sm font-semibold py-2.5 rounded-xl transition ${
          highlight
            ? 'text-white hover:shadow-lg hover:shadow-blue-500/20'
            : 'bg-slate-100 text-slate-400 border border-slate-150'
        }`}
        style={highlight ? { background: 'linear-gradient(135deg, #1e3a5f, #1e40af)' } : {}}
      >
        {cta}
      </button>
    </div>
  )
}
