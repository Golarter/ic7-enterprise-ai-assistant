import React from 'react';
import ReactDOM from 'react-dom/client';
import { AuthProvider } from 'react-oidc-context';
import App from './App.jsx';
import './index.css';

const region = import.meta.env.VITE_COGNITO_REGION || 'us-east-1';
const poolId = import.meta.env.VITE_COGNITO_POOL_ID;
const clientId = import.meta.env.VITE_COGNITO_CLIENT_ID;
const configured = Boolean(poolId && clientId && !poolId.includes('REEMPLAZAR') && !clientId.includes('REEMPLAZAR'));
const oidcConfig = {
  authority: `https://cognito-idp.${region}.amazonaws.com/${poolId}`,
  client_id: clientId,
  redirect_uri: 'http://localhost:3000/',
  post_logout_redirect_uri: 'http://localhost:3000/',
  response_type: 'code',
  scope: 'openid email profile',
  onSigninCallback: () => window.history.replaceState({}, document.title, window.location.pathname),
};

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {configured ? <AuthProvider {...oidcConfig}><App /></AuthProvider> : <App setupRequired />}
  </React.StrictMode>
);
