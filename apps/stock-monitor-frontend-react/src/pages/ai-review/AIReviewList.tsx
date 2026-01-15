import { useEffect, useState } from 'react';
import { arenaApi } from '@/lib/api';
import type { AIDecisionResult } from '@/types/arena';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { AIReportDialog } from '@/components/report/AIReportDialog';

export default function AIReviewList() {
  const [decisions, setDecisions] = useState<AIDecisionResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchCode, setSearchCode] = useState('');
  const [selectedDecision, setSelectedDecision] = useState<AIDecisionResult | null>(null);

  const fetchDecisions = async (code?: string) => {
    setLoading(true);
    try {
      const response = await arenaApi.getDecisions(code);
      setDecisions(response.data);
    } catch (error) {
      console.error('Failed to fetch decisions:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDecisions();
  }, []);

  const handleSearch = () => {
    fetchDecisions(searchCode || undefined);
  };

  return (
    <div className="container mx-auto p-4 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">每日 AI 复盘</h1>
        <div className="flex gap-2">
            <Input 
                placeholder="股票代码" 
                value={searchCode}
                onChange={(e) => setSearchCode(e.target.value)}
                className="w-40"
            />
            <Button onClick={handleSearch}>搜索</Button>
            <Button variant="outline" onClick={() => fetchDecisions()}>刷新</Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {decisions.map((decision) => (
          <Card 
            key={decision.id} 
            className="cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => setSelectedDecision(decision)}
          >
            <CardHeader className="pb-2">
              <CardTitle className="flex justify-between items-center text-lg">
                <span>{decision.stock_code}</span>
                <span className={`text-sm px-2 py-1 rounded ${
                  decision.primary_operation === 'buy' ? 'bg-red-100 text-red-700' :
                  decision.primary_operation === 'sell' ? 'bg-green-100 text-green-700' :
                  'bg-gray-100 text-gray-700'
                }`}>
                  {decision.primary_operation?.toUpperCase()}
                </span>
              </CardTitle>
              <div className="text-xs text-gray-500">
                {new Date(decision.trade_date).toLocaleDateString()}
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <p className="text-sm font-medium">主要观点:</p>
                <p className="text-sm text-gray-600 line-clamp-3">
                  {decision.primary_reason}
                </p>
                <div className="pt-2 text-xs text-gray-400 flex justify-between">
                    <span>Model: {decision.model_name}</span>
                    <span>{new Date(decision.created_at).toLocaleString()}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      
      {decisions.length === 0 && !loading && (
        <div className="text-center text-gray-500 py-10">
          暂无复盘数据
        </div>
      )}

      <AIReportDialog 
        open={!!selectedDecision} 
        onOpenChange={(open) => !open && setSelectedDecision(null)}
        decision={selectedDecision}
      />
    </div>
  );
}
