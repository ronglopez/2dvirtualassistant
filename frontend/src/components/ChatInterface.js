// Import necessary libraries
import React, { useReducer, useEffect, useRef, useState, useCallback } from 'react';
import axios from 'axios';
import { ReactMic } from 'react-mic';
import { Button, Form, Col, Row, InputGroup, FormControl, Dropdown } from 'react-bootstrap';
import { io } from 'socket.io-client';

// Define Initial State
const initialState = {
  userInput: '',
  chatLog: [],
  isProcessing: false,
  isRecording: false,
  isListening: false,
};

// Define Reducer Function
const reducer = (state, action) => {
  switch (action.type) {
    case 'SET_USER_INPUT':
      return { ...state, userInput: action.payload };
    case 'SET_IS_PROCESSING':
      return { ...state, isProcessing: action.payload };
    case 'SET_IS_RECORDING':
      return { ...state, isRecording: action.payload };
    case 'SET_IS_LISTENING':
      return { ...state, isListening: action.payload };
    case 'ADD_CHAT_ENTRY':
      return { ...state, chatLog: [...state.chatLog, action.payload] };
    default:
      return state;
  }
};

// Main Chat Functions
function ChatInterface({ chatStarted, handleEndClick }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const inputRef = useRef(null);
  const isListeningRef = useRef(state.isListening);
  const recordingModeRef = useRef(false);
  const recordingTimeoutRef = useRef(null);
  const periodicMessageIntervalRef = useRef(null);
  const [isTimerPaused, setIsTimerPaused] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const fileInputRef = useRef(null);

  // Timers
  const PERIODIC_MESSAGE_INTERVAL = 60000; // seconds in the thousands, ie. 60 seconds = 60000
  const RECORD_MESSAGE_TIMEOUT = 10000; // seconds in the thousands, ie. 10 seconds = 10000

  // State to hold available devices
  const [devices, setDevices] = useState([]);

  // State to hold selected device index
  const [selectedDeviceIndex, setSelectedDeviceIndex] = useState(1); // Default to 1
  const [selectedDeviceLabel, setSelectedDeviceLabel] = useState("Select Device");

  // Create a ref to hold the socket connection
  const socketRef = useRef(null);

  // State to hold thumbnail URL
  const [thumbnailURL, setThumbnailURL] = useState(null);

  /// Function to handle file change and generate thumbnail
  const handleFileChange = (event) => {
    const file = event.target.files[0];
    setUploadedFile(file);

    // Generate thumbnail URL
    const reader = new FileReader();
    reader.onloadend = () => {
      setThumbnailURL(reader.result);
    };
    reader.readAsDataURL(file);
  };

  // Function to remove uploaded file and clear thumbnail
  const removeUploadedFile = () => {
    setUploadedFile(null);
    setThumbnailURL(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // Handle changes in the text input field
  const handleInputChange = (event) => {
    dispatch({ type: 'SET_USER_INPUT', payload: event.target.value });
  };

  // Handle the submission of text input to the backend
  const handleSubmit = async (e) => {
    e.preventDefault();
  
    // Pause the periodic message timer
    console.log("Pausing periodic message timer due to recording...");
    setIsTimerPaused(true);
  
    dispatch({ type: 'SET_IS_PROCESSING', payload: true });
  
    // Trim whitespace
    const trimmedInput = state.userInput.trim();
  
    // Create FormData to hold both text and file data
    const formData = new FormData();
    formData.append('input', trimmedInput);
  
    if (uploadedFile) {
      formData.append('file', uploadedFile);
  
      // Add status message that an image was uploaded
      dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'system', content: `Image uploaded: ${uploadedFile.name}` } });
    }

    if (trimmedInput) {    
      // Add user's message to chat log for display
      dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'user', content: trimmedInput } });
    }
  
    try {
      
      // Send FormData to backend and get AI's response
      const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/input_message`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
  
      const aiResponse = response.data;
  
      // Add AI's response to chat log
      dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'assistant', content: aiResponse } });
  
      // Reset the file input to "No file chosen"
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
  
      // Resume the periodic message timer
      console.log("Resuming periodic message timer after AI response...");
      setIsTimerPaused(false);
  
    } catch (error) {
      console.error("Error communicating with backend:", error);
    }
  
    // Clear the input field and uploaded file state
    dispatch({ type: 'SET_USER_INPUT', payload: '' });
    setUploadedFile(null);
    dispatch({ type: 'SET_IS_PROCESSING', payload: false });
  
    // Focus on the input field after processing is complete
    setTimeout(() => {
      inputRef.current.focus();
    }, 100);
  
    // Clear the existing interval and set up a new one
    console.log("Clearing and resetting periodic message interval due to text input...");
    clearInterval(periodicMessageIntervalRef.current);
    periodicMessageIntervalRef.current = setInterval(fetchPeriodicMessage, PERIODIC_MESSAGE_INTERVAL);
  };
  
  // Handle the stopping of voice recording
  const onStop = async (recordedBlob) => {

    if (recordingModeRef.current) { // Only process if in recording mode
      recordingModeRef.current = false;

      // Create a FormData object to send the audio blob to the backend
      const formData = new FormData();
      formData.append('file', recordedBlob.blob);

      try {

        // Send the audio blob to the backend for transcription and AI response
        const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/voice`, formData);
        const { transcription, ai_response } = response.data;
        
        // Add the transcribed audio and AI's response to the chat log
        dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'user', content: transcription } });
        dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'assistant', content: ai_response } });

        // Resume the periodic message timer
        console.log("Resuming periodic message timer after AI response...");
        setIsTimerPaused(false);

      } catch (error) {
        console.error("Error sending audio to backend:", error);
      }
    }
  };

  // Handle the voice recording
  const handleRecording = () => {

    // Check if the user is starting to record
    if (!state.isRecording) {

      // Pause the periodic message timer
      console.log("Pausing periodic message timer due to recording...");
      setIsTimerPaused(true);

      // If not currently recording, start recording and set the recording mode ref
      recordingModeRef.current = true;
      dispatch({ type: 'SET_IS_RECORDING', payload: true });

      // Set a timeout to stop the recording after 10 seconds and save the timeout ID
      recordingTimeoutRef.current = setTimeout(() => {
        dispatch({ type: 'SET_IS_RECORDING', payload: false });
      }, RECORD_MESSAGE_TIMEOUT);

    } else {

      // If currently recording, stop the recording and clear the timeout
      dispatch({ type: 'SET_IS_RECORDING', payload: false });

      if (recordingTimeoutRef.current) {
        clearTimeout(recordingTimeoutRef.current);
        recordingTimeoutRef.current = null;
      }

      // Clear the existing interval and set up a new one for periodic messages
      console.log("Clearing and resetting periodic message interval due to recording...");
      clearInterval(periodicMessageIntervalRef.current);
      periodicMessageIntervalRef.current = setInterval(fetchPeriodicMessage, PERIODIC_MESSAGE_INTERVAL);
    }
  };

  // Handle the listening state
  const handleListening = () => {
    if (state.isListening) {
      // If currently listening, stop listening and emit 'stop_listening' event
      dispatch({ type: 'SET_IS_LISTENING', payload: false });
      if (socketRef.current) {
        socketRef.current.emit('stop_listening');
      }
    } else {
      // If not currently listening, start listening
      dispatch({ type: 'SET_IS_LISTENING', payload: !state.isListening });
    }
  };

  // Handle device selection
  const handleDeviceChange = (eventKey) => {
    setSelectedDeviceIndex(eventKey);
    setSelectedDeviceLabel(devices[eventKey]?.label || "Select Device");
  };

  // Function to fetch a periodic message from the backend
  const fetchPeriodicMessage = useCallback(async () => {
    if (isTimerPaused) {
      console.log("Periodic message timer is paused.");
      return;
    }
    
    console.log("Fetching periodic message...");

    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/periodic_message`);
      const message = response.data;

      // Add the message to the chat log
      dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'assistant', content: message } });
    } catch (error) {
      console.error("Error fetching periodic message from backend:", error);
    }
  }, [isTimerPaused]);

  // Set up an interval to call fetchPeriodicMessage every 10 seconds, but pausing and resetting in Listen mode
  useEffect(() => {
    if (!chatStarted) return;

    if (state.isListening) {
      console.log("Pausing periodic message timer due to listening mode...");
      clearInterval(periodicMessageIntervalRef.current); // Clear the existing interval
    } else {
      console.log("Setting up or resuming periodic message interval...");
      clearInterval(periodicMessageIntervalRef.current); // Clear the existing interval, if any
      periodicMessageIntervalRef.current = setInterval(fetchPeriodicMessage, PERIODIC_MESSAGE_INTERVAL); // Set up a new interval
    }

    return () => {
      console.log("Clearing periodic message interval...");
      clearInterval(periodicMessageIntervalRef.current);
    };
  }, [state.isListening, fetchPeriodicMessage, chatStarted]);

  // Fetch available devices when the component mounts
  useEffect(() => {
    if (!chatStarted) return;

    if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
      navigator.mediaDevices.enumerateDevices()
        .then(deviceList => {
          // Filter for audio input devices (microphones)
          const microphones = deviceList.filter(device => device.kind === 'audioinput');
          setDevices(microphones);
  
          // Update the default device label if devices are available
          if (microphones.length > 0 && selectedDeviceIndex < microphones.length) {
            setSelectedDeviceLabel(microphones[selectedDeviceIndex]?.label || "Select Device");
          }
  
        })
        .catch(error => {
          console.error('Error fetching devices:', error);
        });
    } else {
      console.warn('Media devices are not supported in this browser.');
      // You can also set a state here to notify the user or disable certain features
    }
  }, [chatStarted, selectedDeviceIndex]);

  // Fetch the greeting message when the component mounts
  useEffect(() => {
    if (!chatStarted) return;

    const fetchGreeting = async () => {
      try {
        const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/greeting`);
        const greeting = response.data;

        // Add AI's greeting to chat log
        dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'assistant', content: greeting } });
      } catch (error) {
        console.error("Error fetching greeting from backend:", error);
      }
    };

    fetchGreeting();
  }, [chatStarted]);

  // Handle the listening state
  useEffect(() => {
    if (!chatStarted) return;

    isListeningRef.current = state.isListening;
  }, [state.isListening, chatStarted]);

  // Handle the listening loop
  useEffect(() => {
    if (!chatStarted) return;

    if (state.isListening) {
      
      // Create a Socket.IO connection
      socketRef.current = io(`${process.env.REACT_APP_WEBSOCKET_URL}`);
  
      // Set up event listeners for the Socket.IO connection
      socketRef.current.on('listening_result', (data) => {
        const { transcription, ai_response } = data;
  
        // Add the transcribed audio and AI's response to the chat log
        dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'user', content: transcription } });
        dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'assistant', content: ai_response } });
  
        // Emit the 'start_listening' event to start listening with the selected device index
        socketRef.current.emit('start_listening', { device_index: selectedDeviceIndex });
      });

      socketRef.current.on('listening_periodic_message', (message) => {
        dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'assistant', content: message } });

        // Emit the 'start_listening' event to start listening with the selected device index
        socketRef.current.emit('start_listening', { device_index: selectedDeviceIndex });
      });

      socketRef.current.on('listening_deactivated', function(data) {
        const { ai_response } = data;

        // Stop listening and update the button state
        dispatch({ type: 'SET_IS_LISTENING', payload: false });
        console.log("Listening mode deactivated for inactivity ");

        // Add the transcribed audio and AI's response to the chat log
        dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'assistant', content: ai_response } });
      });
  
      // Emit the 'start_listening' event to start listening with the selected device index
      socketRef.current.emit('start_listening', { device_index: selectedDeviceIndex });

      // Quit listening on error
      socketRef.current.on('listening_error', (error) => {

        // Stop listening and update the button state
        dispatch({ type: 'SET_IS_LISTENING', payload: false });
        console.error("Listening error:", error);
      });
  
      // Quit listening on quit keyword
      socketRef.current.on('listening_quit', (data) => {
        const { transcription, ai_response } = data;
  
        // Stop listening and update the button state
        dispatch({ type: 'SET_IS_LISTENING', payload: false });
        console.error("Listening quit:", data);
  
        // Add the transcribed audio and AI's response to the chat log
        dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'user', content: transcription } });
        dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'assistant', content: ai_response } });
      });
  
      } else if (socketRef.current) {
        // Disconnect the Socket.IO connection if isListening is false
        socketRef.current.emit('stop_listening');
        socketRef.current.disconnect();
        socketRef.current = null;
      }
    
      // Clean up the Socket.IO connection when the component is unmounted
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, [state.isListening, selectedDeviceIndex, chatStarted]);

  // Frontend UI
  return (
    <div className="chat-interface d-flex flex-column justify-content-between">
      <Row className="chat-header__top">
        <Col xs={12}>
          <div className="d-inline-block me-3">
            <p className="text-light fs-7 fw-semibold mb-1">Select input device</p>
          </div>
          <div className="d-inline-block">
            <Dropdown onSelect={handleDeviceChange}>
              <Dropdown.Toggle variant='secondary' id="dropdown-basic">
                <i className="fas fa-microphone"></i> {/* This is your microphone icon */}
                {" "}
                {selectedDeviceLabel.length > 20 ? selectedDeviceLabel.substring(0, 25) + "..." : selectedDeviceLabel}
              </Dropdown.Toggle>

              <Dropdown.Menu>
                {devices.map((device, index) => (
                  <Dropdown.Item key={device.deviceId} eventKey={index}>
                    {device.label}
                  </Dropdown.Item>
                ))}
              </Dropdown.Menu>
            </Dropdown>
          </div>
        </Col>
      </Row>
      <Row className="chat-header align-items-center">
        <Col className="text-start">
          <div className='d-flex flex-row align-items-center'>
            <div className='profile-img'></div>
            <div className=''>
              <p className='ai-name'>Mira Lastname</p>
              <p className='ai-status mb-0'>
                {state.isProcessing ? <>Thinking<span className="ellipsis"></span></> : 
                state.isRecording ? <>Listening to you<span className="ellipsis"></span></> : 
                state.isListening ? <>Listening to you<span className="ellipsis"></span></> : 
                'Ready to chat!'}
              </p>
            </div>
          </div>
        </Col>
        <Col className="text-end">
          <Button variant="danger" onClick={handleEndClick}>
            End
          </Button>
        </Col>
      </Row>

      {/* Display chat log */}
      <div className="chat-log d-flex flex-column justify-content-end h-100 overflow-y-auto">
        {state.chatLog.map((entry, index) => (
          <div key={index} className={`chat-entry ${entry.role}`}>
            <div className='chat-entry__bubble'>
              <p>{entry.content}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="chat-footer">
        {/* Device selection dropdown */}
        <Row className="chat-sub-footer justify-content-center">
          <Col xs={12}>
            {/* Audio listen controls */}
            <Row className="audio-controls">
              <Col xs={12}>
                <Button variant="primary" className='listen-btn' onClick={handleListening} disabled={state.isRecording} aria-label="Listening mode button">
                  <i className="fas fa-broadcast-tower me-2"></i>
                  {state.isListening ? "Listening..." : "Start Listen Mode"}
                </Button>
              </Col>
            </Row>
          </Col>
        </Row>

        {/* Input form */}
        <Form onSubmit={handleSubmit} className="chat-footer__input">

          {/* Soundwave */}
          <ReactMic
            record={state.isRecording || state.isListening}
            className={`sound-wave ${state.isRecording || state.isListening ? 'visible' : 'hidden'}`}
            onStop={onStop}
            strokeColor="#000000"
            backgroundColor="#ffffff"
            aria-label="Audio recorder"
          />

          {/* Text input */}
          <InputGroup className="gap-2">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".jpg,.jpeg,.png"
              style={{ display: 'none' }}
            />
            <Button variant="light" onClick={() => fileInputRef.current.click()} disabled={state.isProcessing}>
              <i className="fas fa-image"></i>
            </Button>
            <FormControl
              type="text"
              value={state.userInput}
              onChange={handleInputChange}
              placeholder="Type your message..."
              disabled={state.isProcessing}
              ref={inputRef}
              aria-label="Chat input field"
              maxLength={100}
            />
            {(state.isProcessing || state.userInput.trim() || uploadedFile) ? null : (
              <Button variant="light" onClick={handleRecording} disabled={state.isListening}>
                {state.isRecording ? <i className="fas fa-stop"></i> : <i className="fas fa-microphone"></i>}
              </Button>
            )}
            {(state.isProcessing || state.userInput.trim() || uploadedFile) ? (
              <Button variant="light" className="send-btn" type="submit" disabled={state.isProcessing || (!state.userInput.trim() && !uploadedFile)}>
                <i className="fas fa-paper-plane"></i>
              </Button>
            ) : null}
          </InputGroup>

          {/* Chip to display uploaded file name and thumbnail */}
          {uploadedFile && (
            <div className="chat-footer__upload-image-badge">
              <span className="badge d-inline-flex bg-secondary justify-content-between align-items-center">
                <div className="chat-input__badge-content d-flex align-items-center">
                  <div className="chat-footer__uploaded-image me-3">
                    {thumbnailURL && <img src={thumbnailURL} alt="Upload Thumbnail" />}
                  </div>
                  <div className="chat-input__file-name text-start">
                    <p className="text-truncate mb-0">{uploadedFile.name}</p>
                  </div>
                </div>
                <Button variant="secondary" className="close" aria-label="Close" onClick={removeUploadedFile}>
                  &times;
                </Button>
              </span>
            </div>
          )}
        </Form>
      </div>
    </div>
  );
}

export default ChatInterface;
