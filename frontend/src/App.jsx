import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Activity, AlertCircle, ArrowDownRight, ArrowUpRight, Brain,
  CalendarDays, Check, ChevronDown, CircleHelp, ClipboardList,
  HeartPulse, LoaderCircle, Menu, Plus, RefreshCw, Search,
  ShieldCheck, Sparkles, Stethoscope, TrendingUp, UserRound,
  X, Droplets, Scale, Clock3
} from 'lucide-react'
import {
  CartesianGrid, Line, LineChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis
} from 'recharts'
import './App.css'

const API = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const iconForMetric = (name = '') => {
  const value = name.toLowerCase()
  if (value.includes('heart') || value.includes('pulse')) return HeartPulse
  if (value.includes('glucose') || value.includes('sugar')) return Droplets
  if (value.includes('weight')) return Scale
  return Activity
}

const formatDate = (value) => {
  if (!value) return 'Date not recorded'
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? 'Date not recorded'
    : date.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
}

const formatDateTimeLocal = () => {
  const date = new Date()
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset())
  return date.toISOString().slice(0, 16)
}

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...options.headers,
    },
  })

  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try {
      const body = await response.json()
      message = body.detail || message
    } catch {
      // Keep the HTTP status message when the response isn't JSON.
    }
    throw new Error(message)
  }

  return response.status === 204 ? null : response.json()
}

