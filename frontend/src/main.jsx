import React,{useEffect,useState} from 'react';import{createRoot}from'react-dom/client';import{LayoutDashboard,Smartphone,Users,Calculator,FileText,Wallet,Settings,ShieldCheck,LogOut,Menu,Upload,CheckCircle,Plus,ExternalLink}from'lucide-react';import './style.css';
const BASE=(import.meta.env.VITE_API_URL||'http://127.0.0.1:8000').replace(/\/$/,'');
const money=c=>(Number(c||0)/100).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});

// Tradução somente para exibição: os códigos originais permanecem intactos para a API.
const statusLabels={
 available:'Disponível',reserved:'Reservado',sold:'Vendido',rented:'Alugado',
 pending:'Pendente',paid:'Pago',overdue:'Em atraso',review:'Em análise',
 active:'Ativo',draft:'Rascunho',closed:'Encerrado',cancelled:'Cancelado',
 canceled:'Cancelado',returned:'Devolvido',completed:'Concluído',
 approved:'Aprovado',rejected:'Rejeitado',partial:'Parcialmente pago',
 partially_paid:'Parcialmente pago',late:'Em atraso',open:'Em aberto',
 unavailable:'Indisponível',maintenance:'Em manutenção',
 delivered:'Entregue',archived:'Arquivado',inactive:'Inativo',
 historical:'Histórico',defaulted:'Inadimplente',acquired:'Adquirido',
 signed:'Assinado',awaiting:'Aguardando',processing:'Processando'
};
const statusPt=value=>value==null||value===''?'—':statusLabels[String(value).toLowerCase()]||String(value);

const dateOnly=value=>String(value||'').slice(0,10);
const currentStatus=p=>p.status==='pending'&&dateOnly(p.due_at)&&dateOnly(p.due_at)<new Date().toISOString().slice(0,10)?'overdue':p.status;
const monthKey=value=>dateOnly(value).slice(0,7);
const monthLabel=value=>{if(!value)return '—';const [y,m]=value.split('-');return `${m}/${y}`};
const chartBarStyle={background:'linear-gradient(180deg,#29d3b1,#168eaa)',borderRadius:'5px 5px 0 0',minWidth:14};
function MiniBars({items,empty='Sem dados registrados'}){const max=Math.max(1,...items.map(x=>x.value));return items.length?<div style={{display:'flex',alignItems:'flex-end',gap:12,height:190,padding:'12px 4px 0',overflowX:'auto'}}>{items.map(x=><div key={x.key} title={`${x.label}: ${money(x.value)}`} style={{flex:'1 0 46px',minWidth:46,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'flex-end',height:'100%',gap:5}}><small style={{fontSize:11,whiteSpace:'nowrap'}}>{money(x.value)}</small><div style={{...chartBarStyle,width:'65%',height:`${Math.max(x.value>0?3:0,Math.round(x.value/max*118))}px`}}/><small style={{fontSize:11,whiteSpace:'nowrap'}}>{x.label}</small></div>)}</div>:<p>{empty}</p>}
const nav=[['Dashboard',LayoutDashboard],['Simulador',Calculator],['Clientes e fiadores',Users],['Estoque',Smartphone],['Contratos',FileText],['Financeiro',Wallet],['Cobranças',Wallet],['Documentos',ShieldCheck],['Relatórios',Wallet],['Configurações',Settings]];
const inspectionFields=[['screen','Tela'],['touch','Touch'],['cameras','Câmeras'],['speakers','Alto-falantes'],['microphone','Microfone'],['buttons','Botões'],['charging','Carregamento'],['wifi','Wi-Fi'],['bluetooth','Bluetooth'],['face_id','Face ID'],['battery','Bateria'],['body','Carcaça'],['imei_verified','IMEI conferido']];
const kinds=[['client_video','Vídeo do aluguel'],['client_identity','RG e CPF — cliente'],['client_residence','Residência — cliente'],['client_income','Renda — cliente'],['guarantor_video','Vídeo do aluguel — fiador'],['guarantor_identity','RG e CPF — fiador'],['guarantor_residence','Residência — fiador'],['guarantor_income','Renda — fiador']];

function calcularNegociacao({
  custo = 0,
  venda = 0,
  entrada = 0,
  parcelas = 12,
  juros = 8,
  modalidade = 'negociada',
  parcelaFixa = 0
}) {
  const n = Math.max(1, Math.round(Number(parcelas) || 1));
  const custoValor = Math.max(0, Number(custo) || 0);
  const vendaValor = Math.max(0, Number(venda) || 0);
  const entradaValor = Math.max(0, Math.min(vendaValor, Number(entrada) || 0));
  const saldo = vendaValor - entradaValor;
  const capital = Math.max(0, custoValor - entradaValor);

  const valorParcela = modalidade === 'tabelada'
    ? Math.max(0, Number(parcelaFixa) || 0)
    : saldo * (1 + Math.max(0, Number(juros) || 0) * n / 100) / n;

  const totalParcelas = valorParcela * n;
  const totalJuros = totalParcelas - saldo;
  const totalRecebido = entradaValor + totalParcelas;
  const lucroBruto = totalRecebido - custoValor;

  return {
    saldo,
    capital,
    valorParcela,
    totalParcelas,
    totalJuros,
    totalRecebido,
    lucroBruto,
    roi: capital > 0 ? lucroBruto / capital * 100 : 0,
    margem: totalRecebido > 0 ? lucroBruto / totalRecebido * 100 : 0,
    payback: valorParcela > 0 ? capital / valorParcela : 0,
    jurosImplicitos: saldo > 0
      ? (totalParcelas / saldo - 1) * 100 / n
      : 0
  };
}

// Fluxo econômico da entrada: dinheiro parcelado; aparelho de troca considerado no ato.
// Valores em centavos para evitar diferenças de arredondamento na divisão da entrada.
function calcularFluxoEntrada({custo, entradaDinheiro, troca, diluicao, parcelas, valorParcela}) {
  const centavos = v => Math.round(Math.max(0, Number(v) || 0) * 100);
  const custoCent = centavos(custo);
  const entradaCent = centavos(entradaDinheiro);
  const trocaCent = centavos(troca);
  const partes = Math.max(1, Math.min(3, Math.round(Number(diluicao) || 1)));
  const n = Math.max(1, Math.round(Number(parcelas) || 1));
  const parcelaCent = centavos(valorParcela);
  const base = Math.floor(entradaCent / partes);
  const entradas = Array.from({length: partes}, (_, i) => base + (i === partes - 1 ? entradaCent - base * partes : 0));
  const recebimentoInicial = entradas[0] + trocaCent;
  const capitalInicial = Math.max(0, custoCent - recebimentoInicial);
  let acumulado = recebimentoInicial;
  let payback = acumulado >= custoCent ? 0 : null;
  const fluxo = Array.from({length: Math.max(n, partes - 1)}, (_, i) => {
    const periodo = i + 1;
    const anterior = acumulado;
    const entradaNoPeriodo = periodo < partes ? entradas[periodo] : 0;
    const parcelaNoPeriodo = periodo <= n ? parcelaCent : 0;
    const recebido = entradaNoPeriodo + parcelaNoPeriodo;
    acumulado += recebido;
    if (payback === null && acumulado >= custoCent && recebido > 0) {
      payback = (periodo - 1) + (custoCent - anterior) / recebido;
    }
    return {periodo, entrada: entradaNoPeriodo / 100, parcela: parcelaNoPeriodo / 100,
      recebido: recebido / 100, acumulado: acumulado / 100,
      recuperado: Math.min(custoCent, acumulado) / 100};
  });
  return {entradas: entradas.map(v => v / 100), recebimentoInicial: recebimentoInicial / 100,
    capitalInicial: capitalInicial / 100, payback, fluxo};
}

