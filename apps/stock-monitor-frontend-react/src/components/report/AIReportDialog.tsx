import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { AIDecisionResult } from '@/types/arena';

interface AIReportDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    decision: AIDecisionResult | null;
}

export function AIReportDialog({ open, onOpenChange, decision }: AIReportDialogProps) {
    if (!decision) return null;

    // Parse trigger context if available
    const signals: string[] = [];
    if (decision.trigger_context) {
        let context = decision.trigger_context;
        if (typeof context === 'string') {
            try { context = JSON.parse(context); } catch(e) {}
        }
        
        if (context && typeof context === 'object') {
             Object.entries(context).forEach(([key, value]: [string, any]) => {
                 if (typeof value === 'object' && value !== null) {
                     // e.g. "RSI Oversold": { value: 28, threshold: 30, operator: "<" }
                     let label = key;
                     if (value.value !== undefined) {
                         label += `: ${value.value}`;
                     }
                     signals.push(label);
                 } else {
                     signals.push(key);
                 }
             });
        }
    }

    // Extract report content from JSON decision
    const reportContent = decision.decision_json?.reasoning || 
        (decision.decision_json ? JSON.stringify(decision.decision_json, null, 2) : "暂无分析内容");

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        {decision.stock_code} AI 复盘报告
                        <span className={`text-sm px-2 py-1 rounded-full ${
                          decision.primary_operation === 'buy' ? 'bg-red-100 text-red-700' :
                          decision.primary_operation === 'sell' ? 'bg-green-100 text-green-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {decision.primary_operation?.toUpperCase()}
                        </span>
                    </DialogTitle>
                    <DialogDescription>
                        {new Date(decision.trade_date).toLocaleDateString()} | Model: {decision.model_name}
                    </DialogDescription>
                </DialogHeader>

                {/* Signals */}
                {signals.length > 0 && (
                    <div className="flex gap-2 flex-wrap mb-4">
                        {signals.map((sig, idx) => (
                            <span key={idx} className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                                {sig}
                            </span>
                        ))}
                    </div>
                )}

                {/* Markdown Content */}
                <div className="prose prose-sm max-w-none dark:prose-invert">
                    <ReactMarkdown>{reportContent}</ReactMarkdown>
                </div>
                
                {/* Structured Data View */}
                <div className="mt-6 border-t pt-4">
                    <h4 className="font-semibold mb-2">结构化决策</h4>
                    <pre className="bg-gray-50 p-2 rounded text-xs overflow-x-auto">
                        {JSON.stringify(decision.decision_json, null, 2)}
                    </pre>
                </div>
            </DialogContent>
        </Dialog>
    );
}