function App() {
  const [activeTab, setActiveTab] = useState('Overview')
  const [measurements, setMeasurements] = useState([])
  const [conditions, setConditions] = useState([])
  const [treatments, setTreatments] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [refreshing, setRefreshing] = useState(false)
  const [showMeasurementForm, setShowMeasurementForm] = useState(false)
  const [savingMeasurement, setSavingMeasurement] = useState(false)
  const [formError, setFormError] = useState('')
  const [notice, setNotice] = useState('')
  const [selectedMetric, setSelectedMetric] = useState('')
  const [searchText, setSearchText] = useState('')
  const [analysisPrompt, setAnalysisPrompt] = useState('')
  const [analysisResult, setAnalysisResult] = useState('')
  const [analysisError, setAnalysisError] = useState('')
  const [analysing, setAnalysing] = useState(false)

  const [measurementForm, setMeasurementForm] = useState({
    name: '',
    value: '',
    unit: '',
    measured_at: formatDateTimeLocal(),
    source: 'patient_reported',
    condition_id: '',
    notes: '',
  })

  const loadDashboard = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true)
    else setLoading(true)
    setLoadError('')

    try {
      const [measurementData, conditionData, treatmentData] = await Promise.all([
        apiRequest('/api/measurements'),
        apiRequest('/api/conditions'),
        apiRequest('/api/treatments'),
      ])
      setMeasurements(Array.isArray(measurementData) ? measurementData : [])
      setConditions(Array.isArray(conditionData) ? conditionData : [])
      setTreatments(Array.isArray(treatmentData) ? treatmentData : [])
    } catch (error) {
      setLoadError(error.message || 'Could not load dashboard data.')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    loadDashboard()
  }, [loadDashboard])

  const metricNames = useMemo(
    () => [...new Set(measurements.map((item) => item.name))].sort(),
    [measurements],
  )

  useEffect(() => {
    if (metricNames.length && !metricNames.includes(selectedMetric)) {
      setSelectedMetric(metricNames[0])
    }
    if (!metricNames.length) setSelectedMetric('')
  }, [metricNames, selectedMetric])

  const latestMeasurements = useMemo(() => {
    const latestByName = new Map()
    for (const item of measurements) {
      const current = latestByName.get(item.name)
      if (!current || new Date(item.measured_at) > new Date(current.measured_at)) {
        latestByName.set(item.name, item)
      }
    }
    return [...latestByName.values()].sort(
      (a, b) => new Date(b.measured_at) - new Date(a.measured_at),
    )
  }, [measurements])

  const chartData = useMemo(() => {
    return measurements
      .filter((item) => item.name === selectedMetric)
      .slice()
      .sort((a, b) => new Date(a.measured_at) - new Date(b.measured_at))
      .map((item) => ({
        ...item,
        label: new Date(item.measured_at).toLocaleDateString(undefined, {
          day: 'numeric',
          month: 'short',
        }),
        chartValue: Number(item.value),
      }))
  }, [measurements, selectedMetric])

  const filteredMeasurements = useMemo(() => {
    const query = searchText.trim().toLowerCase()
    return measurements
      .slice()
      .sort((a, b) => new Date(b.measured_at) - new Date(a.measured_at))
      .filter((item) => !query || [
        item.name, item.unit, item.source, item.notes,
      ].some((value) => String(value || '').toLowerCase().includes(query)))
  }, [measurements, searchText])

  const activeConditions = conditions.filter((item) => item.status === 'active').length
  const activeTreatments = treatments.filter((item) => item.status === 'active').length

  const updateMeasurementForm = (event) => {
    const { name, value } = event.target
    setMeasurementForm((current) => ({ ...current, [name]: value }))
  }

  const saveMeasurement = async (event) => {
    event.preventDefault()
    setSavingMeasurement(true)
    setFormError('')
    setNotice('')

    try {
      const payload = {
        name: measurementForm.name.trim(),
        value: Number(measurementForm.value),
        unit: measurementForm.unit.trim(),
        measured_at: new Date(measurementForm.measured_at).toISOString(),
        source: measurementForm.source,
        notes: measurementForm.notes.trim() || null,
      }

      if (measurementForm.condition_id) {
        payload.condition_id = Number(measurementForm.condition_id)
      }

      await apiRequest('/api/measurements', {
        method: 'POST',
        body: JSON.stringify(payload),
      })

      setMeasurementForm({
        name: '',
        value: '',
        unit: '',
        measured_at: formatDateTimeLocal(),
        source: 'patient_reported',
        condition_id: '',
        notes: '',
      })
      setShowMeasurementForm(false)
      setNotice('Measurement saved successfully.')
      await loadDashboard(true)
    } catch (error) {
      setFormError(error.message || 'Could not save measurement.')
    } finally {
      setSavingMeasurement(false)
    }
  }

  const runAnalysis = async (event) => {
    event.preventDefault()
    if (!analysisPrompt.trim()) return

    setAnalysing(true)
    setAnalysisError('')
    setAnalysisResult('')

    try {
      const result = await apiRequest('/api/analyze', {
        method: 'POST',
        body: JSON.stringify({ prompt: analysisPrompt.trim() }),
      })
      setAnalysisResult(result.result || 'The API returned no analysis text.')
    } catch (error) {
      setAnalysisError(error.message || 'Analysis could not be completed.')
    } finally {
      setAnalysing(false)
    }
  }

  const tabs = [
    { label: 'Overview', icon: Activity },
    { label: 'Measurements', icon: HeartPulse },
    { label: 'Conditions', icon: ClipboardList },
    { label: 'Treatments', icon: Stethoscope },
    { label: 'AI Analysis', icon: Brain },
  ]

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#" onClick={(event) => { event.preventDefault(); setActiveTab('Overview') }}>
          <span className="brand-mark"><Brain size={23} /></span>
          <span className="brand-copy">
            <strong>MedTwin<span> Pro</span></strong>
            <small>Digital health platform</small>
          </span>
        </a>

        <div className="sidebar-label">WORKSPACE</div>
        <nav className="side-nav" aria-label="Main navigation">
          {tabs.map(({ label, icon: Icon }) => (
            <button
              type="button"
              key={label}
              className={`nav-item ${activeTab === label ? 'selected' : ''}`}
              onClick={() => setActiveTab(label)}
            >
              <Icon size={18} strokeWidth={1.8} />
              <span>{label}</span>
              {label === 'Measurements' && measurements.length > 0 && (
                <span className="nav-count">{measurements.length}</span>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="privacy-card">
            <span className="privacy-icon"><ShieldCheck size={19} /></span>
            <strong>Your health data</strong>
            <p>Measurements and records are loaded from your connected backend.</p>
          </div>
          <div className="connection-state">
            <span className={`connection-dot ${loadError ? 'offline' : loading ? 'pending' : ''}`} />
            <span>{loadError ? 'API connection issue' : loading ? 'Connecting to API…' : 'API connection checked'}</span>
          </div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="mobile-brand">
            <span className="brand-mark"><Brain size={20} /></span>
            <strong>MedTwin Pro</strong>
          </div>
          <div className="breadcrumb">
            <span>Workspace</span><span className="crumb-separator">/</span><strong>{activeTab}</strong>
          </div>
          <div className="topbar-actions">
            <button
              type="button"
              className="icon-button"
              title="Refresh data"
              aria-label="Refresh data"
              onClick={() => loadDashboard(true)}
              disabled={refreshing}
            >
              <RefreshCw size={17} className={refreshing ? 'spin' : ''} />
            </button>
            <div className="profile-chip">
              <span className="profile-avatar"><UserRound size={17} /></span>
              <span className="profile-name">Health workspace</span>
              <ChevronDown size={15} />
            </div>
          </div>
        </header>

        <div className="page-content">
          {loadError && (
            <div className="error-banner" role="alert">
              <AlertCircle size={19} />
              <div><strong>Unable to load your health records</strong><p>{loadError}. Check that the FastAPI backend is running.</p></div>
              <button type="button" className="icon-button" onClick={() => loadDashboard()} aria-label="Retry"><RefreshCw size={16} /></button>
            </div>
          )}

          {notice && (
            <div className="success-banner" role="status">
              <Check size={18} /><span>{notice}</span>
              <button type="button" className="icon-button" onClick={() => setNotice('')} aria-label="Dismiss"><X size={15} /></button>
            </div>
          )}

          <section className="page-heading">
            <div>
              <div className="eyebrow"><span className="eyebrow-dot" /> PERSONAL HEALTH WORKSPACE</div>
              <h1>{activeTab === 'Overview' ? 'Health overview' : activeTab}</h1>
              <p className="page-subtitle">
                {activeTab === 'Overview'
                  ? 'A clear view of your recorded health information.'
                  : activeTab === 'Measurements'
                    ? 'Review and record measurements from your health journey.'
                    : activeTab === 'Conditions'
                      ? 'View your recorded medical conditions and their status.'
                      : activeTab === 'Treatments'
                        ? 'Keep track of recorded treatments and outcomes.'
                        : 'Explore your records with the AI analysis service.'}
              </p>
            </div>
            <div className="heading-actions">
              <button type="button" className="button button-secondary" onClick={() => loadDashboard(true)} disabled={refreshing}>
                <RefreshCw size={16} className={refreshing ? 'spin' : ''} /> Refresh
              </button>
              <button type="button" className="button button-primary" onClick={() => { setShowMeasurementForm((value) => !value); setFormError('') }}>
                {showMeasurementForm ? <X size={17} /> : <Plus size={17} />}
                {showMeasurementForm ? 'Close form' : 'Add measurement'}
              </button>
            </div>
          </section>

          {showMeasurementForm && (
            <section className="panel form-panel">
              <div className="panel-heading">
                <div><h2>Record a measurement</h2><p>Enter a value from a real observation or report.</p></div>
              </div>
              <form className="measurement-form" onSubmit={saveMeasurement}>
                <label>Measurement name
                  <input name="name" value={measurementForm.name} onChange={updateMeasurementForm} placeholder="e.g. Blood pressure" maxLength={150} required />
                </label>
                <label>Value
                  <input name="value" type="number" step="any" value={measurementForm.value} onChange={updateMeasurementForm} placeholder="Enter value" required />
                </label>
                <label>Unit
                  <input name="unit" value={measurementForm.unit} onChange={updateMeasurementForm} placeholder="e.g. mmHg, kg" maxLength={50} required />
                </label>
                <label>Date and time
                  <input name="measured_at" type="datetime-local" value={measurementForm.measured_at} onChange={updateMeasurementForm} required />
                </label>
                <label>Data source
                  <select name="source" value={measurementForm.source} onChange={updateMeasurementForm}>
                    <option value="patient_reported">Patient reported</option>
                    <option value="clinician_reported">Clinician reported</option>
                    <option value="lab_result">Lab result</option>
                    <option value="device_recorded">Device recorded</option>
                    <option value="other">Other</option>
                  </select>
                </label>
                <label>Related condition <span className="optional">(optional)</span>
                  <select name="condition_id" value={measurementForm.condition_id} onChange={updateMeasurementForm}>
                    <option value="">No linked condition</option>
                    {conditions.map((condition) => <option key={condition.id} value={condition.id}>{condition.name}</option>)}
                  </select>
                </label>
                <label className="form-full">Notes <span className="optional">(optional)</span>
                  <textarea name="notes" value={measurementForm.notes} onChange={updateMeasurementForm} rows={2} placeholder="Add context about this reading…" />
                </label>
                {formError && <p className="form-error form-full"><AlertCircle size={16} />{formError}</p>}
                <div className="form-actions form-full">
                  <button type="button" className="button button-secondary" onClick={() => setShowMeasurementForm(false)}>Cancel</button>
                  <button type="submit" className="button button-primary" disabled={savingMeasurement}>
                    {savingMeasurement ? <LoaderCircle className="spin" size={16} /> : <Check size={16} />}
                    {savingMeasurement ? 'Saving…' : 'Save measurement'}
                  </button>
                </div>
              </form>
            </section>
          )}

          {loading ? (
            <div className="loading-state"><LoaderCircle size={28} className="spin" /><p>Loading your health records…</p></div>
          ) : (
            <>
              {activeTab === 'Overview' && (
                <>
                  <section className="summary-grid">
                    <SummaryCard icon={Activity} label="Recorded measurements" value={measurements.length} hint="All stored readings" tone="blue" />
                    <SummaryCard icon={ClipboardList} label="Active conditions" value={activeConditions} hint={`${conditions.length} condition records`} tone="teal" />
                    <SummaryCard icon={Stethoscope} label="Active treatments" value={activeTreatments} hint={`${treatments.length} treatment records`} tone="violet" />
                    <SummaryCard icon={CalendarDays} label="Latest record" value={measurements.length ? formatDate(measurements.reduce((latest, item) => new Date(item.measured_at) > new Date(latest.measured_at) ? item : latest).measured_at) : '—'} hint="Most recent measurement" tone="amber" compact />
                  </section>

                  <div className="dashboard-grid">
                    <section className="panel chart-panel">
                      <div className="panel-heading chart-heading">
                        <div><h2>Measurement trends</h2><p>Historical readings recorded in your workspace</p></div>
                        {metricNames.length > 0 && (
                          <label className="select-wrap">
                            <span className="sr-only">Choose metric</span>
                            <select value={selectedMetric} onChange={(event) => setSelectedMetric(event.target.value)}>
                              {metricNames.map((name) => <option key={name} value={name}>{name}</option>)}
                            </select>
                            <ChevronDown size={15} />
                          </label>
                        )}
                      </div>
                      {chartData.length > 0 ? (
                        <>
                          <div className="chart-current">
                            <strong>{chartData[chartData.length - 1].chartValue} <small>{chartData[chartData.length - 1].unit}</small></strong>
                            <span>Latest recorded value</span>
                          </div>
                          <div className="chart-wrap">
                            <ResponsiveContainer width="100%" height="100%">
                              <LineChart data={chartData} margin={{ top: 10, right: 12, left: -15, bottom: 0 }}>
                                <CartesianGrid stroke="#e9eef5" strokeDasharray="4 5" vertical={false} />
                                <XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fill: '#8b98aa', fontSize: 11 }} dy={10} />
                                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#8b98aa', fontSize: 11 }} />
                                <Tooltip
                                  contentStyle={{ border: '1px solid #e4eaf2', borderRadius: 12, boxShadow: '0 8px 28px #1b36540d' }}
                                  formatter={(value) => [`${value} ${chartData[0]?.unit || ''}`, selectedMetric]}
                                  labelStyle={{ color: '#65758b', marginBottom: 4 }}
                                />
                                <Line type="monotone" dataKey="chartValue" stroke="#2478d4" strokeWidth={2.7} dot={{ r: 3.5, fill: '#2478d4', strokeWidth: 2, stroke: '#fff' }} activeDot={{ r: 6 }} />
                              </LineChart>
                            </ResponsiveContainer>
                          </div>
                          <p className="chart-footnote"><CircleHelp size={14} /> Shows recorded readings only; no target or prediction is inferred.</p>
                        </>
                      ) : (
                        <EmptyState icon={TrendingUp} title="No trend data yet" message="Record at least one measurement to see it here. More readings will reveal a trend over time." />
                      )}
                    </section>

                    <section className="panel recent-panel">
                      <div className="panel-heading">
                        <div><h2>Latest measurements</h2><p>Your most recent recorded values</p></div>
                        <button type="button" className="text-button" onClick={() => setActiveTab('Measurements')}>View all <ArrowUpRight size={14} /></button>
                      </div>
                      {latestMeasurements.length ? (
                        <div className="latest-list">
                          {latestMeasurements.slice(0, 5).map((item) => {
                            const Icon = iconForMetric(item.name)
                            return (
                              <div className="latest-item" key={item.id}>
                                <span className="metric-icon"><Icon size={19} /></span>
                                <div className="latest-copy"><strong>{item.name}</strong><span>{formatDate(item.measured_at)}</span></div>
                                <div className="latest-value"><strong>{item.value}</strong><span>{item.unit}</span></div>
                              </div>
                            )
                          })}
                        </div>
                      ) : (
                        <EmptyState icon={HeartPulse} title="No measurements yet" message="Your recorded health values will appear here." />
                      )}
                    </section>
                  </div>

                  <div className="lower-grid">
                    <section className="panel">
                      <div className="panel-heading"><div><h2>Medical conditions</h2><p>Conditions stored in your records</p></div><button type="button" className="text-button" onClick={() => setActiveTab('Conditions')}>View all <ArrowUpRight size={14} /></button></div>
                      {conditions.length ? <div className="record-list">
                        {conditions.slice(0, 4).map((condition) => <div className="record-row" key={condition.id}>
                          <span className="record-icon"><ClipboardList size={18} /></span>
                          <div className="record-copy"><strong>{condition.name}</strong><span>Added {formatDate(condition.created_at)}</span></div>
                          <StatusBadge status={condition.status} />
                        </div>)}
                      </div> : <EmptyState icon={ClipboardList} title="No conditions recorded" message="Your condition list is currently empty." />}
                    </section>
                    <section className="panel">
                      <div className="panel-heading"><div><h2>Treatment overview</h2><p>Existing treatment records</p></div><button type="button" className="text-button" onClick={() => setActiveTab('Treatments')}>View all <ArrowUpRight size={14} /></button></div>
                      {treatments.length ? <div className="record-list">
                        {treatments.slice(0, 4).map((treatment) => <div className="record-row" key={treatment.id}>
                          <span className="record-icon treatment-icon"><Stethoscope size={18} /></span>
                          <div className="record-copy"><strong>{treatment.name}</strong><span>{treatment.treatment_type.replaceAll('_', ' ')} · {treatment.provider_name || 'Provider not recorded'}</span></div>
                          <StatusBadge status={treatment.status} />
                        </div>)}
                      </div> : <EmptyState icon={Stethoscope} title="No treatments recorded" message="Your treatment list is currently empty." />}
                    </section>
                  </div>
                </>
              )}

              {activeTab === 'Measurements' && (
                <section className="panel table-panel">
                  <div className="panel-heading table-heading">
                    <div><h2>All measurements</h2><p>{measurements.length} recorded {measurements.length === 1 ? 'measurement' : 'measurements'}</p></div>
                    <label className="search-box"><Search size={16} /><input value={searchText} onChange={(event) => setSearchText(event.target.value)} placeholder="Search measurements…" /></label>
                  </div>
                  {filteredMeasurements.length ? (
                    <div className="table-scroll"><table><thead><tr><th>Measurement</th><th>Value</th><th>Date recorded</th><th>Source</th><th>Notes</th></tr></thead><tbody>
                      {filteredMeasurements.map((item) => <tr key={item.id}>
                        <td><strong>{item.name}</strong><span className="cell-sub">Record #{item.id}</span></td>
                        <td><strong>{item.value} {item.unit}</strong></td>
                        <td>{formatDate(item.measured_at)}</td>
                        <td><span className="source-tag">{item.source.replaceAll('_', ' ')}</span></td>
                        <td className="notes-cell">{item.notes || '—'}</td>
                      </tr>)}
                    </tbody></table></div>
                  ) : <EmptyState icon={Activity} title={searchText ? 'No matching measurements' : 'No measurements recorded'} message={searchText ? 'Try a different search term.' : 'Use Add measurement to record your first reading.'} />}
                </section>
              )}

              {activeTab === 'Conditions' && (
                <section className="panel">
                  <div className="panel-heading"><div><h2>Medical conditions</h2><p>Conditions currently stored in the backend</p></div><span className="count-pill">{conditions.length} total</span></div>
                  {conditions.length ? <div className="condition-grid">
                    {conditions.map((condition) => <article className="condition-card" key={condition.id}>
                      <div className="condition-card-top"><span className="record-icon"><ClipboardList size={20} /></span><StatusBadge status={condition.status} /></div>
                      <h3>{condition.name}</h3>
                      <p className="muted-line">Diagnosis date: {formatDate(condition.diagnosis_date)}</p>
                      {condition.notes && <p className="condition-notes">{condition.notes}</p>}
                      <div className="condition-footer"><span>Record #{condition.id}</span><span>Added {formatDate(condition.created_at)}</span></div>
                    </article>)}
                  </div> : <EmptyState icon={ClipboardList} title="No conditions recorded" message="No condition records were returned by the API." />}
                </section>
              )}

              {activeTab === 'Treatments' && (
                <section className="panel">
                  <div className="panel-heading"><div><h2>Treatment records</h2><p>Existing treatment details and recorded status</p></div><span className="count-pill">{treatments.length} total</span></div>
                  {treatments.length ? <div className="treatment-list">
                    {treatments.map((treatment) => <TreatmentRecord key={treatment.id} treatment={treatment} />)}
                  </div> : <EmptyState icon={Stethoscope} title="No treatments recorded" message="Treatment records returned by your backend will appear here." />}
                </section>
              )}

              {activeTab === 'AI Analysis' && (
                <div className="analysis-layout">
                  <section className="panel analysis-panel">
                    <div className="analysis-intro">
                      <span className="analysis-symbol"><Sparkles size={22} /></span>
                      <div><h2>AI health-record analysis</h2><p>Submit a question or a summary of records for the configured AI service to analyze.</p></div>
                    </div>
                    <form onSubmit={runAnalysis}>
                      <label className="analysis-label" htmlFor="analysis-prompt">Your prompt</label>
                      <textarea id="analysis-prompt" className="analysis-textarea" value={analysisPrompt} onChange={(event) => setAnalysisPrompt(event.target.value)} rows={5} placeholder="Example: Summarize these recorded measurements and explain what information is missing: …" required />
                      <p className="analysis-disclaimer"><ShieldCheck size={15} /> Avoid including personal identifiers. AI output may be inaccurate and is not a diagnosis or a substitute for professional medical judgment.</p>
                      {analysisError && <p className="form-error"><AlertCircle size={16} />{analysisError}</p>}
                      <button type="submit" className="button button-primary" disabled={analysing || !analysisPrompt.trim()}>
                        {analysing ? <LoaderCircle size={17} className="spin" /> : <Sparkles size={17} />}
                        {analysing ? 'Analyzing…' : 'Run analysis'}
                      </button>
                    </form>
                  </section>
                  <section className="panel analysis-result-panel">
                    <div className="panel-heading"><div><h2>Analysis result</h2><p>Response from the backend AI service</p></div></div>
                    {analysisResult ? <div className="analysis-result">{analysisResult}</div> : <EmptyState icon={Brain} title="No analysis yet" message="Submit a prompt to see the response here. This result is separate from your saved health measurements." />}
                  </section>
                </div>
              )}
            </>
          )}

          <footer className="page-footer">
            <span><ShieldCheck size={15} /> Health records from your configured backend</span>
            <span><Clock3 size={14} /> Last viewed {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
          </footer>
        </div>
      </main>
    </div>
  )
}

function SummaryCard({ icon: Icon, label, value, hint, tone, compact = false }) {
  return (
    <article className="summary-card">
      <div className="summary-top"><span className={`summary-icon ${tone}`}><Icon size={19} /></span><span className="summary-indicator"><ArrowUpRight size={14} /></span></div>
      <p className="summary-label">{label}</p>
      <div className={`summary-value ${compact ? 'compact-value' : ''}`}>{value}</div>
      <p className="summary-hint">{hint}</p>
    </article>
  )
}

function StatusBadge({ status }) {
  const safeStatus = String(status || 'unknown').toLowerCase()
  const known = ['active', 'resolved', 'inactive', 'planned', 'completed', 'discontinued']
  return <span className={`status-badge ${known.includes(safeStatus) ? safeStatus : 'unknown'}`}><span />{safeStatus.replaceAll('_', ' ')}</span>
}

function EmptyState({ icon: Icon, title, message }) {
  return (
    <div className="empty-state">
      <span className="empty-icon"><Icon size={22} /></span>
      <strong>{title}</strong>
      <p>{message}</p>
    </div>
  )
}

function TreatmentRecord({ treatment }) {
  const [outcomes, setOutcomes] = useState([])
  const [expanded, setExpanded] = useState(false)
  const [outcomeError, setOutcomeError] = useState('')
  const [outcomesLoaded, setOutcomesLoaded] = useState(false)

  const toggleOutcomes = async () => {
    const next = !expanded
    setExpanded(next)
    if (!next || outcomesLoaded) return
    try {
      const result = await apiRequest(`/api/treatments/${treatment.id}/outcomes`)
      setOutcomes(Array.isArray(result) ? result : [])
      setOutcomesLoaded(true)
    } catch (error) {
      setOutcomeError(error.message || 'Could not load outcomes.')
    }
  }

  return (
    <article className="treatment-record">
      <div className="treatment-record-icon"><Stethoscope size={20} /></div>
      <div className="treatment-record-body">
        <div className="treatment-title-row"><h3>{treatment.name}</h3><StatusBadge status={treatment.status} /></div>
        <p className="treatment-type">{treatment.treatment_type.replaceAll('_', ' ')}</p>
        <div className="treatment-meta">
          <span><UserRound size={14} />{treatment.provider_name || 'Provider not recorded'}</span>
          <span><CalendarDays size={14} />{formatDate(treatment.start_date)} – {formatDate(treatment.end_date)}</span>
        </div>
        {treatment.prescribed_regimen && <p className="treatment-regimen">{treatment.prescribed_regimen}</p>}
        {treatment.notes && <p className="treatment-regimen">{treatment.notes}</p>}
        <button type="button" className="text-button outcomes-toggle" onClick={toggleOutcomes}>
          {expanded ? 'Hide outcomes' : 'View recorded outcomes'} <ChevronDown size={14} className={expanded ? 'rotate-icon' : ''} />
        </button>
        {expanded && (
          <div className="outcomes-list">
            {outcomeError ? <p className="form-error">{outcomeError}</p> : outcomes.length ? outcomes.map((outcome) => (
              <div className="outcome-row" key={outcome.id}>
                <StatusBadge status={outcome.outcome_type} />
                <div><p>{outcome.description}</p><span>{formatDate(outcome.recorded_at)} · {outcome.source.replaceAll('_', ' ')}</span></div>
              </div>
            )) : <p className="outcomes-empty">{outcomesLoaded ? 'No outcomes recorded for this treatment.' : 'Loading outcomes…'}</p>}
          </div>
        )}
      </div>
    </article>
  )
}

export default App
