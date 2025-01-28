import React, { useState } from 'react';
import axios from 'axios';
import { Mic, MicOff } from 'lucide-react';

const AudioChat = ({ onNewMessage, inputLanguage = 'auto-detect', outputLanguage = 'English' }) => {
  const [isListening, setIsListening] = useState(false);
  const [status, setStatus] = useState('');
  // const [audioUrl, setAudioUrl] = useState('');

  const startAudioChat = async () => {
    setIsListening(true);
    setStatus('Listening...');

    try {
      // Initiate continuous audio chat
      const response = await axios.post('http://127.0.0.1:5000/speech/speech_chat', {
        inputLanguage,
        outputLanguage
      });

      if (response.data.userMessage) {
        // Display user's query
        onNewMessage({
          text: response.data.userMessage,
          sender: 'user'
        });
      }

      if (response.data.assistantResponse) {
        // Display assistant's response
        onNewMessage({
          text: response.data.assistantResponse,
          sender: 'assistant'
        });

        const audioUrl = response.data.audioUrl;
        if (audioUrl) {
          const audio = new Audio(audioUrl);
          audio.play().catch(error => {
            console.error("Failed to play audio:", error);
          });
        }
      }

      // Listen for another query after response
      if (response.data.status !== 'stopped') {
        startAudioChat();
      }

      setStatus('');
    } catch (error) {
      console.error('Audio chat error:', error);
      setStatus('Error occurred');
      onNewMessage({
        text: 'Sorry, there was an error processing your voice input.',
        sender: 'assistant'
      });
    } finally {
      setIsListening(false);
    }
  };

  return (
    <button
      onClick={startAudioChat}
      disabled={isListening}
      className={`audio-button ${isListening ? '' : 'new-chat-button'}`}
    >
      { isListening ? (<Mic />) : (<MicOff />) }
      <span>{status || 'Start Voice Chat'}</span>
</button>

  );
};

export default AudioChat;