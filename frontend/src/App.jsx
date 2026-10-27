
import { useState } from 'react';
import { useAuth } from 'react-oidc-context';
import {
  Bot,
  FileText,
  ShieldCheck,
  LogIn,
  LogOut,
  Send,
  CircleHelp,
  Loader2,
  LockKeyhole
} from 'lucide-react';

import './App.css';
import DocumentsView from './DocumentsView.jsx';

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || ''
).replace(/\/+$/, '');

function Workspace() {
  const auth = useAuth();

  const [view, setView] = useState('chat');
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [sessionId, setSessionId] = useState(
    () => crypto.randomUUID()
  );

  const apiReady = Boolean(API_BASE_URL);

  const email =
    auth.user?.profile?.email ||
    auth.user?.profile?.sub ||
    'Usuario';

  async function enviarPregunta(event) {
    event.preventDefault();

    const texto = question.trim();

    if (!texto || sending || !apiReady) {
      return;
    }

    setSending(true);
    setError('');
    setQuestion('');

    setMessages((previous) => [
      ...previous,
      {
        role: 'user',
        text: texto
      }
    ]);

    try {
      const token = auth.user?.access_token;

      if (!token) {
        throw new Error(
          'La sesión no tiene un token de acceso válido. Inicia sesión nuevamente.'
        );
      }

      const response = await fetch(
        `${API_BASE_URL}/api/ask`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({
            question: texto,
            session_id: sessionId
          })
        }
      );

      const data = await response.json();

      if (!response.ok) {
        let detail = `HTTP ${response.status}`;

        if (typeof data.detail === 'string') {
          detail = data.detail;
        }

        throw new Error(detail);
      }

      setMessages((previous) => [
        ...previous,
        {
          role: 'assistant',
          text: data.answer || 'No se recibió una respuesta.',
          sources: data.sources || [],
          tools: data.tools_used || [],
          traceId: data.trace_id
        }
      ]);

      if (data.session_id) {
        setSessionId(data.session_id);
      }
    } catch (err) {
      const mensaje = err.message || 'Error inesperado';

      setError(mensaje);

      setMessages((previous) => [
        ...previous,
        {
          role: 'error',
          text: `No fue posible completar la consulta: ${mensaje}`
        }
      ]);
    } finally {
      setSending(false);
    }
  }

  function nuevaConversacion() {
    if (sending) {
      return;
    }

    setView('chat');
    setMessages([]);
    setQuestion('');
    setError('');
    setSessionId(crypto.randomUUID());
  }

  function renderMessage(message, index) {
    const isUser = message.role === 'user';
    const isError = message.role === 'error';

    return (
      <div
        key={index}
        style={{
          padding: '16px',
          marginBottom: '14px',
          borderRadius: '12px',
          background: isUser
            ? '#26345c'
            : isError
              ? '#40212c'
              : '#19233e',
          border: '1px solid rgba(255,255,255,0.08)',
          whiteSpace: 'pre-wrap',
          overflowWrap: 'anywhere'
        }}
      >
        <div
          style={{
            fontWeight: 600,
            marginBottom: '8px'
          }}
        >
          {isUser
            ? 'Tú'
            : isError
              ? 'Error'
              : 'Asistente IA'}
        </div>

        <div>{message.text}</div>

        {message.sources?.length > 0 && (
          <div
            style={{
              marginTop: '14px',
              paddingTop: '10px',
              borderTop: '1px solid rgba(255,255,255,0.1)'
            }}
          >
            <strong>Fuentes consultadas</strong>

            {message.sources.map((source, sourceIndex) => (
              <div
                key={sourceIndex}
                style={{
                  fontSize: '12px',
                  marginTop: '8px',
                  opacity: 0.85
                }}
              >
                [{source.ref || sourceIndex + 1}]{' '}
                {source.document || 'Documento'}

                {source.similarity != null && (
                  <span>
                    {' '}· Similitud:{' '}
                    {(Number(source.similarity) * 100).toFixed(1)}%
                  </span>
                )}
              </div>
            ))}
          </div>
        )}

        {message.tools?.length > 0 && (
          <div
            style={{
              marginTop: '12px',
              fontSize: '12px',
              opacity: 0.7
            }}
          >
            Herramientas utilizadas: {message.tools.join(', ')}
          </div>
        )}

        {message.traceId && (
          <div
            style={{
              marginTop: '8px',
              fontSize: '11px',
              opacity: 0.5
            }}
          >
            Trace ID: {message.traceId}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">
          <Bot size={23} />
          IC7 <span>AI</span>
        </div>

        <div className="sidebar-section">
          ESPACIO DE TRABAJO
        </div>

        <button className={view === 'chat' ? 'nav-active' : 'nav-item'}
          onClick={() => setView('chat')}
          style={{width:'100%', textAlign:'left', cursor:'pointer', border:0}}>
          <Bot size={17} />
          Asistente empresarial
        </button>

        <button
          className="nav-item"
          onClick={nuevaConversacion}
          disabled={sending}
          style={{
            width: '100%',
            textAlign: 'left',
            cursor: 'pointer'
          }}
        >
          <CircleHelp size={17} />
          Nueva conversación
        </button>

        <button className={view === 'documents' ? 'nav-active' : 'nav-item'}
          onClick={() => setView('documents')}
          style={{width:'100%', textAlign:'left', cursor:'pointer', border:0}}>
          <FileText size={17} />
          Documentos
        </button>

        <div className="sidebar-bottom">
          <ShieldCheck size={17} />
          Sesión segura con Cognito
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <strong>Enterprise AI Assistant</strong>
            <small>RAG empresarial · AWS Lambda</small>
          </div>

          <div className="user">
            <span>{email}</span>

            <button
              className="outline"
              onClick={() => auth.signoutRedirect()}
            >
              <LogOut size={16} />
              Salir
            </button>
          </div>
        </header>

        {view === 'documents' ? (
          <DocumentsView apiBaseUrl={API_BASE_URL} accessToken={auth.user?.access_token} />
        ) : (
          <>
        <section
          className="conversation"
          style={{
            overflowY: 'auto',
            paddingBottom: '190px'
          }}
        >
          {messages.length === 0 ? (
            <>
              <div className="welcome-icon">
                <Bot size={30} />
              </div>

              <h1>¿En qué puedo ayudarte?</h1>

              <p>
                Consulta procedimientos internos, solicita información
                y obtén respuestas con referencias verificables.
              </p>

              {!apiReady && (
                <div className="notice">
                  <LockKeyhole size={18} />

                  <div>
                    <strong>Conexión API pendiente</strong>
                    <span>
                      Configura VITE_API_BASE_URL en .env.local
                      para habilitar el chat.
                    </span>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div
              style={{
                width: '100%',
                maxWidth: '800px',
                margin: '0 auto',
                textAlign: 'left'
              }}
            >
              {messages.map(renderMessage)}

              {sending && (
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '14px'
                  }}
                >
                  <Loader2 className="spin" size={18} />
                  Consultando al asistente...
                </div>
              )}
            </div>
          )}

          {error && messages.length === 0 && (
            <p role="alert">{error}</p>
          )}
        </section>

        <div className="composer">
          <form
            className="field"
            onSubmit={enviarPregunta}
          >
            <input
              aria-label="Pregunta"
              placeholder={
                apiReady
                  ? 'Escribe una pregunta sobre los documentos...'
                  : 'Conecta API Gateway para habilitar el chat'
              }
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              disabled={!apiReady || sending}
              maxLength={2000}
            />

            <button
              type="submit"
              disabled={
                !apiReady ||
                sending ||
                !question.trim()
              }
              title="Enviar pregunta"
              aria-label="Enviar pregunta"
            >
              {sending ? (
                <Loader2 className="spin" size={18} />
              ) : (
                <Send size={18} />
              )}
            </button>
          </form>

          <small>
            {apiReady
              ? 'Asistente conectado mediante AWS API Gateway y Cognito.'
              : 'El chat se habilitará después de conectar la API.'}
          </small>
        </div>
          </>
        )}
      </main>
    </div>
  );
}

function Login() {
  const auth = useAuth();

  if (auth.isLoading || auth.activeNavigator) {
    return (
      <div className="center">
        <Loader2 className="spin" size={30} />
        <p>Validando sesión...</p>
      </div>
    );
  }

  if (auth.error) {
    return (
      <div className="center">
        <CircleHelp size={35} />

        <h2>No se pudo completar el inicio de sesión</h2>

        <p>{auth.error.message}</p>

        <button onClick={() => auth.signinRedirect()}>
          Intentar de nuevo
        </button>
      </div>
    );
  }

  if (auth.isAuthenticated) {
    return <Workspace />;
  }

  return (
    <div className="center">
      <div className="login-card">
        <div className="welcome-icon">
          <Bot size={32} />
        </div>

        <div className="eyebrow">
          IC7 · ENTERPRISE AI ASSISTANT
        </div>

        <h1>Tu conocimiento, en un solo lugar.</h1>

        <p>
          Asistente empresarial con búsqueda documental,
          herramientas y trazabilidad.
        </p>

        <button
          className="primary"
          onClick={() => auth.signinRedirect()}
        >
          <LogIn size={18} />
          Iniciar sesión con Cognito
        </button>

        <div className="privacy">
          <ShieldCheck size={16} />
          Acceso exclusivo para usuarios autorizados
        </div>
      </div>
    </div>
  );
}

export default function App({ setupRequired = false }) {
  if (setupRequired) {
    return (
      <div className="center">
        <div className="login-card">
          <Bot size={40} />

          <h1>Configurar Amazon Cognito</h1>

          <p>
            Faltan <code>VITE_COGNITO_POOL_ID</code> y/o{' '}
            <code>VITE_COGNITO_CLIENT_ID</code> en el archivo{' '}
            <code>.env.local</code>.
          </p>

          <p>No agregues claves secretas al frontend.</p>
        </div>
      </div>
    );
  }

  return <Login />;
}
