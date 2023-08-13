import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ReactMic } from 'react-mic';
import './ChatInterface.css';

function ChatInterface() {
  const [userInput, setUserInput] = useState('');
  const [chatLog, setChatLog] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);

  // Handle changes in the text input field
  const handleInputChange = (event) => {
    setUserInput(event.target.value);
  };

  // Handle the submission of text input to the backend
  const handleSubmit = async (e) => {
    e.preventDefault();

    setIsProcessing(true);
    
    // Add user's message to chat log
    setChatLog([...chatLog, { role: 'user', content: userInput }]);
    
    try {
      // Send user's message to backend and get AI's response
      const response = await axios.post('http://localhost:5000/ask', { input: userInput });
      const aiResponse = response.data;
      
      // Add AI's response to chat log
      setChatLog(prevLog => [...prevLog, { role: 'assistant', content: aiResponse }]);
    } catch (error) {
      console.error("Error communicating with backend:", error);
    }
    
    // Clear the input field
    setUserInput('');
    setIsProcessing(false)
  };

  // Handle the stopping of voice recording
  const onStop = async (recordedBlob) => {
    // Create a FormData object to send the audio blob to the backend
    const formData = new FormData();
    formData.append('file', recordedBlob.blob);

    try {
      // Send the audio blob to the backend for transcription and AI response
      const response = await axios.post('http://localhost:5000/voice', formData);
      const { transcription, ai_response } = response.data;
      
      // Add the transcribed audio and AI's response to the chat log
      setChatLog(prevLog => [...prevLog, { role: 'user', content: transcription }]);
      setChatLog(prevLog => [...prevLog, { role: 'assistant', content: ai_response }]);
    } catch (error) {
      console.error("Error sending audio to backend:", error);
    }
  };

  const handleRecording = () => {
    setIsRecording(prevIsRecording => !prevIsRecording);
    if (!isRecording) {  // If starting to record
      setTimeout(() => {
        if (!isRecording) {
          setIsRecording(false);
        }
      }, 6000);  // Stop recording after 6 seconds
    }
  };

  // Fetch the greeting message when the component mounts
  useEffect(() => {
    const fetchGreeting = async () => {
      try {
        const response = await axios.get('http://localhost:5000/greeting');
        const greeting = response.data;
        
        // Add AI's greeting to chat log
        setChatLog([{ role: 'assistant', content: greeting }]);
      } catch (error) {
        console.error("Error fetching greeting from backend:", error);
      }
    };

    fetchGreeting();
  }, []); // <-- The empty dependency array ensures this runs only once when the component mounts

  return (
    <div className="chat-interface">
      {/* Display chat log */}
      <div className="chat-log">
        {chatLog.map((entry, index) => (
          <div key={index} className={`chat-entry ${entry.role}`}>
            <p>{entry.content}</p>
          </div>
        ))}
      </div>
      
      {/* Text input form */}
      <form className="chat-input" onSubmit={handleSubmit}>
        <input
          type="text"
          value={userInput}
          onChange={handleInputChange}
          placeholder="Type your message..."
          disabled={isProcessing}
        />
        <button type="submit" disabled={isProcessing || !userInput.trim()}>
          {isProcessing ? "Sending..." : "Send"}
        </button>
      </form>
      
      {/* Audio recording controls */}
      <div className="audio-controls">
        <ReactMic
          record={isRecording}
          className="sound-wave"
          onStop={onStop}
          strokeColor="#000000"
          backgroundColor="#FF4081"
        />
        <button onClick={handleRecording}>
          {isRecording ? "Recording..." : "Start Recording"}
        </button>
      </div>
    </div>
  );
}

export default ChatInterface;
