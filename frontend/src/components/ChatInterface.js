import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Send } from 'lucide-react';
import '../App.css';
import UploadPdf from './UploadPdf';
import UploadPowerPoint from './UploadPowerPoint';
import ProcessUrl from './ProcessUrl';
import ProcessYouTubeVideo from './ProcessYouTubeVideo';
import AudioChat from './AudioChat';

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [selectedTab, setSelectedTab] = useState('conversation');
  const [history, setHistory] = useState([]);
  const [inputLanguage, setInputLanguage] = useState('auto-detect');
  const [outputLanguage, setOutputLanguage] = useState('English');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [availableLanguages, setAvailableLanguages] = useState([]);
  const [isLoadingLanguages, setIsLoadingLanguages] = useState(true);

  const fetchAvailableLanguages = async () => {
    try {
      setIsLoadingLanguages(true);
      const response = await axios.get('http://127.0.0.1:5000/chatbot/available-languages');
      setAvailableLanguages(response.data.languages);
    } catch (error) {
      console.error('Error fetching languages:', error);
      setError('Failed to load available languages');
      setTimeout(() => setError(''), 2000);
    } finally {
      setIsLoadingLanguages(false);
    }
  };

  useEffect(() => {
    fetchAvailableLanguages();
  }, []);

  const fetchChatHistory = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:5000/chatbot/get-history');
      const transformedData = Array.isArray(response.data.history)
        ? response.data.history.map((entry) => ({
            sender: entry.role === 'user' ? 'user' : 'assistant',
            text: entry.content
          }))
        : [];
      setHistory(transformedData);
    } catch (error) {
      console.error('Error fetching chat history:', error);
      setError('Failed to load chat history')
      setTimeout(() => setError(''), 2000);
      setHistory([]);
    }
  };
  

  useEffect(() => {
    if (selectedTab === 'history') {
      fetchChatHistory();
    }
  }, [selectedTab]);
  
  const handleClearHistory = async () => {
    try {
      await axios.post('http://127.0.0.1:5000/chatbot/clear-history');
      setHistory([]);
      setSuccess('Chat history cleared successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      console.error('Error clearing chat history:', error);
      setError('Failed to clear chat history');
      setTimeout(() => setError(''), 3000);
    }
  };

  const handleSend = async () => {
      if (inputValue.trim()) {
          const newUserMessage = { text: inputValue, sender: 'user' };
          setMessages((prevMessages) => [...prevMessages, newUserMessage]);

          try {
              const response = await axios.post('http://127.0.0.1:5000/chatbot/ask', {
                  question: inputValue,
                  inputLanguage,
                  outputLanguage, 
              });

              const { answer, sources, context } = response.data;
              const newAssistantMessage = {
                  text: answer,
                  sender: 'assistant',
                  context,
                  sources,
              };

              setMessages((prevMessages) => [...prevMessages, newAssistantMessage]);
          } catch (error) {
              
              const backendMessage = error.response?.data?.error || 'Unable to get a response from the chatbot.';
              setError(backendMessage);

              const errorMessage = {
                  text: `${backendMessage}`,
                  sender: 'assistant',
              };
              setMessages((prevMessages) => [...prevMessages, errorMessage]);

              setTimeout(() => setError(''), 3000);
          }
          setInputValue('');
      }
  };


  const startNewConversation = async () => {
    try {
      await axios.post('http://127.0.0.1:5000/chatbot/start-new-conversation');
      setMessages([]);
      setInputValue('');
      setSuccess('Started new conversation');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      setError('Failed to start new conversation');
      setTimeout(() => setError(''), 3000);
    }
  };

  const handleInputLanguageChange = (event) => {
    const selectedLanguage = event.target.value;
    setInputLanguage(selectedLanguage);
  };
  
  const handleOutputLanguageChange = (event) => {
    const selectedLanguage = event.target.value;
    setOutputLanguage(selectedLanguage);
  };

  useEffect(() => {
    localStorage.setItem('inputLanguage', inputLanguage);
    localStorage.setItem('outputLanguage', outputLanguage);
  }, [inputLanguage, outputLanguage]);

  const renderMessages = (messageList) => (
    messageList.length === 0 ? (
      <div className="no-messages">No conversation yet.</div>
    ) : (
      messageList.map((msg, idx) => (
        <div
          key={idx}
          className={`message-container ${msg.sender === 'user' ? 'user-message' : 'assistant-message'}`}
        >
          <div className={`message-bubble ${msg.sender === 'user' ? 'user-bubble' : 'assistant-bubble'}`}>
            <div>{msg.text}</div>
          </div>
        </div>
      ))
    )
  );
  
  return (
    <div>
      <div className="tabs">
        <button
          className={`tab ${selectedTab === 'conversation' ? 'active' : ''}`}
          onClick={() => setSelectedTab('conversation')}
        >
          Conversation
        </button>
        <button
          className={`tab ${selectedTab === 'history' ? 'active' : ''}`}
          onClick={() => setSelectedTab('history')}
        >
          Chat History
        </button>
        <button
          className={`tab ${selectedTab === 'upload' ? 'active' : ''}`}
          onClick={() => setSelectedTab('upload')}
        >
          Document Upload
        </button>
      </div>

      <div className="content-wrapper">
        {selectedTab === 'conversation' && (
          <div id="conversation" className="content active">
            <div className="chat-interface">
              <div className="chat-messages">
                {renderMessages(messages)}
              </div>

              <div className="language-selector">
                <div className="language-group">
                  <label>Input Language</label>
                  <div className="language-dropdown">
                    <select
                      id="inputLanguage"
                      value={inputLanguage}
                      onChange={handleInputLanguageChange}
                      disabled={isLoadingLanguages}
                    >
                      <option value="auto-detect">Auto-detect</option>
                      {availableLanguages.map((lang) => (
                        <option key={lang.name} value={lang.name}>
                          {lang.name}
                        </option>
                      ))}
                    </select>
                    {isLoadingLanguages && <span className="loading-text">Loading...</span>}
                  </div>
                </div>

                <div className="language-group">
                  <label>Output Language</label>
                  <div className="language-dropdown">
                    <select
                      id="outputLanguage"
                      value={outputLanguage || "English"}
                      onChange={handleOutputLanguageChange}
                      disabled={isLoadingLanguages}
                    >
                      {availableLanguages.map((lang) => (
                        <option key={lang.name} value={lang.name}>
                          {lang.name}
                        </option>
                      ))}
                    </select>
                    {isLoadingLanguages && <span className="loading-text">Loading...</span>}
                  </div>
                </div>
              </div>

              <div className="chat-input">
                <input
                  type="text"
                  className="message-input"
                  placeholder="Type your message..."
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                />
                <button onClick={handleSend} className="send-button">
                  <Send className="send-icon" />
                  Send
                </button>
              </div>

              <div className="button-container">
                <button className="new-chat-button" onClick={startNewConversation}>
                  Start New Conversation
                </button>
                <AudioChat 
                  onNewMessage={(message) => setMessages(prevMessages => [...prevMessages, message])}
                  inputLanguage={inputLanguage}
                  outputLanguage={outputLanguage}
                />
              </div>
            </div>
          </div>
        )}

        {selectedTab === 'upload' && (
          <div id="upload" className="content active">
            <UploadPdf />
            <UploadPowerPoint />
            <ProcessUrl />
            <ProcessYouTubeVideo />
          </div>
        )}

        {selectedTab === 'history' && (
          <div id="history" className="content active">
            <div className="chat-history-container">
              {renderMessages(history)}
            </div>
            <button className="clear-history-button" onClick={handleClearHistory}>
              Clear History
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatInterface;