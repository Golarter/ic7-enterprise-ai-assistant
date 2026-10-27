import { useCallback, useEffect, useState } from 'react';
import { MessageSquareText, RefreshCw, Loader2 } from 'lucide-react';

const panel = { maxWidth: 800, margin: '0 auto' };
const card = { background: '#19233e', border: '1px solid rgba(255,255,255,.1)', borderRadius: 12, padding: 18, marginTop: 14 };

export default function ConversationsView({ apiBaseUrl, accessToken, onOpenConversation }) {
  const [items, setItems] = useState([]);
  const [busy, setBusy] = useState(false);
  const [opening, setOpening] = useState('');
  const [error, setError] = useState('');
  const [truncated, setTruncated] = useState(false);

  const load = useCallback(async (signal) => {
    if (!apiBaseUrl || !accessToken) return;
    setBusy(true);
    setError('');
    try {
      const response = await fetch(`${apiBaseUrl}/api/conversations`, {
        headers: { Authorization: `Bearer ${accessToken}` }, signal,
      });
      const body = await response.json();
      if (!response.ok) throw new Error(typeof body.detail === 'string' ? body.detail : `HTTP ${response.status}`);
      if (!signal?.aborted) {
        setItems(Array.isArray(body.conversations) ? body.conversations : []);
        setTruncated(Boolean(body.truncated));
      }
    } catch (e) {
      if (e.name !== 'AbortError' && !signal?.aborted) setError(e.message || 'No se pudieron cargar las conversaciones.');
    } finally {
      if (!signal?.aborted) setBusy(false);
    }
  }, [apiBaseUrl, accessToken]);

  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal);
    return () => controller.abort();
  }, [load]);

  async function open(item) {
    if (!item.session_id || opening) return;
    setOpening(item.session_id);
    setError('');
    try {
      const response = await fetch(`${apiBaseUrl}/api/history/${encodeURIComponent(item.session_id)}`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      const body = await response.json();
      if (!response.ok) throw new Error(typeof body.detail === 'string' ? body.detail : `HTTP ${response.status}`);
      if (!Array.isArray(body)) throw new Error('Formato inesperado del historial.');
      // The API currently returns newest first. Present the messages chronologically.
      const messages = [...body].reverse().flatMap((entry) => ([
        { role: 'user', text: entry.question || '' },
        { role: 'assistant', text: entry.answer || '', sources: entry.sources || [], tools: entry.tools_used || [], traceId: entry.trace_id },
      ]));
      onOpenConversation(item.session_id, messages);
    } catch (e) {
      setError(e.message || 'No se pudo abrir la conversación.');
    } finally {
      setOpening('');
    }
  }

  return (
    <section style={{ flex: 1, overflowY: 'auto', padding: 30, color: '#ecf1ff' }} aria-label="Mis conversaciones">
      <div style={panel}>
        <h2>Mis conversaciones</h2>
        <p style={{ color: '#aab9da' }}>Abre una sesión anterior para consultar sus mensajes y continuar escribiendo en ella.</p>
        <button type="button" disabled={busy || !!opening} onClick={() => load()}
          style={{ background: '#30436d', color: '#fff', border: 0, borderRadius: 9, padding: '10px 14px', cursor: 'pointer', display: 'inline-flex', gap: 8, alignItems: 'center' }}>
          {busy ? <Loader2 size={16} /> : <RefreshCw size={16} />} Actualizar
        </button>
        {error && <p role="alert" style={{ color: '#ffb2b2' }}>{error}</p>}
        {busy && <p style={{ color: '#aab9da' }}>Consultando conversaciones...</p>}
        {!busy && items.length === 0 && <p style={card}>No hay conversaciones indexadas todavía. Las sesiones anteriores a esta función no aparecen automáticamente.</p>}
        {items.map(item => (
          <button key={item.session_id} type="button" disabled={!!opening}
            onClick={() => open(item)} style={{ ...card, display: 'flex', width: '100%', gap: 12, color: '#ecf1ff', textAlign: 'left', cursor: 'pointer', alignItems: 'center' }}>
            {opening === item.session_id ? <Loader2 size={19} /> : <MessageSquareText size={19} />}
            <span style={{ minWidth: 0, flex: 1 }}>
              <strong style={{ display: 'block', overflowWrap: 'anywhere' }}>{item.title || 'Conversación'}</strong>
              <small style={{ color: '#aab9da' }}>{item.updated_at ? `Última actividad: ${item.updated_at}` : 'Sin fecha'}</small>
            </span>
          </button>
        ))}
        {truncated && <p role="status" style={{ color: '#ffdfa1' }}>Listado parcial: se alcanzó el límite de la demo.</p>}
      </div>
    </section>
  );
}
