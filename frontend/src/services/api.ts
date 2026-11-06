const API = '/api'
async function request(path:string, options?:RequestInit) {
  const response = await fetch(`${API}${path}`, options)
  if (!response.ok) {
    const body = await response.json().catch(() => ({detail:response.statusText}))
    throw new Error(typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail))
  }
  return response.json()
}
export const api = {
  health: () => request('/health'), dashboard: () => request('/dashboard'),
  dataset: () => request('/datasets/info'), generate: (rows=6000) => request(`/demo/generate?rows=${rows}`, {method:'POST'}),
  upload: (file:File) => {const body=new FormData(); body.append('file',file); return request('/datasets/upload',{method:'POST',body})},
  train: (config:object) => request('/federated/train',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(config)}),
  status: () => request('/federated/status'), clients: () => request('/federated/clients'),
  predict: (records:object[]) => request('/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({records})}),
  evaluate: (heldOut='Botnet', threshold=.35) => request(`/zero-day/evaluate?held_out=${encodeURIComponent(heldOut)}&threshold=${threshold}`,{method:'POST'}),
  explain: () => request('/detections/explainability'), experiments: () => request('/experiments'),
  settings: () => request('/settings'), saveSettings: (settings:object) => request('/settings',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({settings})})
}
