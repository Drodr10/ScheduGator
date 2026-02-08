import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage } from '../types/index';
import { Send, MessageSquare, Loader2 } from 'lucide-react';

interface ChatSidebarProps {
  majorsList: string[];
  selectedMajor: string;
  onMajorChange: (major: string) => void;
  messages: ChatMessage[];
  isLoading: boolean;
  onSendMessage: (message: string) => void;
}

const DEMO_MAJORS = [
  'Computer Science (CPS)',
  'Computer Engineering (CPE)',
  'Electrical Engineering (EES)',
  'Data Science (DAS)',
  'Business (BUS)',
];

// Format message content for better readability
function formatMessage(content: string): JSX.Element {
  const trimmed = content.trim();
  // Check for empty tool_calls response (with flexible whitespace)
  if (/^\{\s*"tool_calls"\s*:\s*\[\s*\]\s*\}$/.test(trimmed)) {
    return (
      <p>
        I can help with that. Please tell me your major and any preferences
        (morning/evening, days off, AP/dual enrollment credits).
      </p>
    );
  }
  // Split by double newlines for paragraphs
  const paragraphs = content.split(/\n\n+/);
  
  return (
    <>
      {paragraphs.map((para, idx) => {
        // Check if paragraph is a bullet list
        const isList = para.includes('\n* ') || para.includes('\n- ') || /^[\*\-•]\s/.test(para);
        
        if (isList) {
          // Format as bullet list
          const items = para
            .split(/\n/)
            .filter(line => line.trim())
            .map(line => line.replace(/^[\*\-•]\s*/, '').trim());
          
          return (
            <ul key={idx} className="list-disc list-inside space-y-1 my-2">
              {items.map((item, i) => (
                <li key={i} className="ml-2">{item}</li>
              ))}
            </ul>
          );
        } else {
          // Regular paragraph - preserve line breaks
          return (
            <p key={idx} className={idx > 0 ? 'mt-3' : ''}>
              {para.split('\n').map((line, i) => (
                <React.Fragment key={i}>
                  {i > 0 && <br />}
                  {line}
                </React.Fragment>
              ))}
            </p>
          );
        }
      })}
    </>
  );
}

export const ChatSidebar: React.FC<ChatSidebarProps> = ({
  majorsList,
  selectedMajor,
  onMajorChange,
  messages,
  isLoading,
  onSendMessage,
}) => {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (inputValue.trim()) {
      onSendMessage(inputValue);
      setInputValue('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const majorsToShow = majorsList.length > 0 ? majorsList : DEMO_MAJORS;

  return (
    <div className="flex flex-col h-full min-h-0 bg-white dark:bg-gray-800 border-r border-gator-gray-200 dark:border-gray-700 overflow-hidden">
      {/* Header */}
      <div
        className="bg-gradient-to-r from-gator-dark to-gator-light p-4 text-white shrink-0"
        style={{ backgroundImage: 'linear-gradient(90deg, #003DA5 0%, #0066FF 100%)' }}
      >
        <h2 className="text-xl font-bold flex items-center gap-2">
          <MessageSquare size={24} />
          AI Advisor
        </h2>
        <p className="text-sm text-gator-gray-300 mt-1">ScheduGator</p>
      </div>

      {/* Major Selection */}
      <div className="p-4 border-b border-gator-gray-200 dark:border-gray-700 bg-gator-gray-50 dark:bg-gray-900 shrink-0">
        <label className="block text-sm font-semibold text-gator-gray-700 dark:text-gray-300 mb-2">
          Select Your Major
        </label>
        <select
          value={selectedMajor}
          onChange={(e) => onMajorChange(e.target.value)}
          className="w-full px-3 py-2 border-2 border-gator-dark dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-gator-accent bg-white dark:bg-gray-700 text-gator-gray-900 dark:text-gray-100"
        >
          <option value="">Choose a major...</option>
          {majorsToShow.map((major) => (
            <option key={major} value={major}>
              {major}
            </option>
          ))}
        </select>
      </div>

      {/* Messages Area */}
      <div className="flex-1 min-h-0 overflow-y-auto p-4 space-y-4 bg-gator-gray-50 dark:bg-gray-900 flex flex-col">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center text-center py-8">
            <MessageSquare size={48} className="text-gator-gray-300 dark:text-gray-600 mb-4" />
            <p className="text-gator-gray-600 dark:text-gray-400 font-semibold">No messages yet</p>
            <p className="text-gator-gray-500 dark:text-gray-500 text-sm mt-2">
              Select a major and ask the AI Advisor to generate your perfect schedule!
            </p>
            <div className="mt-6 space-y-2 w-full">
              <p className="text-xs font-semibold text-gator-gray-600 dark:text-gray-400 mb-3">Example questions:</p>
              <div className="space-y-1 text-xs text-gator-gray-600 dark:text-gray-500">
                <p>• "Show me a schedule with no morning classes"</p>
                <p>• "Optimize for study groups"</p>
                <p>• "Check if this works with my current progress"</p>
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg) => {
              return (
                <div key={msg.id} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div
                    className={`max-w-[85%] px-4 py-3 rounded-lg ${
                      msg.type === 'user'
                        ? 'bg-gator-dark text-white rounded-br-none'
                        : msg.type === 'system'
                        ? 'bg-yellow-100 dark:bg-yellow-900 text-yellow-900 dark:text-yellow-100 border-l-4 border-yellow-500 rounded-bl-none'
                        : 'bg-gator-gray-200 dark:bg-gray-700 text-gator-gray-900 dark:text-gray-100 rounded-bl-none'
                    }`}
                  >
                    <div className="text-sm whitespace-pre-wrap break-words">
                      {formatMessage(msg.content)}
                    </div>
                    <div className="flex items-center justify-between mt-2 gap-2">
                      <p className={`text-xs ${msg.type === 'user' ? 'text-gator-gray-300' : 'text-gator-gray-600 dark:text-gray-400'}`}>
                        {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gator-gray-200 dark:bg-gray-700 text-gator-gray-900 dark:text-gray-100 px-4 py-3 rounded-lg rounded-bl-none flex items-center gap-2">
                  <div className="gator-loader">🐊</div>
                  <span className="text-sm">Generating schedule...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-gator-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 shrink-0">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask the AI Advisor..."
            disabled={!selectedMajor}
            className="flex-1 px-4 py-2 border-2 border-gator-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:border-gator-dark dark:focus:border-gator-light focus:ring-1 focus:ring-gator-dark dark:focus:ring-gator-light bg-white dark:bg-gray-700 text-gator-gray-900 dark:text-gray-100 disabled:bg-gator-gray-100 dark:disabled:bg-gray-900 disabled:cursor-not-allowed"
          />
          <button
            onClick={handleSend}
            disabled={!inputValue.trim() || !selectedMajor || isLoading}
            className="bg-gator-accent text-white p-2 rounded-lg hover:bg-orange-600 transition-colors disabled:bg-gator-gray-400 dark:disabled:bg-gray-700 disabled:cursor-not-allowed"
          >
            {isLoading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
          </button>
        </div>
        {!selectedMajor && (
          <p className="text-xs text-gator-gray-500 dark:text-gray-500 mt-2">📌 Please select a major to get started</p>
        )}
      </div>
    </div>
  );
};
