import {useEffect} from 'react'
import {NavLink, useLocation} from 'react-router-dom'
import {Activity, Bot, FileText, Gauge, LayoutDashboard, Network, Settings, ShieldAlert, Users, BrainCircuit} from 'lucide-react'
import {Page} from './pages/Page'
import {api} from './services/api'

const nav = [
  ['/','Overview',LayoutDashboard], ['/federated','Federated Learning',Network], ['/traffic','Traffic Analysis',Activity], ['/zero-day','Zero-Day Detection',ShieldAlert], ['/explainability','Explainable AI',BrainCircuit], ['/clients','Client Management',Users], ['/performance','Model Performance',Gauge], ['/reports','Reports',FileText], ['/settings','Settings',Settings]
]
export default function App(){
 const location=useLocation()
 useEffect(()=>{api.settings().then((settings:any)=>document.documentElement.dataset.theme=settings.theme||'dark').catch(()=>{})},[])
 return <div className="app-shell">
  <aside className="sidebar"><div className="brand-mark"><ShieldAlert/><div><b>ADAPTIVE IDS</b><span>Research Console</span></div></div>
   <nav>{nav.map(([path,label,Icon])=>{const IconComponent=Icon as typeof LayoutDashboard;return <NavLink key={String(path)} to={String(path)} className={({isActive})=>isActive?'active':''}><IconComponent size={18}/><span>{label as string}</span></NavLink>})}</nav>
   <div className="privacy"><Bot size={16}/> Simulated local clients</div>
  </aside>
  <main><header><div><span className="eyebrow">Network Defense Laboratory</span><h1>{String(nav.find(n=>n[0]===location.pathname)?.[1] || 'Overview')}</h1></div><div className="system-pill"><i/> API connected</div></header><Page route={location.pathname}/></main>
 </div>
}
