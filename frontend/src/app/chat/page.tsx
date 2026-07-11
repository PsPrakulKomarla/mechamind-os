'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Loader2, FileText, Copy, ThumbsUp, ThumbsDown, ChevronLeft, ChevronRight, Sparkles, Menu, Bell, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { toast } from '@/components/ui/toaster';
import { cn, formatDateTime, truncate } from '@/lib/utils';

interface Citation {
  document_id: string;
  chunk_id: string;
  excerpt: string;
  score: number;
  document_title: string;
  page_number?: number;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  created_at: string;
  feedback?: 'helpful' | 'not_helpful';
}

const LLM_PROVIDERS = [
  { value: 'openai', label: 'GPT-4o (OpenAI)' },
  { value: 'anthropic', label: 'Claude 3.5 Sonnet (Anthropic)' },
  { value: 'ollama', label: 'Llama 3.1 70B (Local)' },
];

const SUGGESTED_PROMPTS = [
  "What's the maintenance procedure for Pump P-101?",
  "Show me common issues for Boiler B-601",
  "What are the operating parameters for Compressor C-401?",
  "Find documents about vibration analysis",
  "What's the last maintenance date for Turbine TG-301?",
  "Explain the safety procedure for confined space entry",
];

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [provider, setProvider] = useState('openai');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [showSidebar, setShowSidebar] = useState(true);
  const [suggestedPrompts] = useState(SUGGESTED_PROMPTS);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: input,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    const currentInput = input;
    setInput('');

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: currentInput,
          session_id: sessionId,
          provider,
          use_rag: true,
          top_k: 10,
        }),
      });

      if (!response.ok) throw new Error('Failed to get response');

      const data = await response.json();
      
      if (!sessionId) setSessionId(data.session_id);

      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.message.content,
        citations: data.citations || [],
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to send message. Please try again.',
        variant: 'destructive',
      });
      // Revert user message on error
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
    }
  };

  const handleFeedback = (messageId: string, feedback: 'helpful' | 'not_helpful') => {
    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === messageId ? { ...msg, feedback } : msg
      )
    );
    toast({
      title: 'Feedback recorded',
      description: `Thanks for your feedback!`,
    });
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({ title: 'Copied to clipboard' });
  };

  const handlePromptClick = (prompt: string) => {
    setInput(prompt);
    textareaRef.current?.focus();
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className={cn(
        'w-72 flex-shrink-0 border-r border-gray-200 bg-white flex flex-col transition-all duration-300',
        showSidebar ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      )}>
        <div className="p-4 border-b border-gray-200">
          <h2 className="font-semibold text-gray-900">Chat Sessions</h2>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {messages.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Sparkles className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p className="text-sm">Start a new conversation</p>
            </div>
          ) : (
            <button
              className="w-full text-left p-3 rounded-lg hover:bg-gray-100 transition-colors"
              onClick={() => setMessages([])}
            >
              <span className="font-medium text-gray-900">New Conversation</span>
              <p className="text-xs text-gray-500 mt-1">Start fresh chat</p>
            </button>
          )}
        </div>
        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm text-gray-500">
            <span>Provider</span>
            <Select value={provider} onValueChange={setProvider}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Select" />
              </SelectTrigger>
              <SelectContent>
                {LLM_PROVIDERS.map((p) => (
                  <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="h-16 border-b border-gray-200 bg-white flex items-center px-6 gap-4">
          <button
            className="lg:hidden p-2 rounded-lg hover:bg-gray-100"
            onClick={() => setShowSidebar(!showSidebar)}
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="flex-1">
            <h1 className="text-lg font-semibold text-gray-900">Knowledge Copilot</h1>
            <p className="text-xs text-gray-500">Ask questions about your industrial documents</p>
          </div>
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" className="relative">
              <Bell className="h-5 w-5" />
              <span className="absolute top-1 right-1 h-2 w-2 bg-red-500 rounded-full" />
            </Button>
            <Button variant="ghost" size="icon">
              <User className="h-5 w-5" />
            </Button>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-hidden flex flex-col">
          <ScrollArea className="flex-1 p-6 space-y-6">
            {messages.length === 0 ? (
              <div className="max-w-2xl mx-auto text-center py-12">
                <Sparkles className="h-16 w-16 mx-auto text-primary-600 mb-4" />
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">Welcome to Knowledge Copilot</h2>
                <p className="text-gray-500 mb-6 max-w-md mx-auto">
                  Ask me anything about your equipment, procedures, maintenance records, or compliance documents.
                  I'll search through your knowledge base and provide answers with source citations.
                </p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {suggestedPrompts.map((prompt) => (
                    <Button
                      key={prompt}
                      variant="outline"
                      size="sm"
                      className="text-left w-auto"
                      onClick={() => handlePromptClick(prompt)}
                    >
                      {prompt}
                    </Button>
                  ))}
                </div>
              </div>
            ) : (
              <>
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={cn(
                      'flex gap-3 max-w-3xl',
                      message.role === 'user' ? 'ml-auto flex-row-reverse' : ''
                    )}
                  >
                    <div
                      className={cn(
                        'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
                        message.role === 'user'
                          ? 'bg-primary-100 text-primary-600'
                          : 'bg-gray-100 text-gray-600'
                      )}
                    >
                      {message.role === 'user' ? (
                        <span className="text-sm font-medium">U</span>
                      ) : (
                        <Sparkles className="h-4 w-4" />
                      )}
                    </div>
                    <div
                      className={cn(
                        'max-w-[70%] rounded-2xl p-4',
                        message.role === 'user'
                          ? 'bg-primary-600 text-white rounded-tr-sm'
                          : 'bg-white border border-gray-200 rounded-tl-sm shadow-sm'
                      )}
                    >
                      <div className="prose prose-sm max-w-none">
                        {message.role === 'assistant' ? (
                          <div dangerouslySetInnerHTML={{ __html: message.content }} />
                        ) : (
                          <p className="whitespace-pre-wrap">{message.content}</p>
                        )}
                      </div>
                      
                      {/* Citations */}
                      {message.citations && message.citations.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-gray-100">
                          <p className="text-xs font-medium text-gray-500 mb-2">Sources</p>
                          <div className="space-y-1">
                            {message.citations.slice(0, 3).map((citation, idx) => (
                              <div
                                key={idx}
                                className="flex items-start gap-2 p-2 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
                              >
                                <FileText className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
                                <div className="flex-1 min-w-0">
                                  <p className="text-xs font-medium text-gray-900 truncate">
                                    {citation.document_title}
                                  </p>
                                  <p className="text-xs text-gray-500 line-clamp-1">
                                    {truncate(citation.excerpt, 100)}
                                  </p>
                                  {citation.page_number && (
                                    <span className="text-xs text-primary-600">
                                      Page {citation.page_number}
                                    </span>
                                  )}
                                </div>
                              </div>
                            ))}
                            {message.citations.length > 3 && (
                              <p className="text-xs text-gray-500">
                                +{message.citations.length - 3} more sources
                              </p>
                            )}
                          </div>
                        </div>
                      )}
                      
                      {/* Actions */}
                      <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-400">
                            {formatDateTime(message.created_at)}
                          </span>
                          {message.role === 'assistant' && (
                            <>
                              <Button
                                variant="ghost"
                                size="icon"
                                className={cn(
                                  'h-7 w-7',
                                  message.feedback === 'helpful' && 'text-green-600'
                                )}
                                onClick={() => handleFeedback(message.id, 'helpful')}
                                aria-label="Helpful"
                              >
                                <ThumbsUp className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                className={cn(
                                  'h-7 w-7',
                                  message.feedback === 'not_helpful' && 'text-red-600'
                                )}
                                onClick={() => handleFeedback(message.id, 'not_helpful')}
                                aria-label="Not helpful"
                              >
                                <ThumbsDown className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-7 w-7"
                                onClick={() => handleCopy(message.content)}
                                aria-label="Copy"
                              >
                                <Copy className="h-4 w-4" />
                              </Button>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex gap-3">
                    <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
                      <Sparkles className="h-4 w-4 text-gray-600 animate-pulse" />
                    </div>
                    <div className="bg-white border border-gray-200 rounded-2xl p-4 rounded-tl-sm shadow-sm max-w-[70%]">
                      <div className="flex gap-1">
                        <span className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <span className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <span className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </ScrollArea>

          {/* Input */}
          <div className="border-t border-gray-200 bg-white p-4">
            <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
              <div className="flex gap-2">
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask about equipment, procedures, maintenance..."
                  className="flex-1 min-h-[50px] max-h-[200px] p-3 pr-10 border border-gray-300 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  rows={1}
                  disabled={isLoading}
                />
                <Button
                  type="submit"
                  size="lg"
                  disabled={!input.trim() || isLoading}
                  className="h-[50px] flex-shrink-0"
                >
                  {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
                </Button>
              </div>
              <p className="text-xs text-gray-500 mt-2 text-center">
                Powered by {LLM_PROVIDERS.find(p => p.value === provider)?.label || 'AI'} • Press Enter to send, Shift+Enter for new line
              </p>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}