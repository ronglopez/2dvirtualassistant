import React, { useState } from 'react';
import axios from 'axios';
import { ReactMic } from 'react-mic';

import './ChatInterface.css';

function ChatInterface() {
  const [userInput, setUserInput] = useState('');
  const [chatLog, setChatLog] = useState([]);
  const [isRecording, setIsRecording] = useState(false);

  const handleInputChange = (event) => {
    setUserInput(event.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    // Add user's message to chat log
    setChatLog([...chatLog, { role: 'user', content: userInput }]);
    
    try {
      // Send user's message to backend
      const response = await axios.post('http://localhost:5000/ask', { input: userInput });
      const aiResponse = response.data;
      
      // Add AI's response to chat log
      setChatLog(prevLog => [...prevLog, { role: 'assistant', content: aiResponse }]);
    } catch (error) {
      console.error("Error communicating with backend:", error);
    }
    
    // Clear the input field
    setUserInput('');
  };

  const onData = (recordedBlob) => {
    console.log('chunk of real-time data is: ', recordedBlob);
  }

  const onStop = async (recordedBlob) => {
    console.log('recordedBlob:', recordedBlob);
  
    // Create a FormData object to send the audio blob to the backend
    const formData = new FormData();
    formData.append('file', recordedBlob.blob);
  
    try {
      // Send the audio blob to the backend
      const response = await axios.post('http://localhost:5000/voice', formData);
      const { transcription, ai_response } = response.data;  // Destructure the response
  
      // Add the transcribed audio to the chat log
      setChatLog(prevLog => [...prevLog, { role: 'user', content: transcription }]);
  
      // Add AI's response to chat log
      setChatLog(prevLog => [...prevLog, { role: 'assistant', content: ai_response }]);
    } catch (error) {
      console.error("Error sending audio to backend:", error);
    }
  };  

  return (
    <div className="chat-interface">
      <div className="chat-log">
        {chatLog.map((entry, index) => (
          <div key={index} className={`chat-entry ${entry.role}`}>
            <p>{entry.content}</p>
          </div>
        ))}
      </div>
      <form className="chat-input" onSubmit={handleSubmit}>
        <input
          type="text"
          value={userInput}
          onChange={handleInputChange}
          placeholder="Type your message..."
        />
        <button type="submit">Send</button>
      </form>
      <div className="audio-controls">
        <ReactMic
          record={isRecording}
          className="sound-wave"
          onStop={onStop}
          onData={onData}
          strokeColor="#000000"
          backgroundColor="#FF4081"
        />
        <button onClick={() => setIsRecording(true)}>Start Recording</button>
        <button onClick={() => setIsRecording(false)}>Stop Recording</button>
      </div>
    </div>
  );
}

export default ChatInterface;
