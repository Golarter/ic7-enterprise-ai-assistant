
import { useState } from "react";
import { useAuth } from "react-oidc-context";

export default function App() {
  const auth = useAuth();
  const [resultado, setResultado] = useState("");

  async function probarAPI() {
    setResultado("Consultando API Gateway...");

    try {
      const response = await fetch(
        "https://xwejxdr534.execute-api.us-east-1.amazonaws.com/health",
        {
          headers: {
            Authorization: `Bearer ${auth.user.access_token}`,
          },
        }
      );

      setResultado(
        `HTTP ${response.status}: ${await response.text()}`
      );
    } catch (error) {
      setResultado(`Error de conexión: ${error.message}`);
    }
  }

  if (!auth.isAuthenticated) {
    return <p>Primero inicia sesión con Cognito.</p>;
  }

  return (
    <main style={{ padding: 32 }}>
      <h2>Prueba API Gateway + Cognito</h2>
      <button onClick={probarAPI}>Probar conexión</button>
      <pre>{resultado}</pre>
    </main>
  );
}
