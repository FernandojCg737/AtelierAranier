export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api/v1',
  googleClientId: '358122795142-b9uf3oe7i98lg2bjkhcj6habdrh1mqcp.apps.googleusercontent.com',
  // CU11: Client ID de PayPal (sandbox) -- es publico por diseno, la pagina
  // de checkout de PayPal lo necesita para cargar su SDK en el navegador.
  // El Client Secret nunca sale del backend.
  paypalClientId: 'BAA5qL7SYwxYqXcObNp7cuq9-DKSDIrlAslsqcoHEFuPoLBrvkEydFDvIsjkKf0Zj49TJZ4AXptEAtzVmc'
};
