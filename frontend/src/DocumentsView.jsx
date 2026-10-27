import { useCallback, useEffect, useRef, useState } from 'react';
import { FileText, UploadCloud, RefreshCw, Loader2, Trash2 } from 'lucide-react';

const shell = { flex: 1, overflowY: 'auto', padding: '30px', color: '#ecf1ff' };
const panel = { maxWidth: 800, margin: '0 auto' };
const block = { background: '#19233e', border: '1px solid rgba(255,255,255,.1)',
  borderRadius: 12, padding: 20, marginTop: 18 };
const buttonStyle = { display:'inline-flex', gap:8, alignItems:'center', padding:'10px 14px',
  background:'#455fe9', color:'#fff', border:0, borderRadius:9, cursor:'pointer' };

export default function DocumentsView({ apiBaseUrl, accessToken }) {
  const [items, setItems] = useState([]);
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [truncated, setTruncated] = useState(false);
  const [toDelete, setToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const fileInput = useRef(null);

  const load = useCallback(async (signal) => {
    if (!apiBaseUrl || !accessToken) return;
    setBusy(true); setError('');
    try {
      const res = await fetch(`${apiBaseUrl}/api/documents`, {
        headers: { Authorization: `Bearer ${accessToken}` }, signal
      });
      const data = await res.json();
      if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : `HTTP ${res.status}`);
      if (!signal?.aborted) {
        setItems(Array.isArray(data.documents) ? data.documents : []);
        setTruncated(Boolean(data.truncated));
      }
    } catch (err) {
      if (err.name !== 'AbortError') setError(err.message || 'No se pudo consultar los documentos');
    } finally {
      if (!signal?.aborted) setBusy(false);
    }
  }, [apiBaseUrl, accessToken]);

  useEffect(() => {
    const ctrl = new AbortController();
    load(ctrl.signal);
    return () => ctrl.abort();
  }, [load]);

  async function upload(event) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    setError(''); setNotice('');
    if (file.size > 256 * 1024) {
      setError('Máximo 256 KB por archivo.'); return;
    }
    if (!/\.(txt|md|pdf)$/i.test(file.name)) {
      setError('Formato no admitido en esta interfaz: utiliza TXT, MD o PDF.'); return;
    }
    if (!apiBaseUrl || !accessToken) { setError('Debes iniciar sesión.'); return; }
    const form = new FormData();
    form.append('file', file);
    setUploading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/api/documents`, {
        method: 'POST', headers: { Authorization: `Bearer ${accessToken}` }, body: form
      });
      const data = await response.json();
      if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : `HTTP ${response.status}`);
      setNotice(`Documento indexado: ${data.name} (${data.chunks} fragmentos).`);
      await load();
    } catch (err) {
      setError(err.message || 'Error al cargar el archivo');
    } finally { setUploading(false); }
  }

  async function removeDocument() {
    if (!toDelete || deleting) return;
    setDeleting(true); setError(''); setNotice('');
    try {
      const res = await fetch(`${apiBaseUrl}/api/documents/${encodeURIComponent(toDelete.document_id)}`, {
        method: 'DELETE', headers: { Authorization: `Bearer ${accessToken}` }
      });
      const data = await res.json();
      if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : `HTTP ${res.status}`);
      setToDelete(null);
      setNotice(`Documento eliminado: ${toDelete.name} (${data.chunks_deleted} fragmentos).`);
      await load();
    } catch (err) {
      setError(err.message || 'No se pudo eliminar el documento');
    } finally { setDeleting(false); }
  }

  return (
    <section style={shell} aria-label="Mis documentos">
      <div style={panel}>
        <h2 style={{ marginBottom: 8 }}>Mis documentos</h2>
        <p style={{ color:'#aab9da', lineHeight:1.6 }}>
          Los archivos que subes son privados y se utilizan en tus consultas al asistente.
          Los documentos empresariales compartidos permanecen disponibles en el chat.
        </p>
        <div style={block}>
          <h3 style={{marginTop:0}}>Cargar documento privado</h3>
          <p style={{color:'#aab9da', fontSize:14}}>Máximo 256 KB. TXT, MD o PDF.</p>
          <input ref={fileInput} type="file" accept=".txt,.md,.pdf"
            onChange={upload} style={{display:'none'}} aria-label="Seleccionar documento" />
          <button type="button" style={buttonStyle} disabled={uploading}
            onClick={() => fileInput.current?.click()}>
            {uploading ? <Loader2 size={18} /> : <UploadCloud size={18} />}
            {uploading ? 'Indexando...' : 'Seleccionar archivo'}
          </button>
        </div>
        {error && <p role="alert" style={{color:'#ffb2b2'}}>{error}</p>}
        {notice && <p role="status" style={{color:'#a0e5c2'}}>{notice}</p>}
        <div style={block}>
          <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', gap:12}}>
            <h3 style={{margin:0}}>Archivos privados ({items.length})</h3>
            <button type="button" onClick={() => load()} disabled={busy || uploading || deleting}
              style={{...buttonStyle, background:'#30436d'}}>
              <RefreshCw size={16} /> Actualizar
            </button>
          </div>
          {busy && <p style={{color:'#aab9da'}}>Consultando documentos...</p>}
          {!busy && items.length === 0 && <p style={{color:'#aab9da'}}>Aún no has cargado documentos privados.</p>}
          {items.map(doc => (
            <div key={doc.document_id} style={{display:'flex', gap:12, padding:'14px 0', borderBottom:'1px solid rgba(255,255,255,.08)'}}>
              <FileText size={20} style={{flexShrink:0}} />
              <div style={{minWidth:0, flex:1}}>
                <strong style={{overflowWrap:'anywhere'}}>{doc.name}</strong>
                <div style={{fontSize:12, color:'#aab9da', marginTop:5}}>
                  {doc.chunks} fragmento(s) · Privado · Indexado
                </div>
              </div>
              <button type="button" aria-label={`Eliminar ${doc.name}`} disabled={deleting || uploading}
                onClick={() => setToDelete(doc)}
                style={{...buttonStyle, marginLeft:'auto', background:'transparent', border:'1px solid #ae5162', color:'#ffc4cc'}}>
                <Trash2 size={16} /> Eliminar
              </button>
            </div>
          ))}
          {toDelete && (
            <div role="alertdialog" aria-modal="true" aria-label="Confirmar eliminación"
              style={{...block, borderColor:'#ae5162'}}>
              <strong>¿Eliminar este documento?</strong>
              <p style={{overflowWrap:'anywhere'}}>Se eliminarán permanentemente los fragmentos de <b>{toDelete.name}</b>.
                Esta acción no elimina las conversaciones guardadas.</p>
              <div style={{display:'flex', justifyContent:'flex-end', gap:10}}>
                <button type="button" disabled={deleting} onClick={() => setToDelete(null)}
                  style={{...buttonStyle, background:'#30436d'}}>Cancelar</button>
                <button type="button" disabled={deleting} onClick={removeDocument}
                  style={{...buttonStyle, background:'#a3374c'}}>
                  {deleting ? 'Eliminando...' : 'Sí, eliminar'}
                </button>
              </div>
            </div>
          )}
          {truncated && <p role="status" style={{color:'#ffdfa1'}}>Listado parcial: se alcanzó el límite de la demo.</p>}
        </div>
      </div>
    </section>
  );
}
