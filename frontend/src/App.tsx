import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Findings from './pages/Findings'
import FindingDetail from './pages/FindingDetail'

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen bg-gray-50">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/findings" element={<Findings />} />
            <Route path="/findings/:id" element={<FindingDetail />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
