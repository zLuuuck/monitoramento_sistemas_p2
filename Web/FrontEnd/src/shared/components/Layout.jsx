export function Layout({ children }) {
  return (
    <div className="min-h-screen bg-gray-100">
      {/* Cabeçalho */}
      <header className="bg-white shadow-md p-4 border-b border-gray-200">
        <div className="container mx-auto">
          <div className="flex items-center gap-3">
            <span className="text-2xl">📊</span>
            <h1 className="text-2xl font-bold text-gray-800">
              Dashboard de Monitoramento
            </h1>
          </div>
        </div>
      </header>

      {/* Conteúdo principal */}
      <main className="container mx-auto p-6">
        {children}
      </main>
    </div>
  );
}