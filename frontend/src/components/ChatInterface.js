// Import necessary libraries
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { ReactMic } from 'react-mic';
import './ChatInterface.css';

function ChatInterface() {
  const [userInput, setUserInput] = useState('');
  const [chatLog, setChatLog] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const isListeningRef = useRef(isListening);
  const inputRef = useRef(null);

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
      const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/ask`, { input: userInput });
      const aiResponse = response.data;
      
      // Add AI's response to chat log
      setChatLog(prevLog => [...prevLog, { role: 'assistant', content: aiResponse }]);
    } catch (error) {
      console.error("Error communicating with backend:", error);
    }
    
    // Clear the input field
    setUserInput('');
    setIsProcessing(false);

    // Focus on the input field after processing is complete
    setTimeout(() => {
      inputRef.current.focus();
    }, 100);    
  };

  // Handle the stopping of voice recording
  const onStop = async (recordedBlob) => {
    // Create a FormData object to send the audio blob to the backend
    const formData = new FormData();
    formData.append('file', recordedBlob.blob);

    try {
      // Send the audio blob to the backend for transcription and AI response
      const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/voice`, formData);
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
    if (isRecording) {  // If stopping the recording
      setTimeout(() => {
        setIsRecording(false);
      }, 6000);  // Stop recording after 6 seconds
    }
  };

  const handleListening = () => {
    setIsListening((prevIsListening) => !prevIsListening);
  };

  // Fetch the greeting message when the component mounts
  useEffect(() => {
    const fetchGreeting = async () => {
      try {
        const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/greeting`);
        const greeting = response.data;
        
        // Add AI's greeting to chat log
        setChatLog([{ role: 'assistant', content: greeting }]);
      } catch (error) {
        console.error("Error fetching greeting from backend:", error);
      }
    };

    fetchGreeting();
  }, []); // Empty dependency array ensures this runs only once

  useEffect(() => {
    isListeningRef.current = isListening;
  }, [isListening]);

  // Handle the listening loop
  useEffect(() => {
    if (isListening) {
      const listenLoop = async () => {
        try {
          while (isListeningRef.current) {

            // Make a request to the /listen endpoint
            const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/listen`);

            const { transcription, ai_response } = response.data;

            // Add the transcribed audio and AI's response to the chat log
            setChatLog((prevLog) => [...prevLog, { role: 'user', content: transcription },]);
            setChatLog((prevLog) => [...prevLog, { role: 'assistant', content: ai_response },]);

            // Optional: Add a delay to prevent continuous rapid polling
            await new Promise((resolve) => setTimeout(resolve, 100));
          }
        } catch (error) {
          
        console.error("Error listening to audio:", error);
      }
    };

    listenLoop();
  }
}, [isListening]); // This effect runs whenever isListening changes

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
          ref={inputRef}
          aria-label="Chat input field"  // <-- Added for accessibility
        />
        <button type="submit" disabled={isProcessing || !userInput.trim()} aria-label="Send message">
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
          aria-label="Audio recorder"
        />
        <button onClick={handleRecording} aria-label="Audio recording button">
          {isRecording ? "Recording..." : "Start Recording"}
        </button>
        <button onClick={handleListening} aria-label="Listening mode button">
          {isListening ? "Listening..." : "Start Listening"}
        </button>
      </div>
    </div>
  );
}

export default ChatInterface;
