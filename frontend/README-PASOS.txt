IC7 FRONTEND - PARCHE DE INTERFAZ Y LOGIN

1. Extraer el ZIP en C:\Users\gusol\ic7-frontend (combinar src; reemplazar App.jsx, App.css, main.jsx, index.css).
2. Copiar .env.example a .env.local.
3. En .env.local, completar VITE_COGNITO_POOL_ID y VITE_COGNITO_CLIENT_ID desde Cognito.
4. En CMD: cd %USERPROFILE%\ic7-frontend
5. En CMD: npm install react-oidc-context oidc-client-ts lucide-react
6. En CMD: npm run dev -- --host 127.0.0.1 --port 3000 --strictPort
7. Abrir http://localhost:3000/ e iniciar sesión.

NOTAS DE SEGURIDAD: No poner APP_API_KEY, GEMINI_API_KEY, credenciales AWS ni client_secret en variables VITE_*. El chat se mantiene deshabilitado hasta crear y proteger API Gateway con JWT de Cognito y una integración que no exponga secretos. Mantener la Lambda Function URL en AWS_IAM.
