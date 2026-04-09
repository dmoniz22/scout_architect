import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import TermPlanner from './pages/TermPlanner';
import MyPlans from './pages/MyPlans';
import Settings from './pages/Settings';
import SingleMeeting from './pages/SingleMeeting';
import DeletedItems from './pages/DeletedItems';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="term-planner" element={<TermPlanner />} />
          <Route path="my-plans" element={<MyPlans />} />
          <Route path="single-meeting" element={<SingleMeeting />} />
          <Route path="deleted" element={<DeletedItems />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;