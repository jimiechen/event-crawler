import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import PromptList from '@/pages/prompts/PromptList';
import SignalList from '@/pages/signals/SignalList';
import AIReviewList from '@/pages/ai-review/AIReviewList';
import Dashboard from '@/pages/dashboard/Dashboard';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="ai-review" element={<AIReviewList />} />
          <Route path="prompts" element={<PromptList />} />
          <Route path="signals" element={<SignalList />} />
          <Route path="settings" element={<div>设置页面</div>} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
