import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Optimizer from './pages/Optimizer';
import Weather from './pages/Weather';
import Config from './pages/Config';

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen bg-[#0a0f1a]">
        <Sidebar />
        <main className="flex-1 ml-60 p-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/optimizer" element={<Optimizer />} />
            <Route path="/weather" element={<Weather />} />
            <Route path="/config" element={<Config />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
