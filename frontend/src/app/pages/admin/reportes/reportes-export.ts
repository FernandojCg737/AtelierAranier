// Los 4 reportes de CU16 comparten esta misma forma de "descargar" un blob
// que llego por HttpClient (CSV/Excel) como si fuera un link normal.
export function descargarArchivo(blob: Blob, nombreArchivo: string): void {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = nombreArchivo;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}
