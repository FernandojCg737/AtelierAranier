export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api/v1',
  googleClientId: '884894293971-b3tg606745s1unk6fvcr1uplu9fgaiqg.apps.googleusercontent.com',
  // CU11: Client ID de PayPal (sandbox) -- es publico por diseno, la pagina
  // de checkout de PayPal lo necesita para cargar su SDK en el navegador.
  // El Client Secret nunca sale del backend.
  paypalClientId: 'BAA5qL7SYwxYqXcObNp7cuq9-DKSDIrlAslsqcoHEFuPoLBrvkEydFDvIsjkKf0Zj49TJZ4AXptEAtzVmc'
};
