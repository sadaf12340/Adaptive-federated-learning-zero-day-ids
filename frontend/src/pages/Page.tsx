import {useEffect, useState} from 'react'
import {BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell} from 'recharts'
import {AlertTriangle, Download, Play, RefreshCw, ShieldCheck, Upload, Zap} from 'lucide-react'
import {api} from '../services/api'

const colors=['#43d6d0','#5599ff','#9b7cff','#ffb454','#ed6a8b','#79d98d']
function Card({title,children,action}:any){return <section className="card"><div className="card-head"><h3>{title}</h3>{action}</div>{children}</section>}
function Metric({label,value,accent='cyan'}:{label:string,value:any,accent?:string}){return <div className="metric"><span>{label}</span><strong className={accent}>{value}</strong></div>}
function Status({message}:{message:string}){return message?<div className="notice">{message}</div>:null}

export function Page({route}:{route:string}){
 const [busy,setBusy]=useState(false), [message,setMessage]=useState('')
 const run=async(fn:()=>Promise<any>, success='Operation completed')=>{setBusy(true);setMessage('Working...');try{await fn();setMessage(success)}catch(e:any){setMessage(e.message)}finally{setBusy(false)}}
 if(route==='/' ) return <Overview run={run}/>
 const shared={busy,setBusy,message,setMessage,run}
 if(route=== '/federated') return <Federated shared={shared}/>
 if(route=== '/traffic') return <Traffic shared={shared}/>
 if(route=== '/zero-day') return <ZeroDay shared={shared}/>
 if(route=== '/explainability') return <Explain shared={shared}/>
 if(route=== '/clients') return <Clients shared={shared}/>
 if(route=== '/performance') return <Performance shared={shared}/>
 if(route=== '/reports') return <Reports shared={shared}/>
 return <SettingsPage shared={shared}/>
}

function Overview({run}:any){const [d,setD]=useState<any>({});
 useEffect(()=>{api.dashboard().then(setD).catch(()=>{})},[])
 const generate=()=>run(async()=>{await api.generate(6000); await api.dashboard().then(setD)},'Synthetic dataset generated')
 return <div className="page"><div className="toolbar"><button className="primary" disabled={false} onClick={generate}><Zap size={16}/>Generate demo data</button></div>
  <section className="project-intro">
   <div className="project-intro-icon"><ShieldCheck/></div>
   <div>
    <span className="eyebrow">About this project</span>
    <h2>Adaptive Federated Learning for Zero-Day Intrusion Detection</h2>
    <p>This local research console detects suspicious network traffic without sharing raw records between simulated clients. It combines federated model training, adaptive client participation, confidence-based zero-day detection, and explainable feature analysis.</p>
   </div>
   <div className="project-tags"><span>Federated learning</span><span>Zero-day detection</span><span>Explainable AI</span></div>
  </section>
  <div className="metrics-grid"><Metric label="Flows analyzed" value={(d.flows_analyzed??0).toLocaleString()}/><Metric label="Normal traffic" value={(d.normal??0).toLocaleString()} accent="green"/><Metric label="Detected attacks" value={(d.detected_attacks??0).toLocaleString()} accent="amber"/><Metric label="Zero-day alerts" value={d.zero_day_alerts??0} accent="red"/><Metric label="Global accuracy" value={d.global_accuracy==null?'--':`${(d.global_accuracy*100).toFixed(1)}%`}/><Metric label="Active clients" value={d.active_clients??0}/></div>
  <div className="grid-2"><Card title="Traffic distribution" action={<span className="status-tag">Live backend</span>}><div className="empty-chart">{d.dataset_loaded?<div className="donut-copy"><ShieldCheck/><b>{d.flows_analyzed}</b><span>flows</span></div>:<span>No dataset loaded</span>}</div></Card>
  <Card title="Recent alert families"><div className="alert-list">{d.recent_alerts?.length?d.recent_alerts.map((a:any)=><div key={a.label}><span><AlertTriangle size={15}/>{a.label}</span><b>{a.count}</b></div>):<p className="muted">Generate a dataset to populate alerts.</p>}</div></Card></div>
 </div>
}

