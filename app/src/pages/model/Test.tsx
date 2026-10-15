import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Send, ArrowLeft, Loader2, Brain, Wrench } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { modelService } from '@/services/model';
import type { ModelRead } from '@/services/model';

export default function ModelTest() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [model, setModel] = useState<ModelRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [messages, setMessages] = useState<Array<{
    role: 'user' | 'assistant';
    content: string;
    type: 'text' | 'tool_call' | 'tool_result' | 'thinking';
    toolCalls?: Array<{
      id: string;
      type: string;
      function: {
        name: string;
        arguments: string;
      };
    }>;
    toolResult?: {
      toolCallId: string;
      functionName: string;
      result: any;
    };
  }>>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [streaming, setStreaming] = useState(false);
  const [currentAssistantMessage, setCurrentAssistantMessage] = useState<string>('');
  const [currentToolCalls, setCurrentToolCalls] = useState<Array<{
    id: string;
    type: string;
    function: {
      name: string;
      arguments: string;
    };
  }>>([]);
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    loadModel();
  }, [id]);

  const loadModel = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const data = await modelService.getModel(Number(id));
      setModel(data);
    } catch (error) {
      console.error('加载模型失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || sending || !model) return;
    
    const userMessage = {
      role: 'user' as const,
      content: input,
      type: 'text' as const
    };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setSending(true);
    setStreaming(true);
    setCurrentAssistantMessage('');
    setCurrentToolCalls([]);

    try {
      // 取消之前的请求
      if (controllerRef.current) {
        controllerRef.current.abort();
      }
      controllerRef.current = new AbortController();

      // 构建请求参数
      const requestBody = {
        message: input,
        model_id: Number(id),
        conversation_id: conversationId || undefined
      };

      // 发送流式请求
      const response = await fetch('http://localhost:8080/api/v1/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
        },
        body: JSON.stringify(requestBody),
        signal: controllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        // 处理流式数据
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.trim() === '') continue;
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6);
            if (dataStr === '[DONE]') {
              // 流式结束
              if (currentAssistantMessage || currentToolCalls.length > 0) {
                const assistantMessage = {
                  role: 'assistant' as const,
                  content: currentAssistantMessage,
                  type: currentToolCalls.length > 0 ? 'tool_call' as const : 'text' as const,
                  toolCalls: currentToolCalls.length > 0 ? currentToolCalls : undefined
                };
                setMessages(prev => [...prev, assistantMessage]);
              }
              setStreaming(false);
              break;
            }
            
            try {
              const data = JSON.parse(dataStr);
              if (data.choices && data.choices.length > 0) {
                const choice = data.choices[0];
                if (choice.delta) {
                  if (choice.delta.content) {
                    setCurrentAssistantMessage(prev => prev + choice.delta.content);
                  }
                  if (choice.delta.tool_calls) {
                    setCurrentToolCalls(prev => [...prev, ...choice.delta.tool_calls]);
                  }
                }
              }
              // 保存会话ID
              if (data.conversation_id) {
                setConversationId(data.conversation_id);
              }
            } catch (e) {
              console.error('解析流式数据失败:', e);
            }
          }
        }
      }

    } catch (error) {
      console.error('发送消息失败:', error);
      const errorMessage = {
        role: 'assistant' as const,
        content: '抱歉，处理您的请求时出现错误。',
        type: 'text' as const
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setSending(false);
      setStreaming(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      </div>
    );
  }

  if (!model) {
    return (
      <div className="p-6">
        <div className="text-center">
          <h2 className="text-xl font-semibold">模型不存在</h2>
          <Button onClick={() => navigate('/models')} className="mt-4">
            <ArrowLeft className="mr-2 h-4 w-4" />返回模型列表
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-2">
        <Button variant="ghost" onClick={() => navigate('/models')}>
          <ArrowLeft className="mr-2 h-4 w-4" />返回模型列表
        </Button>
        <h1 className="text-3xl font-bold">模型测试 - {model.name}</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>与模型对话</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="border rounded-lg p-4">
            <h3 className="font-medium mb-2">模型信息</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">模型ID:</span> {model.model_id}
              </div>
              <div>
                <span className="text-muted-foreground">供应商:</span> {model.provider_name}
              </div>
              <div>
                <span className="text-muted-foreground">状态:</span> {model.status}
              </div>
              <div>
                <span className="text-muted-foreground">上下文长度:</span> {model.context_length.toLocaleString()}
              </div>
            </div>
          </div>

          <div className="h-96 border rounded-lg overflow-hidden">
            <ScrollArea className="h-full p-4">
              {messages.length === 0 && !streaming ? (
                <div className="text-center text-muted-foreground py-12">
                  开始与模型对话吧
                </div>
              ) : (
                messages.map((message, index) => (
                  <div key={index} className={`mb-4 ${message.role === 'user' ? 'text-right' : 'text-left'}`}>
                    {message.role === 'user' ? (
                      <div className="inline-block max-w-[80%] p-3 rounded-lg bg-primary text-primary-foreground">
                        {message.content}
                      </div>
                    ) : (
                      <div className="inline-block max-w-[80%] p-3 rounded-lg bg-muted">
                        {message.type === 'thinking' && (
                          <div className="flex items-center gap-2 mb-2">
                            <Brain className="h-4 w-4 text-blue-500" />
                            <span className="text-sm text-blue-500">模型思考中...</span>
                          </div>
                        )}
                        {message.content && (
                          <div className="whitespace-pre-wrap">{message.content}</div>
                        )}
                        {message.type === 'tool_call' && message.toolCalls && (
                          <div className="mt-2 p-2 bg-gray-100 rounded">
                            <div className="flex items-center gap-2 mb-1">
                              <Wrench className="h-4 w-4 text-green-500" />
                              <span className="text-sm font-medium text-green-500">工具调用</span>
                            </div>
                            {message.toolCalls.map((toolCall, toolIndex) => (
                              <div key={toolIndex} className="text-sm mt-1">
                                <div>函数: {toolCall.function.name}</div>
                                <div className="mt-1 p-1 bg-gray-200 rounded text-xs">
                                  参数: {toolCall.function.arguments}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                        {message.type === 'tool_result' && message.toolResult && (
                          <div className="mt-2 p-2 bg-gray-100 rounded">
                            <div className="flex items-center gap-2 mb-1">
                              <Wrench className="h-4 w-4 text-purple-500" />
                              <span className="text-sm font-medium text-purple-500">工具结果</span>
                            </div>
                            <div className="text-sm">
                              <div>函数: {message.toolResult.functionName}</div>
                              <div className="mt-1 p-1 bg-gray-200 rounded text-xs">
                                结果: {JSON.stringify(message.toolResult.result, null, 2)}
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))
              )}
              {streaming && (
                <div className="text-left mb-4">
                  <div className="inline-block max-w-[80%] p-3 rounded-lg bg-muted">
                    {currentAssistantMessage && (
                      <div className="whitespace-pre-wrap">{currentAssistantMessage}</div>
                    )}
                    {currentToolCalls.length > 0 && (
                      <div className="mt-2 p-2 bg-gray-100 rounded">
                        <div className="flex items-center gap-2 mb-1">
                          <Wrench className="h-4 w-4 text-green-500" />
                          <span className="text-sm font-medium text-green-500">工具调用</span>
                        </div>
                        {currentToolCalls.map((toolCall, toolIndex) => (
                          <div key={toolIndex} className="text-sm mt-1">
                            <div>函数: {toolCall.function.name}</div>
                            <div className="mt-1 p-1 bg-gray-200 rounded text-xs">
                              参数: {toolCall.function.arguments}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                    {!currentAssistantMessage && currentToolCalls.length === 0 && (
                      <div className="flex items-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span>模型思考中...</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </ScrollArea>
          </div>

          <div className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="输入您的问题..."
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              disabled={sending}
            />
            <Button onClick={handleSend} disabled={sending || !input.trim()}>
              {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}