function App(){const [historyFile,setHistoryFile]=useState(null),[historyPreview,setHistoryPreview]=useState(null),[historyBusy,setHistoryBusy]=useState(false);const [inventoryFile,setInventoryFile]=useState(null),[inventoryPreview,setInventoryPreview]=useState(null),[inventoryBusy,setInventoryBusy]=useState(false);const[token,setToken]=useState(sessionStorage.getItem('canog_token')||''),[portalToken,setPortalToken]=useState(sessionStorage.getItem('canog_portal')||''),[portal,setPortal]=useState(false),[page,setPage]=useState('Dashboard'),[menu,setMenu]=useState(false),[login,setLogin]=useState({email:'',password:''}),[portalLogin,setPortalLogin]=useState({cpf:'',password:'',tenant_id:''}),[customers,setCustomers]=useState([]),[devices,setDevices]=useState([]),[contracts,setContracts]=useState([]),[installments,setInstallments]=useState([]),[dash,setDash]=useState({}),[settings,setSettings]=useState({}),[me,setMe]=useState(null),[message,setMessage]=useState(''),[error,setError]=useState(''),[form,setForm]=useState({}),[simContractDraft,setSimContractDraft]=useState(null),[selected,setSelected]=useState(''),[docs,setDocs]=useState([]),[sim,setSim]=useState({price_cents:250000,cost_cents:180000,entry_cents:50000,trade_in_cents:0,count:12,rate_pct:8,mode:'price',negotiated_installment_cents:26500}),[result,setResult]=useState(null),[dueAlerts,setDueAlerts]=useState(null),[legalStatus,setLegalStatus]=useState(null),[legalContract,setLegalContract]=useState(''),[legalForm,setLegalForm]=useState({}),[inspectionContract,setInspectionContract]=useState(''),[inspection,setInspection]=useState({checks:{},observations:'',accessories:''}),[financeSearch,setFinanceSearch]=useState(''),[financeStatus,setFinanceStatus]=useState('todos'),[financeMonth,setFinanceMonth]=useState(''),[detailContractId,setDetailContractId]=useState(''),[contractStatusFilter,setContractStatusFilter]=useState('todos'),[financeProofOnly,setFinanceProofOnly]=useState(false),[collectionSearch,setCollectionSearch]=useState(''),[collectionOrder,setCollectionOrder]=useState('dias'),[detailReturnPage,setDetailReturnPage]=useState('Financeiro'),[collectionHistory,setCollectionHistory]=useState([]),[historyCustomer,setHistoryCustomer]=useState(''),[historyForm,setHistoryForm]=useState({channel:'whatsapp',outcome:'no_reply',contract_id:'',notes:'',follow_up_date:''}),[historySaving,setHistorySaving]=useState(false);
async function req(path,{method='GET',body,auth=token,formData=false}={}){const r=await fetch(BASE+path,{method,headers:{...(auth?{Authorization:'Bearer '+auth}:{}),...(body&&!formData?{'Content-Type':'application/json'}:{})},body:body?(formData?body:JSON.stringify(body)):undefined});if(!r.ok){let e;try{e=await r.json()}catch{}throw Error(typeof e?.detail==='string'?e.detail:JSON.stringify(e?.detail||'Erro '+r.status))}return r.headers.get('content-type')?.includes('application/json')?r.json():r.blob()}
async function refresh(){if(!token)return;try{const [c,d,k,i,x,s]=await Promise.all(['/customers','/devices','/contracts','/installments','/dashboard','/settings'].map(p=>req(p)));setCustomers(c);setDevices(d);setContracts(k);setInstallments(i);setDash(x);setSettings(s)}catch(e){setError(e.message)}}
 useEffect(()=>{if(token)req('/collections/history').then(setCollectionHistory).catch(e=>setError('Histórico de cobranças: '+e.message));else setCollectionHistory([])},[token]);
useEffect(()=>{refresh()},[token]);useEffect(()=>{if(portal&&portalToken)req('/portal/me',{auth:portalToken}).then(setMe).catch(e=>setError(e.message))},[portal,portalToken]);
async function act(fn){setError('');setMessage('');try{const t=await fn();setMessage('Operação concluída.');await refresh();return t}catch(e){setError(e.message)}}
async function signIn(e){e.preventDefault();setError('');setMessage('');try{const a=await req('/auth/login',{method:'POST',body:login,auth:''});sessionStorage.setItem('canog_token',a.access_token);setToken(a.access_token)}catch(e){setError(e.message)}}
async function signPortal(e){e.preventDefault();setError('');setMessage('');try{const a=await req('/portal/login',{method:'POST',body:portalLogin,auth:''});sessionStorage.setItem('canog_portal',a.access_token);setPortalToken(a.access_token)}catch(e){setError(e.message)}}
async function sendPortalProof(installmentId,file){if(!file)return;setError('');setMessage('');try{const fd=new FormData();fd.append('file',file);await req('/portal/installments/'+installmentId+'/proof',{method:'POST',body:fd,auth:portalToken,formData:true});const updated=await req('/portal/me',{auth:portalToken});setMe(updated);setMessage('Comprovante enviado para análise.')}catch(e){setError(e.message)}}
const field=(label,key,type='text',placeholder='')=><label>{label}<input type={type} placeholder={placeholder} value={form[key]??''} onChange={e=>setForm({...form,[key]:e.target.value})}/></label>;
const sel=(label,key,options)=><label>{label}<select value={form[key]||''} onChange={e=>setForm({...form,[key]:e.target.value})}><option value=''>Selecione</option>{options.map(o=><option value={o.id} key={o.id}>{o.name||o.model}</option>)}</select></label>;
async function submitCustomer(e){e.preventDefault();await act(async()=>{await req('/customers',{method:'POST',body:{name:form.name,cpf:form.cpf,phone:form.phone||'',email:form.email||'',address:form.address||''}});setForm({})})}
async function inventoryImport(action){
 if(!inventoryFile)return;
 setInventoryBusy(true);setError('');setMessage('');
 try{
  const fd=new FormData();fd.append('file',inventoryFile);
  const data=await req('/imports/inventory/'+action,{method:'POST',body:fd,formData:true});
  if(action==='preview')setInventoryPreview(data);
  else{setMessage(`Importados ${data.created} aparelhos; ignorados ${data.skipped}.`);setInventoryPreview(null);setInventoryFile(null);await refresh()}
 }catch(e){setError(e.message)}finally{setInventoryBusy(false)}
}
 async function previewHistory(){if(!historyFile)return;setHistoryBusy(true);setError('');setMessage('');try{const fd=new FormData();fd.append('file',historyFile);setHistoryPreview(await req('/imports/history/preview',{method:'POST',body:fd,formData:true}))}catch(e){setError(e.message)}finally{setHistoryBusy(false)}}
async function confirmHistory(){if(!historyFile||!historyPreview)return; if(!window.confirm('Importar vendas e parcelas históricas? Os saldos sem histórico serão considerados em aberto.'))return;setHistoryBusy(true);setError('');setMessage('');try{const fd=new FormData();fd.append('file',historyFile);const data=await req('/imports/history/confirm',{method:'POST',body:fd,formData:true});setMessage(`Importação concluída: ${data.created_sales} vendas e ${data.created_installments} parcelas. ${data.skipped_sales} vendas já existentes.`);setHistoryPreview(null);await refresh()}catch(e){setError(e.message)}finally{setHistoryBusy(false)}}
 async function submitDevice(e){e.preventDefault();await act(async()=>{await req('/devices',{method:'POST',body:{model:form.model,imei:form.imei,cost_cents:Math.round(Number(form.cost)*100),color:form.color||'',capacity:form.capacity||''}});setForm({})})}
async function submitContract(e){e.preventDefault();if(simContractDraft?.periodo!=='Mensal' && simContractDraft){setError('O backend ainda não recebe periodicidade semanal ou diária. Ajuste a simulação para Mensal antes de salvar.');return;}if(simContractDraft?.diluicao>1){setError('Entrada diluída em 2x ou 3x ainda não pode ser salva: o backend precisa registrar os vencimentos adicionais. Para evitar cobranças incorretas, aguarde a próxima integração.');return;} await act(async()=>{await req('/contracts',{method:'POST',body:{customer_id:form.customer_id,guarantor_id:form.guarantor_id,device_id:form.device_id,installments_count:Number(form.count),installment_cents:Math.round(Number(form.installment)*100),entry_cents:Math.round(Number(form.entry||0)*100),trade_in_cents:Math.round(Number(form.trade||0)*100),residual_cents:Math.round(Number(form.residual||0)*100),first_due:new Date(form.due+'T12:00:00').toISOString()}});setForm({});setSimContractDraft(null)})}
async function getDocs(id){setSelected(id);setDocs([]);if(!id)return;try{setDocs(await req('/contracts/'+id+'/documents'))}catch(e){setError(e.message)}}
async function upload(e){e.preventDefault();const formElement=e.currentTarget;const fd=new FormData(formElement);const id=selected;if(!id){setError('Selecione um contrato.');return}setError('');setMessage('');try{await req('/contracts/'+id+'/documents',{method:'POST',body:fd,formData:true});formElement.reset();await getDocs(id);setMessage('Documento enviado com sucesso.');await refresh()}catch(e){setError(e.message)}}
async function openInspection(id){try{const data=await req('/contracts/'+id+'/inspection');setInspection(data);setInspectionContract(id)}catch(e){setError(e.message)}}
async function download(path,filename){try{const blob=await req(path);const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),3000)}catch(e){setError(e.message)}}
async function downloadPortalQr(){try{const blob=await req('/portal/pix-qr',{auth:portalToken});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='pix-canog.png';a.click();setTimeout(()=>URL.revokeObjectURL(url),3000)}catch(e){setError(e.message)}}
function logout(){sessionStorage.removeItem('canog_token');setToken('');setPage('Dashboard')}
const contractsById=new Map(contracts.map(c=>[c.id,c]));
const customersById=new Map(customers.map(c=>[c.id,c]));
const devicesById=new Map(devices.map(d=>[d.id,d]));
const contractCustomer=p=>customersById.get(contractsById.get(p.contract_id)?.customer_id)?.name||'Cliente não identificado';
const financeRows=installments.filter(p=>{const search=financeSearch.trim().toLocaleLowerCase('pt-BR');return (!search||[contractCustomer(p),p.contract_id,String(p.number)].some(v=>String(v||'').toLocaleLowerCase('pt-BR').includes(search)))&&(financeStatus==='todos'||currentStatus(p)===financeStatus)&&(!financeProofOnly||(p.status==='review'&&Boolean(p.proof_id)))&&(!financeMonth||monthKey(p.due_at)===financeMonth)}).sort((a,b)=>String(a.due_at).localeCompare(String(b.due_at)));
const financeTotal=financeRows.reduce((sum,p)=>sum+Number(p.amount_cents||0),0);
const months=[...new Set(installments.map(p=>monthKey(p.due_at)).filter(Boolean))].sort();
const dueByMonth=months.map(key=>({key,label:monthLabel(key),value:installments.filter(p=>monthKey(p.due_at)===key&&p.status!=='paid').reduce((sum,p)=>sum+Number(p.amount_cents||0),0)}));
const receivedMonths=[...new Set(installments.filter(p=>p.status==='paid'&&p.paid_at).map(p=>monthKey(p.paid_at)).filter(Boolean))].sort();
const paidByMonth=receivedMonths.map(key=>({key,label:monthLabel(key),value:installments.filter(p=>p.status==='paid'&&monthKey(p.paid_at)===key).reduce((sum,p)=>sum+Number(p.amount_cents||0),0)}));
const receivedAmount=Math.max(0,Number(dash.received_cents||0));
const outstandingAmount=Math.max(0,Number(dash.outstanding_cents||0));
const financialTotal=receivedAmount+outstandingAmount;
const receivedPercent=financialTotal?receivedAmount/financialTotal*100:0;
const paidCount=installments.filter(p=>p.status==='paid').length;
const overdueCount=installments.filter(p=>currentStatus(p)==='overdue').length;
const partialCount=installments.filter(p=>['partial','partially_paid'].includes(p.status)).length;
const pendingCount=installments.filter(p=>!['paid','overdue','partial','partially_paid'].includes(currentStatus(p))).length;
const installmentGroups=[{label:'Pagas',count:paidCount,color:'#29d3b1'},{label:'Em atraso',count:overdueCount,color:'#f97373'},{label:'Parciais',count:partialCount,color:'#f5b95e'},{label:'Outras em aberto',count:pendingCount,color:'#64a8f4'}];
const chartGridStyle={display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(min(100%,360px),1fr))',gap:16,alignItems:'stretch'};
const selectedContract=contractsById.get(detailContractId);
const selectedCustomer=selectedContract&&customersById.get(selectedContract.customer_id);
const selectedDevice=selectedContract&&devicesById.get(selectedContract.device_id);
function openContract(id){setDetailReturnPage(page);setDetailContractId(id);setPage('Detalhes do contrato');setError('');setMessage('')}
 const todayLocal=()=>{const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`};
 const daysLate=due=>{const date=dateOnly(due);if(!/^\d{4}-\d{2}-\d{2}$/.test(date))return 0;const [y,m,d]=date.split('-').map(Number),[ty,tm,td]=todayLocal().split('-').map(Number);return Math.max(0,Math.floor((Date.UTC(ty,tm-1,td)-Date.UTC(y,m-1,d))/86400000))};
 const collectionGroups=new Map();
 installments.forEach(p=>{if(!['pending','overdue','partial','partially_paid','late'].includes(p.status)||daysLate(p.due_at)<=0||p.proof_id||p.status==='review')return;const contract=contractsById.get(p.contract_id);if(!contract||contract.status!=='active')return;const customer=customersById.get(contract.customer_id);const key=contract.customer_id||p.contract_id;if(!collectionGroups.has(key))collectionGroups.set(key,{key,customer,items:[],amount:0,days:0,contracts:new Set()});const g=collectionGroups.get(key);g.items.push(p);g.amount+=Number(p.open_cents??p.remaining_cents??p.balance_cents??p.amount_cents??0);g.days=Math.max(g.days,daysLate(p.due_at));g.contracts.add(p.contract_id)});
 const collectionRows=[...collectionGroups.values()].filter(g=>!collectionSearch.trim()||[g.customer?.name,g.customer?.phone,...g.contracts].some(v=>String(v||'').toLocaleLowerCase('pt-BR').includes(collectionSearch.trim().toLocaleLowerCase('pt-BR')))).sort((a,b)=>collectionOrder==='valor'?b.amount-a.amount:collectionOrder==='nome'?String(a.customer?.name||'').localeCompare(String(b.customer?.name||''),'pt-BR'):b.days-a.days);
 const collectionAmount=collectionRows.reduce((a,g)=>a+g.amount,0);
 function collectionWhatsapp(g){const phone=String(g.customer?.phone||'').replace(/\D/g,'');const normalized=phone.length===11||phone.length===10?'55'+phone:phone;if(!/^55\d{10,11}$/.test(normalized)){setError('Telefone ausente ou inválido. Atualize o cadastro do cliente antes de abrir o WhatsApp.');return}const name=String(g.customer?.name||'cliente').trim().split(' ')[0];const lines=g.items.slice().sort((a,b)=>String(a.due_at).localeCompare(String(b.due_at))).map(p=>`Parcela ${p.number}, vencimento ${dateOnly(p.due_at).split('-').reverse().join('/')}: ${money(p.open_cents??p.remaining_cents??p.balance_cents??p.amount_cents)}`);const msg=`Olá, ${name}! Tudo bem? Aqui é da CANOG. Identificamos parcelas que constam em aberto no nosso sistema:\n\n${lines.join('\n')}\n\nTotal registrado: ${money(g.amount)}. Caso já tenha realizado o pagamento, por favor desconsidere esta mensagem e nos envie o comprovante para conferência. Podemos conversar sobre a regularização?`;window.open('https://wa.me/'+normalized+'?text='+encodeURIComponent(msg),'_blank','noopener,noreferrer')}
  const channelNames={whatsapp:'WhatsApp',phone:'Ligação',other:'Outro'};
  const outcomeNames={no_reply:'Sem resposta',promise:'Promessa de pagamento',negotiation:'Negociação',payment_reported:'Pagamento informado',contacted:'Contato realizado',other:'Outro'};
  function beginCollectionRecord(g){setHistoryCustomer(g.key);setHistoryForm({channel:'whatsapp',outcome:'no_reply',contract_id:[...g.contracts][0]||'',notes:'',follow_up_date:''});setError('');setMessage('')}
  async function saveCollectionRecord(e){e.preventDefault();if(!historyCustomer)return;setHistorySaving(true);setError('');setMessage('');try{await req('/collections/history',{method:'POST',body:{customer_id:historyCustomer,contract_id:historyForm.contract_id||null,channel:historyForm.channel,outcome:historyForm.outcome,notes:historyForm.notes,follow_up_date:historyForm.follow_up_date||null}});setCollectionHistory(await req('/collections/history'));setHistoryCustomer('');setMessage('Cobrança registrada no histórico.')}catch(err){setError(err.message)}finally{setHistorySaving(false)}}
 function openDashboardCard(kind){setError('');setMessage('');if(kind==='active'||kind==='draft'){setContractStatusFilter(kind);setPage('Contratos')}else{setFinanceSearch('');setFinanceMonth('');setFinanceStatus(kind==='overdue'?'overdue':'review');setFinanceProofOnly(kind==='proofs');setPage('Financeiro')}setMenu(false)}

if(portal)return <div className="auth-bg"><div className="auth-card"><div className="brand-lockup portal-brand"><img src="/canog-logo.png" alt="CANOG"/><span>PORTAL DO CLIENTE</span></div><h1>Área do cliente</h1><p>Seu contrato e suas parcelas em um só lugar.</p><button className="secondary" onClick={()=>setPortal(false)}>Voltar ao painel</button>{!portalToken?<form onSubmit={signPortal}><label>Código da loja<input required value={portalLogin.tenant_id} onChange={e=>setPortalLogin({...portalLogin,tenant_id:e.target.value})}/></label><label>CPF<input required value={portalLogin.cpf} onChange={e=>setPortalLogin({...portalLogin,cpf:e.target.value})}/></label><label>Senha<input type="password" required value={portalLogin.password} onChange={e=>setPortalLogin({...portalLogin,password:e.target.value})}/></label><button className="primary">Entrar</button></form>:<><h2>Olá, {me?.name}</h2><p>Chave PIX: {me?.pix_key||'Não configurada'}</p><button className="secondary" onClick={()=>navigator.clipboard.writeText(me?.pix_key||'')}>Copiar chave PIX</button><button className="secondary" onClick={()=>downloadPortalQr()}>Visualizar QR cadastrado</button><h3>Parcelas</h3>{me?.installments?.map(p=><div className="record" key={p.id}><b>Parcela {p.number} — {money(p.amount_cents)}</b><span>{statusPt(p.status)} · {p.due_at.slice(0,10)}</span>{p.status==='review'&&<small>Comprovante aguardando conferência.</small>}{p.status==='pending'&&<label>Enviar comprovante<input type="file" accept="image/*,.pdf" onChange={e=>sendPortalProof(p.id,e.target.files?.[0])}/></label>}</div>)}<button className="secondary" onClick={()=>{sessionStorage.removeItem('canog_portal');setPortalToken('');setMe(null)}}>Sair</button></>}{error&&<p className="error">{error}</p>}</div></div>;
if(!token)return <div className="auth-bg"><div className="auth-card"><div className="brand-lockup"><img src="/canog-logo.png" alt="CANOG"/><span>GESTÃO</span></div><h1>Bem-vindo de volta</h1><p>Entre com as credenciais do administrador.</p><form onSubmit={signIn}><label>E-mail<input type="email" required value={login.email} onChange={e=>setLogin({...login,email:e.target.value})}/></label><label>Senha<input type="password" required value={login.password} onChange={e=>setLogin({...login,password:e.target.value})}/></label><button className="primary">Entrar no sistema</button></form><button className="secondary" onClick={()=>{setPortal(true);setError('')}}>Acessar portal do cliente</button>{error&&<p className="error">{error}</p>}</div></div>;
return <div className="app"><aside className={'sidebar '+(menu?'show':'')}><div className="brand-lockup"><img src="/canog-logo.png" alt="CANOG"/><span>GESTÃO</span></div><small className="side-note">CONTROLE OPERACIONAL</small><nav>{nav.map(([n,I])=><button className={page===n?'active':''} key={n} onClick={()=>{setPage(n);setMenu(false);setError('');setMessage('')}}><I size={18}/>{n}</button>)}</nav><div className="sidebar-bottom"><button onClick={logout}><LogOut size={17}/> Sair</button><small>CANOG GESTÃO · PLATAFORMA</small></div></aside><main className="main"><header className="topbar"><button className="menu-button" onClick={()=>setMenu(!menu)}><Menu/></button><span>CANOG Gestão / <b>{page}</b></span><span className="account">Administrador</span></header><div className="content"><div className="page-heading"><div><small>PAINEL CANOG</small><h1>{page}</h1></div><button className="secondary" onClick={refresh}>Atualizar dados</button></div>{error&&<div className="error">{error}</div>}{message&&<div className="success">{message}</div>}
{page==='Dashboard'&&<><div className="stats">{[['Contratos ativos',dash.active_contracts,'active'],['Rascunhos',dash.draft_contracts,'draft'],['Recebido',money(dash.received_cents),null],['A receber',money(dash.outstanding_cents),null],['Parcelas vencidas',dash.overdue_count,'overdue'],['Comprovantes para conferir',dash.pending_proofs,'proofs']].map(([k,v,target])=>target?<button type="button" className="stat" key={k} onClick={()=>openDashboardCard(target)} title={`Abrir ${k.toLowerCase()}`} style={{cursor:'pointer',textAlign:'left',font:'inherit',color:'inherit',width:'100%',transition:'transform .15s,border-color .15s',border:'1px solid #27719b'}} onMouseEnter={e=>{e.currentTarget.style.transform='translateY(-3px)';e.currentTarget.style.borderColor='#29d3b1'}} onMouseLeave={e=>{e.currentTarget.style.transform='';e.currentTarget.style.borderColor='#27719b'}}><small>{k} ↗</small><strong>{v??0}</strong></button>:<div className="stat" key={k}><small>{k}</small><strong>{v??0}</strong></div>)}</div>
<div style={chartGridStyle}>
<section className="panel" style={{minWidth:0}}><h2>Parcelas a receber por vencimento</h2><p>Valores nominais das parcelas ainda não quitadas, por mês.</p><MiniBars items={dueByMonth.slice(-12)}/></section>
<section className="panel" style={{minWidth:0}}><h2>Recebido x a receber</h2><p>Distribuição dos valores financeiros consolidados no sistema.</p><div style={{display:'flex',alignItems:'center',justifyContent:'center',gap:24,flexWrap:'wrap',padding:'18px 0'}}><div style={{position:'relative',width:168,height:168,flexShrink:0}}><svg viewBox="0 0 120 120" width="168" height="168" role="img" aria-label={`Recebido ${receivedPercent.toFixed(1)}% do total`}><circle cx="60" cy="60" r="46" fill="none" stroke="#27425b" strokeWidth="15"/><circle cx="60" cy="60" r="46" fill="none" stroke="#29d3b1" strokeWidth="15" strokeDasharray={`${receivedPercent/100*289.027} 289.027`} transform="rotate(-90 60 60)"/></svg><div style={{position:'absolute',inset:0,display:'flex',alignItems:'center',justifyContent:'center',flexDirection:'column'}}><strong style={{fontSize:25}}>{receivedPercent.toLocaleString('pt-BR',{maximumFractionDigits:1})}%</strong><small>recebido</small></div></div><div style={{display:'grid',gap:12}}><div><span style={{color:'#29d3b1'}}>●</span> Recebido<br/><strong>{money(receivedAmount)}</strong></div><div><span style={{color:'#7894b3'}}>●</span> A receber<br/><strong>{money(outstandingAmount)}</strong></div></div></div></section>
<section className="panel" style={{minWidth:0}}><h2>Situação das parcelas</h2><p>Quantidade de parcelas por situação atual.</p><div style={{display:'grid',gap:16,padding:'18px 0'}}>{installmentGroups.map(g=><div key={g.label}><div style={{display:'flex',justifyContent:'space-between',gap:12,marginBottom:6}}><span>{g.label}</span><strong>{g.count}</strong></div><div style={{height:13,borderRadius:8,background:'#243b52',overflow:'hidden'}}><div style={{height:'100%',width:`${installments.length?g.count/installments.length*100:0}%`,background:g.color,borderRadius:8}}/></div></div>)}</div><small>Total de parcelas: {installments.length}</small></section>
<section className="panel" style={{minWidth:0}}><h2>Recebimentos registrados por mês</h2><p>Parcelas quitadas com data de pagamento registrada. Valores históricos sem data individual não aparecem aqui.</p><MiniBars items={paidByMonth.slice(-12)} empty="Ainda não há pagamentos quitados com data individual registrada."/></section>
</div><section className="panel"><h2>Visão da operação</h2><p>Indicadores calculados a partir dos registros persistidos. Valores financeiros consolidados e parcelas podem seguir critérios distintos; confira os lançamentos históricos quando necessário.</p></section></>}

{page==='Clientes e fiadores'&&<section className="panel"><h2>Conferência da migração histórica</h2><p>Selecione a planilha CANOG para analisar vendas e parcelas. Confira a prévia e depois importe as vendas e parcelas. Registros sem histórico de pagamento serão considerados em aberto.</p><input type="file" accept=".xlsx" onChange={e=>{setHistoryFile(e.target.files?.[0]||null);setHistoryPreview(null)}}/><div className="actions"><button type="button" className="secondary" disabled={!historyFile||historyBusy} onClick={previewHistory}>{historyBusy?'Analisando...':'Conferir vendas e parcelas'}</button></div>{historyPreview&&<div className="actions"><button type="button" className="primary" disabled={historyBusy||historyPreview.sales_with_errors>0||historyPreview.installments_with_errors>0||historyPreview.projection_warnings?.length>0} onClick={confirmHistory}>{historyBusy?'Importando...':'Importar vendas e parcelas'}</button></div>}{historyPreview&&<><p><b>{historyPreview.sales_total}</b> vendas · <b>{historyPreview.installments_total}</b> parcelas · <b>{historyPreview.partial_payments}</b> pagamentos parciais · <b>{historyPreview.sales_with_errors}</b> vendas com pendências · <b>{historyPreview.installments_with_errors}</b> parcelas com pendências.</p><p>{historyPreview.notice}</p><h3>Projeção de todas as parcelas</h3><p><b>{historyPreview.projected_total??0}</b> parcelas previstas, sendo <b>{historyPreview.projected_missing??0}</b> geradas pelas condições das vendas. Valores estimados em atraso: <b>{money(historyPreview.projected_overdue_cents)}</b> · A vencer: <b>{money(historyPreview.projected_future_cents)}</b> · Excedentes a conferir: <b>{money(historyPreview.projected_excess_cents)}</b>.</p><p><small>Valores calculados com base na planilha, sem histórico completo de quitação. Nenhuma alteração no banco foi realizada.</small></p>{historyPreview.projection_warnings?.map((w,i)=><p className="error" key={i}>{w}</p>)}<div className="table-scroll"><table><thead><tr><th>Venda</th><th>Parcela</th><th>Vencimento</th><th>Valor</th><th>Pago registrado</th><th>Saldo estimado</th><th>Origem</th></tr></thead><tbody>{historyPreview.projected_installments?.map(p=><tr key={p.sale_id+'-'+p.number}><td>{p.sale_id}</td><td>{p.number}</td><td>{p.due}</td><td>{money(p.amount_cents)}</td><td>{money(p.paid_cents)}</td><td>{money(p.open_cents)}</td><td>{p.source==='planilha'?'Lançada':'Projetada'}</td></tr>)}</tbody></table></div><h3>Vendas</h3><div className="table-scroll"><table><thead><tr><th>Nº</th><th>Cliente</th><th>IMEI</th><th>Validação</th></tr></thead><tbody>{historyPreview.sales.map(x=><tr key={x.line}><td>{x.sale_id}</td><td>{x.customer}</td><td>{x.imei}</td><td>{[...x.errors,...x.warnings].join('; ')||'Pronto para conferência'}</td></tr>)}</tbody></table></div><h3>Parcelas</h3><div className="table-scroll"><table><thead><tr><th>Venda</th><th>Parcela</th><th>Valor</th><th>Pago</th><th>Validação</th></tr></thead><tbody>{historyPreview.installments.map(x=><tr key={x.line}><td>{x.sale_id}</td><td>{x.number}</td><td>{money(x.amount_cents)}</td><td>{money(x.paid_cents)}</td><td>{[...x.errors,...x.warnings].join('; ')||'Conferido'}</td></tr>)}</tbody></table></div></>}</section>}
{page==='Clientes e fiadores'&&<><section className="panel"><h2>Novo cadastro</h2><form className="form-grid" onSubmit={submitCustomer}>{field('Nome completo','name')}{field('CPF (11 dígitos)','cpf')}{field('Telefone','phone')}{field('E-mail','email','email')}{field('Endereço','address')}<button className="primary">Cadastrar pessoa</button></form></section><section className="panel"><h2>Pessoas cadastradas ({customers.length})</h2><div className="table-scroll"><table><thead><tr><th>Nome</th><th>CPF</th><th>Contato</th></tr></thead><tbody>{customers.map(c=><tr key={c.id}><td>{c.name}</td><td>{c.cpf}</td><td>{c.phone}</td></tr>)}</tbody></table></div></section></>}
{page==='Estoque'&&<><section className="panel"><h2>Importar estoque da planilha</h2><p>Selecione a planilha CANOG (.xlsx), confira a prévia e confirme. IMEIs existentes não serão alterados.</p><input type="file" accept=".xlsx" onChange={e=>{setInventoryFile(e.target.files?.[0]||null);setInventoryPreview(null)}}/><div className="actions"><button type="button" className="secondary" disabled={!inventoryFile||inventoryBusy} onClick={()=>inventoryImport('preview')}>{inventoryBusy?'Aguarde...':'Conferir planilha'}</button>{inventoryPreview&&<button type="button" className="primary" disabled={inventoryBusy||inventoryPreview.ready===0} onClick={()=>{if(window.confirm('Importar '+inventoryPreview.ready+' aparelhos? Os registros existentes serão preservados.'))inventoryImport('confirm')}}>Confirmar importação ({inventoryPreview.ready})</button>}</div>{inventoryPreview&&<><p>Linhas: {inventoryPreview.total} · Prontas: {inventoryPreview.ready} · Ignoradas: {inventoryPreview.skipped}</p><div className="table-scroll"><table><thead><tr><th>Linha</th><th>Modelo</th><th>IMEI</th><th>Custo</th><th>Situação</th><th>Validação</th></tr></thead><tbody>{inventoryPreview.rows.map(r=><tr key={r.line}><td>{r.line}</td><td>{r.model} {r.capacity}</td><td>{r.imei}</td><td>{money(r.cost_cents)}</td><td>{statusPt(r.status)}</td><td>{r.errors.length?r.errors.join('; '):'Pronto'}</td></tr>)}</tbody></table></div></>}</section><section className="panel"><h2>Cadastrar aparelho</h2><form className="form-grid" onSubmit={submitDevice}>{field('Modelo','model')}{field('IMEI (15 dígitos)','imei')}{field('Custo em R$','cost','number')}{field('Capacidade','capacity')}{field('Cor','color')}<button className="primary">Salvar aparelho</button></form></section><section className="panel"><h2>Estoque ({devices.length})</h2><div className="table-scroll"><table><thead><tr><th>Modelo</th><th>IMEI</th><th>Custo</th><th>Status</th></tr></thead><tbody>{devices.map(d=><tr key={d.id}><td>{d.model} {d.capacity}</td><td>{d.imei}</td><td>{money(d.cost_cents)}</td><td>{statusPt(d.status)}</td></tr>)}</tbody></table></div></section></>}

{page === 'Simulador' && (() => {
  const modalidade = sim.mode === 'negotiated' ? 'tabelada' : 'negociada';
  const entrada = Number(sim.entry_cents || 0) / 100;
  const venda = Number(sim.price_cents || 0) / 100;
  const custo = Number(sim.cost_cents || 0) / 100;
  const troca = Number(sim.trade_in_cents || 0) / 100;
  const n = Math.max(1, Number(sim.count) || 1);
  const taxa = Number(sim.rate_pct) || 0;
  const parcelaFixa = Number(sim.negotiated_installment_cents || 0) / 100;
  const entradaTotal = entrada + troca;
   const parcelaDesejada = Math.max(0, Number(sim.parcela_desejada_cents || 0) / 100);
   const saldoParaSugestao = Math.max(0, venda - Math.min(venda, entradaTotal));
   const sugestao = (() => {
     if (modalidade !== 'negociada' || parcelaDesejada <= 0 || saldoParaSugestao <= 0) return null;
     const candidatos = [];
     for (let quantidade = 1; quantidade <= 18; quantidade++) {
       const taxaCalculada = (parcelaDesejada * quantidade / saldoParaSugestao - 1) * 100 / quantidade;
       if (taxaCalculada >= 0 && taxaCalculada <= 20) {
         const taxaArredondada = Math.round(taxaCalculada * 100) / 100;
         const parcelaResultante = saldoParaSugestao * (1 + taxaArredondada * quantidade / 100) / quantidade;
         candidatos.push({quantidade, taxa:taxaArredondada, parcela:parcelaResultante, distancia:Math.abs(taxaArredondada - taxa) + Math.abs(quantidade - n) * 0.15});
       }
     }
     candidatos.sort((a,b) => a.distancia - b.distancia);
     return candidatos[0] || null;
   })();

  const calculo = calcularNegociacao({
    custo,
    venda,
    entrada: entradaTotal,
    parcelas: n,
    juros: taxa,
    modalidade,
    parcelaFixa
  });

  const reais = valor => Number(valor || 0).toLocaleString(
    'pt-BR',
    {style: 'currency', currency: 'BRL'}
  );

  const atualizar = (campo, valor) => {
    setSim(anterior => ({...anterior, [campo]: valor}));
  };

  const campoDinheiro = (titulo, campo) => (
    <label>
      {titulo}
      <input
        type="number"
        min="0"
        step="0.01"
        value={(Number(sim[campo]) || 0) / 100}
        onChange={e => atualizar(
          campo,
          Math.round(Number(e.target.value) * 100)
        )}
      />
    </label>
  );

  const indicador = (titulo, valor) => (
    <div className="stat" key={titulo}>
      <small>{titulo}</small>
      <strong>{valor}</strong>
    </div>
  );

  const percentualEntrada = venda > 0
    ? entradaTotal / venda * 100
    : 0;

  const periodo = sim.periodo || 'Mensal';
  const diluicao = sim.diluicao || 1;
  const fluxoEntrada = calcularFluxoEntrada({custo, entradaDinheiro:entrada, troca,
    diluicao, parcelas:n, valorParcela:calculo.valorParcela});

     const transferirParaContrato = () => {
     const dinheiroCent = Math.round(Math.max(0, entrada) * 100);
     const trocaCent = Math.round(Math.max(0, troca) * 100);
     const parcelaCent = Math.round(Math.max(0, calculo.valorParcela) * 100);
     const qtd = Math.max(1, Math.min(18, Math.round(n)));
     setForm(anterior => ({...anterior,
       count: String(qtd), installment: (parcelaCent / 100).toFixed(2),
       entry: (dinheiroCent / 100).toFixed(2), trade: (trocaCent / 100).toFixed(2)
     }));
     setSimContractDraft({diluicao: Number(diluicao), periodo, modalidade,
       count:qtd, installment_cents:parcelaCent, entry_cents:dinheiroCent,
       trade_in_cents:trocaCent});
     setContractStatusFilter('todos');
     setError('');setMessage('Dados da simulação transferidos. Selecione cliente, fiador, aparelho e primeiro vencimento; confira os valores antes de salvar.');
     setPage('Contratos');setMenu(false);
   };

const mensagem = [
    'SIMULAÇÃO CANOG',
    `Produto: ${sim.produto || 'Aparelho'}`,
    `Venda: ${reais(venda)}`,
    `Entrada total: ${reais(entradaTotal)} (${diluicao}x no dinheiro)`,
    `Entrada no ato em dinheiro: ${reais(fluxoEntrada.entradas[0])}`,
    ...fluxoEntrada.entradas.slice(1).map((valor, i) => `Entrada no período ${i + 1}: ${reais(valor)}`),
    `Parcelamento: ${n}x de ${reais(calculo.valorParcela)}`,
    `Periodicidade: ${periodo}`,
    `Total previsto: ${reais(calculo.totalRecebido)}`,
    'Condições sujeitas a confirmação.'
  ].join('\n');

  return (
    <div style={{display:'grid', gap:18}}>
      <section className="panel">
        <h2>Simulador de Negociação</h2>
        <p>Configure a proposta e acompanhe os resultados em tempo real.</p>

        <div className="actions" style={{flexWrap:'wrap'}}>
          <button
            type="button"
            className={modalidade === 'negociada' ? 'primary' : 'secondary'}
            onClick={() => atualizar('mode', 'price')}
          >
            Negociada
          </button>
          <button
            type="button"
            className={modalidade === 'tabelada' ? 'primary' : 'secondary'}
            onClick={() => atualizar('mode', 'negotiated')}
          >
            Tabelada
          </button>
        </div>

        <div className="form-grid">
          <label>
            Nome do produto
            <input
              placeholder="Ex.: iPhone 13 128GB"
              value={sim.produto || ''}
              onChange={e => atualizar('produto', e.target.value)}
            />
          </label>

          <label>
            Periodicidade
            <select
              value={periodo}
              onChange={e => atualizar('periodo', e.target.value)}
            >
              <option>Mensal</option>
              <option>Semanal</option>
              <option>Diária</option>
            </select>
          </label>

          {campoDinheiro('Custo do aparelho (R$)', 'cost_cents')}
          {campoDinheiro('Valor de venda (R$)', 'price_cents')}
          {campoDinheiro('Entrada em dinheiro (R$)', 'entry_cents')}
          {campoDinheiro('Aparelho recebido na troca (R$)', 'trade_in_cents')}

          <label>
            Entrada diluída
            <select
              value={diluicao}
              onChange={e => atualizar('diluicao', Number(e.target.value))}
            >
              <option value={1}>1x</option>
              <option value={2}>2x</option>
              <option value={3}>3x</option>
            </select>
          </label>

          <label>
            Quantidade de parcelas
            <input
              type="number"
              min="1"
              max="18"
              step="1"
              value={sim.count}
              onChange={e => atualizar(
                'count',
                Math.min(18, Math.max(1, Number(e.target.value) || 1))
              )}
            />
          </label>

          {modalidade === 'negociada' ? (
            <label>
              Juros por período (%)
              <input
                type="number"
                min="0"
                max="100"
                step="0.01"
                value={sim.rate_pct}
                onChange={e => atualizar('rate_pct', Number(e.target.value))}
              />
            </label>
          ) : campoDinheiro(
            'Valor fixo da parcela (R$)',
            'negotiated_installment_cents'
          )}
        </div>

        <p>
          Entrada total: <b>{reais(entradaTotal)}</b> — {' '}
          {percentualEntrada.toFixed(1)}% da venda
        </p>

        <div className="actions" style={{flexWrap:'wrap'}}>
          {[20, 35, 50, 70].map(p => (
            <button
              key={p}
              type="button"
              className="secondary"
              onClick={() => {
                atualizar('entry_cents', Math.round(venda * p * 10));
              }}
            >
              Entrada {p}%
            </button>
          ))}
        </div>

         {modalidade === 'negociada' && (
           <div style={{margin:'18px 0',padding:16,border:'1px solid #27719b',borderRadius:10}}>
             <h3 style={{marginTop:0}}>Valor da parcela desejado</h3>
             <p>Informe quanto o cliente deseja pagar por período. O sistema sugere de 1 a 18 parcelas, com juros simples de 0% a 20% por período.</p>
             <div className="form-grid">
               {campoDinheiro('Parcela desejada (R$)', 'parcela_desejada_cents')}
               <div style={{display:'flex',alignItems:'flex-end'}}>
                 <button type="button" className="primary" disabled={!sugestao} onClick={() => {
                   if (!sugestao) return;
                   setSim(anterior => ({...anterior,count:sugestao.quantidade,rate_pct:sugestao.taxa}));
                 }}>Aplicar sugestão</button>
               </div>
             </div>
             {sugestao ? (
               <p role="status">Sugestão: <b>{sugestao.quantidade}x de {reais(sugestao.parcela)}</b> com juros de <b>{sugestao.taxa.toFixed(2)}% por período</b>. Clique em Aplicar sugestão para atualizar o cálculo.</p>
             ) : parcelaDesejada > 0 ? (
               <p role="status">Não há combinação possível de 1 a 18 parcelas com juros entre 0% e 20% para esse valor. Ajuste a parcela desejada ou a entrada.</p>
             ) : (
               <p><small>Preencha a parcela desejada para receber uma sugestão.</small></p>
             )}
             <small>A sugestão é aproximada e considera juros simples. A taxa é calculada por período (mensal, semanal ou diário, conforme selecionado), sem conversão automática entre periodicidades.</small>
           </div>
         )}

        <h3>Parcelamento</h3>
        <div className="actions" style={{flexWrap:'wrap'}}>
          {[1, 3, 6, 9, 12, 15, 18].map(q => (
            <button
              key={q}
              type="button"
              className={n === q ? 'primary' : 'secondary'}
              onClick={() => atualizar('count', q)}
            >
              {q}x
            </button>
          ))}
        </div>

        {modalidade === 'negociada' && (
          <>
            <h3>Taxas rápidas</h3>
            <div className="actions" style={{flexWrap:'wrap'}}>
              {[3, 5, 8, 10, 12].map(t => (
                <button
                  key={t}
                  type="button"
                  className={taxa === t ? 'primary' : 'secondary'}
                  onClick={() => atualizar('rate_pct', t)}
                >
                  {t}%
                </button>
              ))}
            </div>
          </>
        )}
      </section>

      <section className="panel">
        <h2>Resultado da negociação</h2>

        <div className="highlight">
          {reais(calculo.valorParcela)}
          <small> por parcela {periodo.toLowerCase()}</small>
        </div>

        <div className="stats">
          {indicador('Capital a recuperar após o ato', reais(fluxoEntrada.capitalInicial))}
          {indicador('Lucro bruto projetado', reais(calculo.lucroBruto))}
          {indicador('Saldo financiado', reais(calculo.saldo))}
          {indicador('Total de juros', reais(calculo.totalJuros))}
          {indicador('Total da negociação', reais(calculo.totalRecebido))}
          {indicador('ROI projetado (sobre capital inicial)', fluxoEntrada.capitalInicial > 0 ? `${(calculo.lucroBruto / fluxoEntrada.capitalInicial * 100).toFixed(1)}%` : 'N/A')}
          {indicador('Margem bruta', `${calculo.margem.toFixed(1)}%`)}
          {indicador(
            'Payback estimado',
            fluxoEntrada.payback === null ? 'Não recuperado no prazo' : `${fluxoEntrada.payback.toFixed(1)} períodos`
          )}
        </div>

        {modalidade === 'tabelada' && (
          <p>
            Taxa implícita por período: {' '}
            <b>{calculo.jurosImplicitos.toFixed(2)}%</b>
          </p>
        )}

        <h3>Entrada diluída — cronograma</h3>
        <p>O aparelho recebido na troca é considerado no ato pelo valor informado. A entrada em dinheiro é dividida em {diluicao}x: a primeira parte no ato e as demais nos primeiros vencimentos.</p>
        <div className="table-scroll"><table><thead><tr><th>Momento</th><th>Entrada em dinheiro</th><th>Parcela normal</th><th>Recebimento econômico acumulado</th></tr></thead><tbody>
          <tr><td>No ato</td><td>{reais(fluxoEntrada.entradas[0])}</td><td>—</td><td>{reais(fluxoEntrada.recebimentoInicial)}</td></tr>
          {fluxoEntrada.fluxo.map(item => <tr key={item.periodo}><td>Período {item.periodo}</td><td>{reais(item.entrada)}</td><td>{reais(item.parcela)}</td><td>{reais(item.acumulado)}</td></tr>)}
        </tbody></table></div>
        <h3>Recuperação do capital</h3>
        <p>{fluxoEntrada.payback === null
          ? 'O custo não é recuperado dentro do cronograma simulado.'
          : fluxoEntrada.payback === 0
            ? 'Custo recuperado no ato da negociação.'
            : `Recuperação estimada no período ${Math.ceil(fluxoEntrada.payback)} (${fluxoEntrada.payback.toFixed(1)} períodos), considerando todos os recebimentos previstos.`}</p>
        <div style={{display:'flex',alignItems:'flex-end',gap:8,minHeight:150,overflowX:'auto',padding:'12px 0'}}>
          {fluxoEntrada.fluxo.map(item => <div key={item.periodo}
            title={`Período ${item.periodo}: ${reais(item.recuperado)} do custo recuperados`}
            style={{flex:'1 0 28px',display:'flex',flexDirection:'column',alignItems:'center',gap:6}}>
            <div style={{height:Math.max(5,custo > 0 ? item.recuperado / custo * 110 : 110),width:'75%',borderRadius:'5px 5px 0 0',background:'#29d3b1'}}/>
            <small>{item.periodo}</small>
          </div>)}
        </div>
        <p><small>Simulação ilustrativa de juros simples. A diluição altera o momento dos recebimentos, não o valor total da entrada, os juros ou o valor das parcelas normais. O ROI utiliza o capital a recuperar após o ato; o aparelho de troca é tratado como valor econômico, não como dinheiro em caixa. Não considera inadimplência, despesas operacionais, impostos ou desvalorização do aparelho recebido. O cronograma não é automaticamente transferido para contratos.</small></p>

        <button
          type="button"
          className="primary"
                   <div className="actions" style={{flexWrap:'wrap',marginBottom:14}}>
           <button type="button" className="primary" onClick={transferirParaContrato}>Gerar contrato — preencher rascunho</button>
         </div>
onClick={() => window.open(
            'https://wa.me/?text=' + encodeURIComponent(mensagem),
            '_blank',
            'noopener,noreferrer'
          )}
        >
          Compartilhar proposta pelo WhatsApp
          <ExternalLink size={15}/>
        </button>
      </section>
    </div>
  );
})()}
{page==='Contratos'&&<><section className="panel"><h2>Nova negociação / rascunho</h2>{simContractDraft&&<div role="status" style={{padding:12,border:'1px solid #27719b',borderRadius:8,marginBottom:12}}><b>Dados importados do simulador</b><p>{simContractDraft.count}x de {money(simContractDraft.installment_cents)} · Entrada em dinheiro {money(simContractDraft.entry_cents)} · Troca {money(simContractDraft.trade_in_cents)} · Entrada diluída {simContractDraft.diluicao}x · Periodicidade {simContractDraft.periodo}.</p>{simContractDraft.diluicao>1?<p className="error">Atenção: o cadastro atual ainda não registra os vencimentos da entrada diluída. O salvamento fica bloqueado para 2x e 3x até a integração do backend, evitando cobranças duplicadas ou antecipadas.</p>:simContractDraft.periodo!=='Mensal'?<p>Confira a periodicidade: o cadastro de contratos atual não recebe esse parâmetro da simulação.</p>:<p>Confira cliente, fiador, aparelho e data do primeiro vencimento antes de salvar.</p>}<button type="button" className="secondary" onClick={()=>{setSimContractDraft(null);setMessage('');setError('')}}>Desvincular simulação</button></div>}<form className="form-grid" onSubmit={submitContract}>{sel('Cliente','customer_id',customers)}{sel('Fiador','guarantor_id',customers)}{sel('Aparelho','device_id',devices.filter(d=>d.status==='available'))}{field('Quantidade de parcelas','count','number')}{field('Valor da parcela (R$)','installment','number')}{field('Entrada em dinheiro (R$)','entry','number')}{field('Entrada em aparelho (R$)','trade','number')}{field('Valor residual (R$)','residual','number')}{field('Primeiro vencimento','due','date')}<button className="primary">Salvar rascunho</button></form></section><section className="panel"><h2>Contratos ({contracts.filter(c=>contractStatusFilter==='todos'||c.status===contractStatusFilter).length})</h2><div className="actions" style={{alignItems:'center',flexWrap:'wrap'}}><label>Situação <select value={contractStatusFilter} onChange={e=>setContractStatusFilter(e.target.value)}><option value="todos">Todos os contratos</option><option value="active">Ativos</option><option value="draft">Rascunhos</option><option value="closed">Encerrados</option><option value="cancelled">Cancelados</option></select></label><button type="button" className="secondary" onClick={()=>setContractStatusFilter('todos')}>Limpar filtro</button><button type="button" className="secondary" onClick={()=>setPage('Dashboard')}>← Voltar ao Dashboard</button></div>{legalStatus&&<div className="error" role="status"><b>Diagnóstico contratual {legalStatus.id.slice(0,8)}</b><p>Revisão jurídica obrigatória. Este diagnóstico não autoriza assinatura.</p><p>Campos obrigatórios ausentes: {legalStatus.missing_contract_data?.join(', ')||'nenhum'}</p><p>Marcadores não resolvidos: {legalStatus.unresolved_tokens?.join(', ')||'nenhum'}</p><p>Campos genéricos no modelo: {legalStatus.legacy_placeholders?.length||0}</p></div>}{legalContract&&<section className="panel"><h3>Dados complementares do contrato {legalContract.slice(0,8)}</h3><p>Preencha somente com informações conferidas. O documento gerado exige revisão jurídica antes da assinatura.</p><form className="form-grid" onSubmit={e=>{e.preventDefault();act(async()=>{await req('/contracts/'+legalContract+'/legal-details',{method:'PUT',body:{...legalForm,activation_fee_cents:Math.round(Number(legalForm.activation_fee||0)*100)}});setLegalContract('');setLegalForm({})})}}>{[['CEP do cliente','customer_postal_code','text'],['Estado civil do cliente','customer_marital_status','text'],['Profissão do cliente','customer_occupation','text'],['CEP do fiador','guarantor_postal_code','text'],['Taxa de ativação (R$)','activation_fee','number'],['Data do contrato','contract_date','date'],['Data de término','contract_end_date','date'],['Data da vistoria','inspection_date','date']].map(([label,key,type])=><label key={key}>{label}<input required type={type} min={type==='number'?'0':undefined} step={type==='number'?'0.01':undefined} value={legalForm[key]||''} onChange={e=>setLegalForm({...legalForm,[key]:e.target.value})}/></label>)}<button className="primary">Salvar dados jurídicos</button><button type="button" className="secondary" onClick={()=>setLegalContract('')}>Cancelar</button></form></section>}{inspectionContract&&<section className="panel"><h3>Vistoria digital — contrato {inspectionContract.slice(0,8)}</h3><p>Registre o estado real do aparelho. Este registro não substitui as assinaturas exigidas no Anexo I.</p><form onSubmit={e=>{e.preventDefault();act(async()=>{await req('/contracts/'+inspectionContract+'/inspection',{method:'PUT',body:{checks:inspection.checks,observations:inspection.observations,accessories:inspection.accessories}});setInspectionContract('')})}}><div className="form-grid">{inspectionFields.map(([key,label])=><label key={key}>{label}<select required value={inspection.checks?.[key]||''} onChange={e=>setInspection({...inspection,checks:{...inspection.checks,[key]:e.target.value}})}><option value="">Selecione</option><option value="ok">Conforme</option><option value="issue">Com problema</option><option value="not_tested">Não testado</option></select></label>)}</div><label>Acessórios entregues<input maxLength={500} value={inspection.accessories||''} onChange={e=>setInspection({...inspection,accessories:e.target.value})}/></label><label>Observações e problemas<textarea maxLength={4000} value={inspection.observations||''} onChange={e=>setInspection({...inspection,observations:e.target.value})}/></label><div className="actions"><button className="primary">Salvar vistoria</button><button type="button" className="secondary" onClick={()=>setInspectionContract('')}>Cancelar</button></div></form></section>}{contracts.filter(c=>contractStatusFilter==='todos'||c.status===contractStatusFilter).map(c=><div className="record" key={c.id}><div><b>Contrato {c.id.slice(0,8)}</b><span>{customers.find(x=>x.id===c.customer_id)?.name||'Cliente'} · {statusPt(c.status)} · {c.installments_count}x {money(c.installment_cents)}</span></div><div className="actions"><button className="secondary" onClick={()=>download('/contracts/'+c.id+'/pdf','ficha-'+c.id+'.pdf')}>Ficha PDF</button><button className="secondary" onClick={async()=>{setLegalStatus(null);try{const x=await req('/contracts/'+c.id+'/legal-readiness');setLegalStatus({id:c.id,...x})}catch(e){setError(e.message)}}}>Verificar contrato</button><button className="secondary" onClick={()=>openInspection(c.id)}>Vistoria digital</button><button className="secondary" onClick={()=>download('/contracts/'+c.id+'/review-copy.pdf','conferencia-'+c.id+'.pdf')}>Cópia para conferência</button>{c.status==='draft'&&<button className="secondary" onClick={()=>{setLegalContract(c.id);setLegalForm({})}}>Dados jurídicos</button>}<button className="secondary" onClick={()=>download('/contracts/'+c.id+'/legal-draft.pdf','minuta-'+c.id+'.pdf')}>Gerar minuta</button><button className="secondary" onClick={()=>{getDocs(c.id);setPage('Documentos')}}>Documentos</button>{c.status==='draft'&&c.trade_in_cents>0&&<button className="secondary" onClick={()=>{const model=window.prompt('Modelo do aparelho recebido:');if(!model)return;const imei=window.prompt('IMEI do aparelho recebido (15 dígitos):');if(!imei)return;act(()=>req('/contracts/'+c.id+'/trade-in',{method:'POST',body:{model,imei,cost_cents:c.trade_in_cents}}))}}>Registrar aparelho de entrada</button>}{c.status==='active'&&<><button className="secondary" onClick={()=>{if(window.confirm('Confirmar devolução do aparelho e encerramento?'))act(()=>req('/contracts/'+c.id+'/close',{method:'POST',body:{action:'return'}}))}}>Registrar devolução</button><button className="primary" onClick={()=>{if(window.confirm('Confirma todas as parcelas quitadas, valor residual recebido e termo de transferência assinado?'))act(()=>req('/contracts/'+c.id+'/close',{method:'POST',body:{action:'acquire',residual_paid:true,transfer_signed:true}}))}}>Transferir propriedade</button></>}{c.status==='draft'&&<><button className="secondary" onClick={()=>act(()=>req('/contracts/'+c.id+'/events',{method:'POST',body:{signed:true,delivered:true}}))}>Registrar assinatura e entrega</button><button className="secondary" onClick={async()=>{try{const x=await req('/contracts/'+c.id+'/checklist');setMessage('Pendências: '+(x.missing_documents.join(', ')||'nenhuma')+' | Assinatura: '+x.signed+' | Entrega: '+x.delivered)}catch(e){setError(e.message)}}}>Ver pendências</button><button className="primary" onClick={()=>act(()=>req('/contracts/'+c.id+'/activate',{method:'POST'}))}>Ativar</button></>}</div></div>)}</section></>}
{page==='Cobranças'&&<section className="panel"><h2>Central de Cobranças</h2><p>Parcelas vencidas de contratos ativos, agrupadas por cliente. Confira o histórico antes de entrar em contato. Nenhuma mensagem é enviada automaticamente.</p><div className="stats"><div className="stat"><small>Clientes com atraso</small><strong>{collectionRows.length}</strong></div><div className="stat"><small>Valor registrado em atraso</small><strong>{money(collectionAmount)}</strong></div></div><div className="form-grid"><label>Buscar cliente, telefone ou contrato<input value={collectionSearch} onChange={e=>setCollectionSearch(e.target.value)} placeholder="Nome, telefone ou contrato"/></label><label>Ordenar por<select value={collectionOrder} onChange={e=>setCollectionOrder(e.target.value)}><option value="dias">Maior atraso</option><option value="valor">Maior valor</option><option value="nome">Nome do cliente</option></select></label><button type="button" className="secondary" onClick={()=>{setCollectionSearch('');setCollectionOrder('dias')}}>Limpar filtros</button></div>{collectionRows.length===0?<p>Nenhuma cobrança encontrada para os filtros atuais.</p>:collectionRows.map(g=><div className="record" key={g.key} style={{alignItems:'flex-start',gap:16}}><div style={{flex:'1 1 280px',minWidth:0}}><b>{g.customer?.name||'Cliente não identificado'}</b><span>Telefone: {g.customer?.phone||'Não cadastrado'} · {g.items.length} parcela(s) vencida(s) · {g.days} dia(s) de atraso</span><span>Valor registrado em aberto: <b>{money(g.amount)}</b></span><div style={{marginTop:8}}>{g.items.slice().sort((a,b)=>String(a.due_at).localeCompare(String(b.due_at))).map(p=><small key={p.id} style={{display:'block',marginBottom:5}}>Contrato {p.contract_id.slice(0,8)} · Parcela {p.number} · {dateOnly(p.due_at).split('-').reverse().join('/')} · {money(p.open_cents??p.remaining_cents??p.balance_cents??p.amount_cents)}</small>)}</div></div><div className="actions" style={{flexWrap:'wrap'}}><button type="button" className="primary" onClick={()=>collectionWhatsapp(g)}>Cobrar pelo WhatsApp</button><button type="button" className="secondary" onClick={()=>beginCollectionRecord(g)}>Registrar cobrança</button>{[...g.contracts].map(id=><button type="button" className="secondary" key={id} onClick={()=>openContract(id)}>Contrato {id.slice(0,8)}</button>)}</div></div>)}<div style={{marginTop:22}}><h2>Histórico de cobranças</h2><p>Registros salvos no sistema. Abrir o WhatsApp não registra automaticamente um envio.</p>{collectionHistory.length===0?<p>Nenhuma cobrança registrada até o momento.</p>:<div className="table-scroll"><table><thead><tr><th>Data</th><th>Cliente</th><th>Contrato</th><th>Canal</th><th>Resultado</th><th>Próximo retorno</th><th>Observações</th></tr></thead><tbody>{collectionHistory.filter(h=>!collectionSearch.trim()||[customersById.get(h.customer_id)?.name,h.contract_id].some(v=>String(v||'').toLocaleLowerCase('pt-BR').includes(collectionSearch.trim().toLocaleLowerCase('pt-BR')))).map(h=><tr key={h.id}><td>{new Date(h.created_at).toLocaleString('pt-BR')}</td><td>{customersById.get(h.customer_id)?.name||'Cliente'}</td><td>{h.contract_id?<button type="button" className="secondary" onClick={()=>openContract(h.contract_id)}>{h.contract_id.slice(0,8)}</button>:'—'}</td><td>{channelNames[h.channel]||h.channel}</td><td>{outcomeNames[h.outcome]||h.outcome}</td><td>{h.follow_up_date?dateOnly(h.follow_up_date).split('-').reverse().join('/'):'—'}</td><td style={{whiteSpace:'pre-wrap',minWidth:160}}>{h.notes||'—'}</td></tr>)}</tbody></table></div>}</div>{historyCustomer&&<section className="panel" style={{marginTop:20}}><h3>Registrar cobrança — {customersById.get(historyCustomer)?.name||'Cliente'}</h3><form onSubmit={saveCollectionRecord}><div className="form-grid"><label>Contrato<select value={historyForm.contract_id} onChange={e=>setHistoryForm({...historyForm,contract_id:e.target.value})}><option value="">Sem contrato específico</option>{contracts.filter(c=>c.customer_id===historyCustomer).map(c=><option key={c.id} value={c.id}>{c.id.slice(0,8)}</option>)}</select></label><label>Canal<select value={historyForm.channel} onChange={e=>setHistoryForm({...historyForm,channel:e.target.value})}><option value="whatsapp">WhatsApp</option><option value="phone">Ligação</option><option value="other">Outro</option></select></label><label>Resultado<select value={historyForm.outcome} onChange={e=>setHistoryForm({...historyForm,outcome:e.target.value})}><option value="no_reply">Sem resposta</option><option value="promise">Promessa de pagamento</option><option value="negotiation">Negociação</option><option value="payment_reported">Pagamento informado</option><option value="contacted">Contato realizado</option><option value="other">Outro</option></select></label><label>Próximo retorno (opcional)<input type="date" value={historyForm.follow_up_date} onChange={e=>setHistoryForm({...historyForm,follow_up_date:e.target.value})}/></label></div><label>Observações<textarea maxLength={2000} value={historyForm.notes} onChange={e=>setHistoryForm({...historyForm,notes:e.target.value})} placeholder="Registre o que aconteceu no contato"/></label><div className="actions"><button type="submit" className="primary" disabled={historySaving}>{historySaving?'Salvando...':'Salvar no histórico'}</button><button type="button" className="secondary" onClick={()=>setHistoryCustomer('')}>Cancelar</button></div></form></section>}</section>}
{page==='Financeiro'&&<section className="panel"><h2>Parcelas</h2><div className="actions"><button type="button" className="secondary" onClick={()=>setPage('Dashboard')}>← Voltar ao Dashboard</button></div>{financeProofOnly&&<p>Exibindo somente comprovantes enviados e aguardando conferência.</p>}<div className="form-grid"><label>Buscar cliente ou contrato<input value={financeSearch} onChange={e=>setFinanceSearch(e.target.value)} placeholder="Nome, contrato ou parcela"/></label><label>Situação<select value={financeStatus} onChange={e=>{setFinanceStatus(e.target.value);setFinanceProofOnly(false)}}><option value="todos">Todas</option><option value="pending">Pendente</option><option value="overdue">Em atraso</option><option value="paid">Pago</option><option value="review">Em análise</option><option value="partial">Parcialmente pago</option></select></label><label>Mês de vencimento<input type="month" value={financeMonth} onChange={e=>setFinanceMonth(e.target.value)}/></label><button type="button" className="secondary" onClick={()=>{setFinanceSearch('');setFinanceStatus('todos');setFinanceMonth('');setFinanceProofOnly(false)}}>Limpar filtros</button></div><p><b>{financeRows.length}</b> parcelas encontradas · Total nominal filtrado: <b>{money(financeTotal)}</b></p><div className="table-scroll"><table><thead><tr><th>Contrato</th><th>Parcela</th><th>Vencimento</th><th>Valor</th><th>Situação</th><th>Ação</th></tr></thead><tbody>{financeRows.map(p=><tr key={p.id}><td><button type="button" className="secondary" title="Abrir detalhes do contrato" onClick={()=>openContract(p.contract_id)}>{p.contract_id.slice(0,8)}</button><small style={{display:"block"}}>{contractCustomer(p)}</small></td><td>{p.number}</td><td>{p.due_at.slice(0,10)}</td><td>{money(p.amount_cents)}</td><td>{statusPt(currentStatus(p))}{p.proof_id&&<button className="secondary" onClick={()=>download('/documents/'+p.proof_id+'/download','comprovante')}>Ver comprovante</button>}</td><td>{p.status==='pending'&&<button className="primary" onClick={()=>{if(window.confirm('Você verificou o crédito na conta bancária? Confirmar baixa manual sem comprovante?'))act(()=>req('/installments/'+p.id+'/confirm',{method:'POST'}))}}>Confirmar recebimento manual</button>}{p.status==='review'&&<><button className="primary" onClick={()=>{if(window.confirm('Você conferiu o comprovante E confirmou o crédito na conta bancária?'))act(()=>req('/installments/'+p.id+'/approve-proof',{method:'POST'}))}}>Aprovar comprovante e quitar</button><button className="secondary" onClick={()=>{const reason=window.prompt('Motivo da rejeição do comprovante:');if(reason?.length>=8)act(()=>req('/installments/'+p.id+'/reject-proof',{method:'POST',body:{reason}}))}}>Rejeitar comprovante</button></>}{p.status==='paid'&&<button className="secondary" onClick={()=>{const reason=window.prompt('Motivo do estorno (mínimo 8 caracteres):');if(reason?.length>=8)act(()=>req('/installments/'+p.id+'/reverse',{method:'POST',body:{reason}}))}}>Estornar baixa</button>}</td></tr>)}</tbody></table></div></section>}
{page==='Detalhes do contrato'&&<section className="panel"><div className="actions"><button type="button" className="secondary" onClick={()=>setPage(detailReturnPage)}>← Voltar para {detailReturnPage}</button><button type="button" className="secondary" onClick={refresh}>Atualizar</button></div>{!selectedContract?<p>Contrato não encontrado.</p>:<><h2>Contrato {selectedContract.id.slice(0,8)}</h2><p>Situação: <b>{statusPt(selectedContract.status)}</b></p><h3>Cliente</h3><p><b>{selectedCustomer?.name||'Não informado'}</b> · CPF: {selectedCustomer?.cpf||'Não informado'} · Telefone: {selectedCustomer?.phone||'Não informado'}</p><h3>Aparelho</h3><p>{selectedDevice?`${selectedDevice.model||''} ${selectedDevice.capacity||''} · IMEI: ${selectedDevice.imei||'Não informado'}`:'Aparelho não identificado'} · Custo: {money(selectedDevice?.cost_cents)}</p><h3>Condições do contrato</h3><p>{selectedContract.installments_count} parcelas de {money(selectedContract.installment_cents)} · Entrada: {money(selectedContract.entry_cents)} · Troca: {money(selectedContract.trade_in_cents)}</p><h3>Parcelas vinculadas</h3><div className="table-scroll"><table><thead><tr><th>Nº</th><th>Vencimento</th><th>Valor</th><th>Situação</th></tr></thead><tbody>{installments.filter(p=>p.contract_id===selectedContract.id).sort((a,b)=>a.number-b.number).map(p=><tr key={p.id}><td>{p.number}</td><td>{dateOnly(p.due_at)}</td><td>{money(p.amount_cents)}</td><td>{statusPt(currentStatus(p))}</td></tr>)}</tbody></table></div><div className="actions"><button type="button" className="secondary" onClick={()=>{getDocs(selectedContract.id);setPage('Documentos')}}>Ver documentos</button><button type="button" className="secondary" onClick={()=>download('/contracts/'+selectedContract.id+'/pdf','ficha-'+selectedContract.id+'.pdf')}>Baixar ficha PDF</button></div></>}</section>}
{page==='Documentos'&&<section className="panel"><h2>Documentação contratual</h2><label>Selecionar contrato<select value={selected} onChange={e=>getDocs(e.target.value)}><option value=''>Selecione</option>{contracts.map(c=><option key={c.id} value={c.id}>{c.id.slice(0,8)} — {customers.find(x=>x.id===c.customer_id)?.name}</option>)}</select></label>{selected&&<><form className="form-grid" onSubmit={upload}><label>Categoria<select name="kind">{kinds.map(([k,l])=><option key={k} value={k}>{l}</option>)}</select></label><label>Arquivo<input name="file" type="file" required accept="image/*,.pdf,video/mp4,video/quicktime"/></label><button className="primary">Enviar documento</button></form><h3>Arquivos</h3>{kinds.map(([k,l])=><div className="record" key={k}><b>{l}</b><span>{([...docs].filter(d=>d.kind===k).sort((a,b)=>String(b.created_at||b.id).localeCompare(String(a.created_at||a.id)))[0]?.status==='approved')?'Aprovado':'Pendente de aprovação'}</span></div>)}{docs.map(d=><div className="record" key={d.id}><span>{d.filename} · {statusPt(d.status)}</span><div className="actions"><button className="secondary" onClick={()=>download('/documents/'+d.id+'/download',d.filename)}>Baixar</button>{d.status!=='approved'&&<button className="primary" onClick={async()=>{await act(()=>req('/documents/'+d.id+'/review',{method:'PATCH',body:{status:'approved'}}));getDocs(selected)}}>Aprovar</button>}</div></div>)}</>}</section>}
{page==='Relatórios'&&<section className="panel"><h2>Relatório financeiro</h2><p>Recebimentos, valores a receber e parcelas em atraso são apurados no banco de dados. A margem líquida depende de despesas e conciliação.</p><div className="stats"><div className="stat"><small>Recebido</small><strong>{money(dash.received_cents)}</strong></div><div className="stat"><small>A receber</small><strong>{money(dash.outstanding_cents)}</strong></div><div className="stat"><small>Vencidas</small><strong>{dash.overdue_count||0}</strong></div></div><button className="secondary" onClick={async()=>{try{setDueAlerts(await req('/reports/upcoming-due?days=7'))}catch(e){setError(e.message)}}}>Consultar alertas dos próximos 7 dias</button>{dueAlerts&&<div><h3>Próximos vencimentos: {dueAlerts.upcoming.length} — {money(dueAlerts.upcoming_total_cents)}</h3><h3>Em atraso: {dueAlerts.overdue.length} — {money(dueAlerts.overdue_total_cents)}</h3><div className="table-scroll"><table><thead><tr><th>Contrato</th><th>Parcela</th><th>Vencimento</th><th>Valor</th><th>Grupo</th></tr></thead><tbody>{[...dueAlerts.overdue.map(x=>({...x,group:'Atrasada'})),...dueAlerts.upcoming.map(x=>({...x,group:'A vencer'}))].map(x=><tr key={x.installment_id}><td>{x.contract_id.slice(0,8)}</td><td>{x.number}</td><td>{x.due_date}</td><td>{money(x.amount_cents)}</td><td>{x.group}</td></tr>)}</tbody></table></div></div>}<button className="secondary" onClick={async()=>{try{const data=await req('/reports/financial');setMessage('Investido em aparelhos locados: '+money(data.invested_cents)+' | Em atraso: '+money(data.overdue_cents))}catch(e){setError(e.message)}}}>Consultar resumo detalhado</button></section>}{page==='Configurações'&&<section className="panel"><h2>PIX da loja</h2><form className="form-grid" onSubmit={e=>{e.preventDefault();act(()=>req('/settings',{method:'PUT',body:settings}))}}><label>Chave PIX<input value={settings.pix_key||''} onChange={e=>setSettings({...settings,pix_key:e.target.value})}/></label><label>Nome do recebedor<input value={settings.pix_name||''} onChange={e=>setSettings({...settings,pix_name:e.target.value})}/></label><label>Participação do sócio (%)<input type="number" value={settings.partner_share_pct??20} onChange={e=>setSettings({...settings,partner_share_pct:Number(e.target.value)})}/></label><button className="primary">Salvar configurações</button></form><h3>QR Code PIX</h3><input type="file" accept="image/png,image/jpeg,image/webp" onChange={e=>{const fd=new FormData();fd.append('file',e.target.files[0]);act(()=>req('/settings/pix-qr',{method:'POST',body:fd,formData:true}))}}/><h3>Habilitar acesso ao portal do cliente</h3><form className="form-grid" onSubmit={e=>{e.preventDefault();act(()=>req('/portal/access',{method:'POST',body:{customer_id:form.portal_customer,password:form.portal_password}}))}}>{sel('Cliente','portal_customer',customers)}{field('Senha inicial (mínimo 10 caracteres)','portal_password','password')}<button className="primary">Criar / redefinir acesso</button></form><button className="secondary" onClick={()=>{setPortal(true);setError('')}}>Abrir portal do cliente</button></section>}
</div></main></div>}
createRoot(document.getElementById('root')).render(<App/>);