function Federated({shared}:any){const [status,setStatus]=useState<any>({}),[config,setConfig]=useState({clients:5,rounds:8,epochs:2,learning_rate:.01,drift_sensitivity:.15,adaptive:true}),[clients,setClients]=useState<any[]>([])
 const refresh=()=>Promise.all([api.status(),api.clients()]).then(([s,c])=>{setStatus(s);setClients(c)})
 useEffect(()=>{refresh(); api.settings().then((s:any)=>setConfig({clients:s.clients,rounds:s.rounds,epochs:s.epochs,learning_rate:s.learning_rate,drift_sensitivity:s.drift_sensitivity,adaptive:true}))},[])
 const train=()=>shared.run(async()=>{const result=await api.train(config);setStatus({trained:true,rounds:result.rounds,participants:result.participants,active_clients:result.participants.length});refresh()},'Federated model trained')
 const chart=status.rounds||[]
 return <div className="page"><div className="toolbar"><button className="primary" onClick={train} disabled={shared.busy}><Play size={16}/>Start training</button><button onClick={refresh} disabled={shared.busy}><RefreshCw size={16}/>Refresh</button></div><Status message={shared.message}/>
 <div className="metrics-grid"><Metric label="Communication rounds" value={config.rounds}/><Metric label="Local epochs" value={config.epochs}/><Metric label="Active clients" value={status.active_clients??0}/><Metric label="Training loss" value={chart.at(-1)?.loss?.toFixed(4)??'--'}/></div>
 <div className="config-grid">{Object.entries(config).filter(([k])=>k!== 'adaptive').map(([key,value])=> key==='learning_rate'||key==='drift_sensitivity'?null:<label key={key}>{key.replaceAll('_',' ')}<input type="number" value={String(value)} onChange={e=>setConfig({...config,[key]:Number(e.target.value)})}/></label>)}</div>
 <div className="grid-2"><Card title="Training loss"><Chart><Line data={chart} dataKey="loss" stroke="#ed6a8b"/></Chart></Card><Card title="Global accuracy"><Chart><Line data={chart} dataKey="accuracy" stroke="#43d6d0"/></Chart></Card></div>
 <Card title="Client participation"><table><thead><tr><th>Client</th><th>Status</th><th>Local records</th><th>Last training</th><th>Accuracy</th></tr></thead><tbody>{clients.map(c=><tr key={c.id}><td>{c.id}</td><td><span className="status-tag">{c.status}</span></td><td>{c.local_records}</td><td>{c.last_training_at?'Available':'Not started'}</td><td>{c.local_accuracy?.toFixed(3)}</td></tr>)}</tbody></table>{!clients.length&&<p className="muted">Start a training run to create client participation data.</p>}</Card>
 </div>
}
function Chart({children}:any){return <ResponsiveContainer width="100%" height={240}>{children.props.data.length?<LineChart data={children.props.data} margin={{left:-20,right:8,top:12,bottom:0}}><CartesianGrid stroke="#263b53"/><XAxis dataKey="round"/><YAxis domain={[0,'auto']}/><Tooltip contentStyle={{background:'#111f31',border:'1px solid #27445e'}}/><children.type {...children.props}/></LineChart>:<div/>}</ResponsiveContainer>}

function Traffic({shared}:any){const [dataset,setDataset]=useState<any>(null),[result,setResult]=useState<any>(null)
 useEffect(()=>{api.dataset().then(setDataset).catch(()=>{})},[])
 const upload=(e:any)=>{const file=e.target.files?.[0]; if(file) shared.run(()=>api.upload(file).then(setDataset),'Dataset uploaded and validated')}
 const analyze=()=>shared.run(async()=>{const info=dataset||await api.dataset();const preview=info.preview||[]; setResult(await api.predict(preview.slice(0,20)))},'Traffic records analyzed')
 return <div className="page"><div className="toolbar"><label className="button"><Upload size={16}/>Upload CSV<input hidden type="file" accept=".csv,text/csv" onChange={upload}/></label><button className="primary" onClick={analyze} disabled={shared.busy}><ActivityIcon/>Analyze traffic</button></div><Status message={shared.message}/>
 {dataset?<><div className="metrics-grid"><Metric label="Rows" value={dataset.rows}/><Metric label="Columns" value={dataset.columns.length}/><Metric label="Label field" value={dataset.label_column}/><Metric label="Validation" value="Passed" accent="green"/></div><Card title="Dataset preview"><div className="table-wrap"><table><thead><tr>{dataset.columns.slice(0,8).map((c:string)=><th key={c}>{c}</th>)}</tr></thead><tbody>{dataset.preview.slice(0,8).map((r:any,i:number)=><tr key={i}>{dataset.columns.slice(0,8).map((c:string)=><td key={c}>{String(r[c]??'')}</td>)}</tr>)}</tbody></table></div></Card></>:<Card title="Dataset required"><p className="muted">Upload a CSV or generate the synthetic dataset from Overview.</p></Card>}
 {result&&<Card title="Prediction results"><table><thead><tr><th>Record</th><th>Prediction</th><th>Confidence</th><th>Anomaly score</th><th>Disposition</th></tr></thead><tbody>{result.predictions.map((p:any)=><tr key={p.record_index}><td>{p.record_index+1}</td><td>{p.prediction}</td><td>{(p.confidence*100).toFixed(1)}%</td><td>{p.anomaly_score.toFixed(3)}</td><td><span className={p.suspicious?'risk':'status-tag'}>{p.suspicious?'Suspicious':'Normal'}</span></td></tr>)}</tbody></table></Card>}
 </div>
}
function ActivityIcon(){return <span style={{fontSize:'18px'}}>⌁</span>}

function ZeroDay({shared}:any){const [result,setResult]=useState<any>(null),[threshold,setThreshold]=useState(.35)
 useEffect(()=>{api.settings().then((s:any)=>setThreshold(s.anomaly_threshold))},[])
 const evaluate=()=>shared.run(async()=>setResult(await api.evaluate('Botnet',threshold)),'Held-out evaluation completed')
 return <div className="page"><div className="toolbar"><label>Threshold <input className="inline-input" type="number" step=".05" min="0" max="1" value={threshold} onChange={e=>setThreshold(Number(e.target.value))}/></label><button className="primary" onClick={evaluate} disabled={shared.busy}><ShieldAlertIcon/>Evaluate held-out Botnet</button></div><Status message={shared.message}/>
 {result?<><div className="metrics-grid"><Metric label="Accuracy" value={`${(result.accuracy*100).toFixed(1)}%`}/><Metric label="Precision" value={`${(result.precision*100).toFixed(1)}%`}/><Metric label="Recall" value={`${(result.recall*100).toFixed(1)}%`} accent="green"/><Metric label="F1 score" value={`${(result.f1*100).toFixed(1)}%`}/><Metric label="ROC-AUC" value={result.roc_auc?.toFixed(3)??'N/A'}/><Metric label="Held out" value={result.held_out_class} accent="red"/></div><div className="grid-2"><Card title="Confusion matrix"><div className="confusion">{result.confusion_matrix.flat().map((v:number,i:number)=><div key={i}><span>{i<2?'Normal':'Botnet'}</span><b>{v}</b></div>)}</div></Card><Card title="Anomaly score distribution"><ResponsiveContainer width="100%" height={240}><BarChart data={result.anomaly_scores.slice(-40).map((v:number,i:number)=>({i,v}))}><CartesianGrid stroke="#263b53"/><XAxis dataKey="i"/><YAxis/><Tooltip/><Bar dataKey="v" fill="#5599ff"/></BarChart></ResponsiveContainer></Card></div></>:<Card title="Held-out attack experiment"><p className="muted">The experiment trains on known classes and measures whether confidence loss distinguishes held-out Botnet traffic. This is an empirical anomaly heuristic, not proof of universal zero-day detection.</p></Card>}
 </div>
}
function ShieldAlertIcon(){return <span>◇</span>}
function Explain({shared}:any){const [data,setData]=useState<any>(null);useEffect(()=>{api.explain().then(setData)},[])
 return <div className="page"><div className="toolbar"><button onClick={()=>api.explain().then(setData)}><RefreshCw size={16}/>Refresh explanation</button></div><div className="grid-2"><Card title="Mean coefficient importance"><ResponsiveContainer width="100%" height={340}><BarChart data={data?.feature_importance||[]} layout="vertical" margin={{left:70}}><CartesianGrid stroke="#263b53"/><XAxis type="number"/><YAxis dataKey="feature" type="category" width={100}/><Tooltip/><Bar dataKey="importance" fill="#43d6d0"/></BarChart></ResponsiveContainer></Card><Card title="Decision methodology"><p>{data?.methodology||'Waiting for a trained model.'}</p><div className="method-note"><b>Interpretation</b><p>Larger standardized coefficient magnitudes indicate stronger class separation. Contributions are descriptive and do not prove causation.</p></div></Card></div></div>
}
function Clients({shared}:any){const [clients,setClients]=useState<any[]>([]);useEffect(()=>{api.clients().then(setClients)},[])
 return <div className="page"><div className="notice">Clients below are simulated inside this application process. Raw records remain local to each partition in memory; this is not a production distributed deployment.</div><Card title="Simulated federated clients"><table><thead><tr><th>Client ID</th><th>Status</th><th>Local records</th><th>Last training</th><th>Local accuracy</th><th>Participation</th></tr></thead><tbody>{clients.map(c=><tr key={c.id}><td>{c.id}</td><td><span className="status-tag">{c.status}</span></td><td>{c.local_records}</td><td>{c.last_training_at?'Available':'Never'}</td><td>{c.local_accuracy?.toFixed(3)??'--'}</td><td>{c.status==='participated'?'Recorded':'Idle'}</td></tr>)}</tbody></table>{!clients.length&&<p className="muted">Run federated training to populate client state.</p>}</Card></div>
}
function Performance({shared}:any){const [status,setStatus]=useState<any>({});useEffect(()=>{api.status().then(setStatus)},[]);const rounds=status.rounds||[]
 return <div className="page"><div className="metrics-grid"><Metric label="Latest accuracy" value={rounds.at(-1)?`${(rounds.at(-1).accuracy*100).toFixed(1)}%`:'--'}/><Metric label="Latest loss" value={rounds.at(-1)?.loss?.toFixed(4)??'--'} accent="amber"/><Metric label="Rounds completed" value={rounds.length}/><Metric label="Participants" value={status.participants?.length??0}/></div><div className="grid-2"><Card title="Accuracy history"><Chart><Line data={rounds} dataKey="accuracy" stroke="#43d6d0"/></Chart></Card><Card title="Loss history"><Chart><Line data={rounds} dataKey="loss" stroke="#ed6a8b"/></Chart></Card></div></div>
}
function Reports({shared}:any){const [reports,setReports]=useState<any[]>([]);const refresh=()=>api.experiments().then(setReports);useEffect(()=>{refresh()},[])
 const exportCsv=()=>{const csv=['Experiment,Status,Accuracy,Created',...reports.map(r=>`"${r.name}",${r.status},${r.metrics?.accuracy??''},${r.created_at}`)].join('\n');const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));a.download='experiment-history.csv';a.click()}
 return <div className="page"><div className="toolbar"><button onClick={refresh}><RefreshCw size={16}/>Refresh history</button><button className="primary" onClick={exportCsv}><Download size={16}/>Export CSV</button></div><Card title="Experiment history"><table><thead><tr><th>Experiment</th><th>Status</th><th>Accuracy</th><th>Created</th></tr></thead><tbody>{reports.map(r=><tr key={r.id}><td>{r.name}</td><td><span className="status-tag">{r.status}</span></td><td>{r.metrics?.accuracy==null?'--':(r.metrics.accuracy*100).toFixed(1)+'%'}</td><td>{new Date(r.created_at).toLocaleString()}</td></tr>)}</tbody></table>{!reports.length&&<p className="muted">Completed training runs will appear here.</p>}</Card></div>
}
function SettingsPage({shared}:any){const [settings,setSettings]=useState<any>(null);useEffect(()=>{api.settings().then(setSettings)},[])
 const save=()=>shared.run(async()=>{await api.saveSettings(settings);document.documentElement.dataset.theme=settings.theme||'dark'},'Settings saved')
 if(!settings)return <div className="page"><p className="muted">Loading settings...</p></div>
 return <div className="page"><div className="toolbar"><button className="primary" onClick={save}><ShieldCheck size={16}/>Save settings</button></div><Status message={shared.message}/><div className="settings-grid">{Object.entries(settings).map(([key,value])=>key==='theme'?<label key={key}>Theme<select value={String(value)} onChange={e=>setSettings({...settings,[key]:e.target.value})}><option>dark</option><option>light</option></select></label>:<label key={key}>{key.replaceAll('_',' ')}{typeof value==='boolean'?<select value={String(value)} onChange={e=>setSettings({...settings,[key]:e.target.value==='true'})}><option value="true">Enabled</option><option value="false">Disabled</option></select>:<input type={typeof value==='number'?'number':'text'} value={value as any} onChange={e=>setSettings({...settings,[key]:typeof value==='number'?Number(e.target.value):e.target.value})}/>}</label>)}</div></div>
}
