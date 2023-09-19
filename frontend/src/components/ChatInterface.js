// Import necessary libraries
import React, { useReducer, useEffect, useRef, useState, useCallback } from 'react';
import axios from 'axios';
import { ReactMic } from 'react-mic';
import { Button, Form, Col, Row, InputGroup, Nav, Toast, FormControl, Dropdown } from 'react-bootstrap';
import io from 'socket.io-client';

// Define Initial State
const initialState = {

  // SettingsPanel
  settings: {
    SENTIMENT_SCORES: {}
  },
  isLoaded: false,
  isChanged: false,
  originalSettings: {},
  activeTab: 'main',
  isStreaming: false,

  // ChatInterface
  userInput: '',
  chatLog: [],
  isProcessing: false,
  isRecording: false,
  isListening: false,
};

// Hardcoded options for dropdowns (Update these values as they come out)
const hardcodedPersonalities = ['Debug', 'Rin'];
const openaiModels = ["gpt-3.5-turbo", "gpt-4"];
const openaiEmbeddingModels = ["text-embedding-ada-002"];
const openaiWhisperModels = ["whisper-1"];
const elabsModels = ["eleven_monolingual_v1"];

// Define Reducer Function
const reducer = (state, action) => {
  switch (action.type) {

    // SettingsPanel
    case 'SET_SETTINGS':
      return { ...state, settings: action.payload, originalSettings: action.payload, isLoaded: true };
    case 'REVERT_SETTINGS':
      return { ...state, settings: state.originalSettings, isChanged: false };
    case 'UPDATE_SETTINGS':
      return { ...state, settings: action.payload, originalSettings: action.payload, isChanged: false };
    case 'SET_CHANGED':
      return { ...state, settings: action.payload, isChanged: true };
    case 'SET_NOT_CHANGED':
      return { ...state, isChanged: false };
    case 'SET_ACTIVE_TAB':
      return { ...state, activeTab: action.payload };
    case 'SET_IS_STREAMING':
      return { ...state, isStreaming: action.payload };
    case 'UPDATE_SETTING':
      return {
        ...state,
        settings: {
          ...state.settings,
          [action.payload.key]: action.payload.value
        },
        isChanged: true
      };

    // ChatInterface
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
const ChatInterface = ({ chatStarted, handleEndClick }) => {
  
  //
  // ChatInterface const
  //

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
  const PERIODIC_MESSAGE_INTERVAL = 600000; // seconds in the thousands, ie. 60 seconds = 60000
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
      dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'system', content: `Image uploaded: ${uploadedFile.name}`, message_from: 'image-uploader' } });
    }

    if (trimmedInput) {    
      // Add user's message to chat log for display
      dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'user', content: trimmedInput, message_from: 'admin' } });
    }
  
    try {
      
      // Send FormData to backend and get AI's response
      const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/input_message/input_message`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
  
      const aiResponse = response.data;
  
      // Add AI's response to chat log
      dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'assistant', content: aiResponse, message_from: 'ai' } });
  
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
        const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/voice/voice`, formData);
        const { transcription, ai_response } = response.data;
        
        // Add the transcribed audio and AI's response to the chat log
        dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'user', content: transcription, message_from: 'admin' } });
        dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'assistant', content: ai_response, message_from: 'ai' } });

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
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/periodic_message/periodic_message`);
      const message = response.data;

      // Add the message to the chat log
      dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'assistant', content: message, message_from: 'ai' } });
    } catch (error) {
      console.error("Error fetching periodic message from backend:", error);
    }
  }, [isTimerPaused]);


  //
  // SettingsPanel const
  //

  const isStreamingRef = useRef(state.isStreaming);

  // Create a ref to hold the socket connection
  const streamingSocketRef = useRef(null);

  // State for showing Toasts
  const [showSuccessToast, setShowSuccessToast] = useState(false);
  const [showFailureToast, setShowFailureToast] = useState(false);

  // State for Toast Message
  const [toastMessage, setToastMessage] = useState("");

  // State for YouTube Video ID and Streaming
  const [videoID, setVideoID] = useState("");

  // Get settings from backend
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/settings/get_settings`);
        dispatch({ type: 'SET_SETTINGS', payload: response.data.settings });
      } catch (error) {
        console.error(`Failed to fetch settings: ${error}`);
      }
    };

    fetchSettings();
  }, []);

  // Existing handleChange function
  const handleChange = (e) => {
    const { name, type } = e.target;
    let updatedValue;
  
    if (type === 'checkbox' || type === 'switch') {
      updatedValue = e.target.checked;
    } else if (type === 'range') {
      updatedValue = parseFloat(e.target.value);
    } else {
      updatedValue = e.target.value;
    }
  
    const updatedSettings = { ...state.settings, [name]: updatedValue };
    dispatch({ type: 'SET_CHANGED', payload: updatedSettings });
  };

  // Handle setting cancel button to revert changes
  const handleCancel = () => {
    dispatch({ type: 'REVERT_SETTINGS' });
  };

  // Handle setting update
  const handleSettingsSubmit = async () => {
    try {
      await axios.post(`${process.env.REACT_APP_BACKEND_URL}/settings/update_settings`, state.settings);
      dispatch({ type: 'SET_NOT_CHANGED' });
      dispatch({ type: 'SET_SETTINGS', payload: { ...state.settings } });
      setToastMessage("Settings updated successfully!");
      setShowSuccessToast(true);
    } catch (error) {
      setToastMessage("Failed to update settings.");
      setShowFailureToast(true);
    }
  };

  // Handle nav tabs
  const handleTabChange = (key) => {
    dispatch({ type: 'SET_ACTIVE_TAB', payload: key });
  };

  // Handle the streaming state
  const handleStreaming = () => {
    if (state.isStreaming) {
      // If currently streaming, stop streaming and emit 'stop_Streaming' event
      dispatch({ type: 'SET_IS_STREAMING', payload: false });
      if (streamingSocketRef.current) {
        streamingSocketRef.current.emit('stop_youtube_stream');
      }
    } else {
      // If not currently streaming, start streaming
      dispatch({ type: 'SET_IS_STREAMING', payload: true });
      if (streamingSocketRef.current) {
        streamingSocketRef.current.emit('start_youtube_stream', { videoID: videoID });
      }
    }
  };

  const handleManualProcessMessage = () => {
    streamingSocketRef.current.emit('manual_process_message');
  };


  //
  // SettingsPanel useEffect
  //

  // Handle the streaming state
  useEffect(() => {

    isStreamingRef.current = state.isStreaming;
  }, [state.isStreaming]);

  // Handle the streamingSocketRef connection and toast messages for streaming
  useEffect(() => {
    try {
      // Create a Socket.IO connection
      streamingSocketRef.current = io(`${process.env.REACT_APP_WEBSOCKET_URL}`);
  
      // Start streaming toast
      streamingSocketRef.current.on('success_streaming_toast', (data) => {
        const { toast_message } = data;
        setToastMessage(toast_message);
        setShowSuccessToast(true);
      });
  
      // Stop streaming toast
      streamingSocketRef.current.on('stopped_streaming_toast', (data) => {
        const { toast_message } = data;
        setToastMessage(toast_message);
        setShowSuccessToast(true);
      });
  
      // Error streaming toast
      streamingSocketRef.current.on('error_streaming_toast', (data) => {
        const { toast_message } = data;
        setToastMessage(toast_message);
        setShowFailureToast(true);
      });

      // Set up event listeners for the Socket.IO connection
      streamingSocketRef.current.on('new_message', (data) => {
        console.log("WORKS 3")

        const { ai_response, selected_message_content } = data;

        console.log("WORKS 4")
      
        // Your existing code to dispatch actions
        dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'system', content: selected_message_content, message_from: 'youtube' } });
        dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'assistant', content: ai_response, message_from: 'ai' } });
      });
      
    } catch (error) {
      console.error('An error occurred while toggling YouTube streaming:', error);
      setToastMessage(error);
      setShowFailureToast(true);
    }
  
    return () => {
      if (streamingSocketRef.current) {
        streamingSocketRef.current.disconnect();
      }
    };
  }, []);

  // Handle the streaming mode
  useEffect(() => {
    
    // Create a Socket.IO connection only if it does not exist
    streamingSocketRef.current = io(`${process.env.REACT_APP_WEBSOCKET_URL}`);

    // Set up event listeners for the Socket.IO connection
    streamingSocketRef.current.on('new_message', (data) => {
      console.log("WORKS 3")

      const { ai_response, selected_message_content } = data;

      console.log("WORKS 4")
    
      // Your existing code to dispatch actions
      dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'system', content: selected_message_content, message_from: 'youtube' } });
      dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'assistant', content: ai_response, message_from: 'ai' } });
    });

    // Cleanup function
    return () => {
      if (streamingSocketRef.current) {
        streamingSocketRef.current.disconnect();
        socketRef.current = null;
      }
    };
}, []);


  //
  // ChatInterface useEffect
  //

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
        const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/greeting/greeting`);
        const greeting = response.data;

        // Add AI's greeting to chat log
        dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'assistant', content: greeting, message_from: 'ai' } });
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
        dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'user', content: transcription, message_from: 'admin' } });
        dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'assistant', content: ai_response, message_from: 'ai' } });
  
        // Emit the 'start_listening' event to start listening with the selected device index
        socketRef.current.emit('start_listening', { device_index: selectedDeviceIndex });
      });

      socketRef.current.on('listening_periodic_message', (message) => {
        dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'assistant', content: message, message_from: 'ai' } });

        // Emit the 'start_listening' event to start listening with the selected device index
        socketRef.current.emit('start_listening', { device_index: selectedDeviceIndex });
      });

      socketRef.current.on('listening_deactivated', function(data) {
        const { ai_response } = data;

        // Stop listening and update the button state
        dispatch({ type: 'SET_IS_LISTENING', payload: false });
        console.log("Listening mode deactivated for inactivity ");

        // Add the transcribed audio and AI's response to the chat log
        dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'assistant', content: ai_response, message_from: 'ai' } });
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
        dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'user', content: transcription, message_from: 'admin' } });
        dispatch({ type: 'ADD_CHAT_ENTRY', payload: { role: 'assistant', content: ai_response, message_from: 'ai' } });
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
        socketRef.current = null;
      }
    };
  }, [state.isListening, selectedDeviceIndex, chatStarted]);

  // Frontend UI
  return (
    <>
      {/* Settings Panel */}
      <Col md={6} lg={8} className="settings-panel">
        <Row className="settings-panel-content">

          {/* Success Toast */}
          <Toast className='text-bg-success position-fixed start-50 translate-middle' onClose={() => setShowSuccessToast(false)} show={showSuccessToast} delay={3000} autohide>
            <Toast.Body>{toastMessage}</Toast.Body>
          </Toast>

          {/* Failure Toast */}
          <Toast className='text-bg-danger position-fixed start-50 translate-middle' onClose={() => setShowFailureToast(false)} show={showFailureToast} delay={3000} autohide>
            <Toast.Body>{toastMessage}</Toast.Body>
          </Toast>

          <Col xs={12} className='settings-panel-content__header'>
            <h2 className='text-star mb-4'>Settings</h2>
          </Col>
          {state.isLoaded ? (
            <>
              {/* Tabs */}
              <Col xs={12} className='settings-panel-content__tabs'>
                <Nav variant="tabs" className='nav-fill nav-justified' activeKey={state.activeTab} onSelect={handleTabChange}>
                  <Nav.Item>
                    <Nav.Link eventKey="main">Main</Nav.Link>
                  </Nav.Item>
                  <Nav.Item>
                    <Nav.Link eventKey="audio">Audio</Nav.Link>
                  </Nav.Item>
                  <Nav.Item>
                    <Nav.Link eventKey="sentiment">Sentiment</Nav.Link>
                  </Nav.Item>
                  <Nav.Item>
                    <Nav.Link eventKey="moderation">Moderation</Nav.Link>
                  </Nav.Item>
                  <Nav.Item>
                    <Nav.Link eventKey="stream">Stream</Nav.Link>
                  </Nav.Item>
                  <Nav.Item>
                    <Nav.Link eventKey="advanced">Advanced</Nav.Link>
                  </Nav.Item>
                </Nav>
              </Col>

              {/* Tab Contents */}
              <Col xs={12}>
                <Row className='settings-panel-content__tab-content'>
                  <Col xs={12}>
                    {state.activeTab === 'main' && (
                      <Form className='row'>

                        {/* AI_PERSONALITY */}
                        <Form.Group className='settings-panel-content__form-item col-lg-6'>
                          <Form.Label>AI Personality:</Form.Label>
                          <Form.Control 
                            as="select" 
                            name="AI_PERSONALITY" 
                            className='form-select'
                            value={state.settings.AI_PERSONALITY} 
                            onChange={handleChange}
                          >
                            {hardcodedPersonalities.map((personality, index) => (
                              <option key={index} value={personality}>
                                {personality}
                              </option>
                            ))}
                          </Form.Control>
                          <div className="form-text">Select which AI personality to talk too</div>
                        </Form.Group>

                        {/* USER_NAME */}
                        <Form.Group className='settings-panel-content__form-item col-lg-6'>
                          <Form.Label>User Name:</Form.Label>
                          <Form.Control type="text" name="USER_NAME" value={state.settings.USER_NAME} onChange={handleChange} />
                          <div className="form-text">Name of the person talking to the AI</div>
                        </Form.Group>

                        {/* CHAR_LENGTH */}
                        <Form.Group className='settings-panel-content__form-item col-lg-6'>
                          <Form.Label>Max Response Length:</Form.Label>
                          <Form.Control type="number" name="CHAR_LENGTH" value={state.settings.CHAR_LENGTH} onChange={handleChange} />
                          <div className="form-text">Set max character length for AI response</div>
                        </Form.Group>

                        {/* MIN_SENTENCE_LENGTH */}
                        <Form.Group className='settings-panel-content__form-item col-lg-6'>
                          <Form.Label>Min. Sentence Character Length:</Form.Label>
                          <Form.Control type="number" name="MIN_SENTENCE_LENGTH" value={state.settings.MIN_SENTENCE_LENGTH} onChange={handleChange} />
                          <div className="form-text">Set min. sentence character length</div>
                        </Form.Group>

                        {/* MAX_TOKENS */}
                        <Form.Group className='settings-panel-content__form-item col-lg-6'>
                          <Form.Label>Max Tokens:</Form.Label>
                          <Form.Control type="number" name="MAX_TOKENS" value={state.settings.MAX_TOKENS} onChange={handleChange} />
                          <div className="form-text">Set max tokens for AI response</div>
                        </Form.Group>

                        {/* TEMPERATURE */}
                        <Form.Group className='settings-panel-content__form-item col-lg-6'>
                          <Form.Label>Temperature: {state.settings.TEMPERATURE}</Form.Label>
                          <Form.Control 
                            type="range" 
                            className='form-range'
                            name="TEMPERATURE"
                            min="0" 
                            max="1" 
                            step="0.1" 
                            value={state.settings.TEMPERATURE} 
                            onChange={handleChange} />
                          <div className="form-text">Closer to 1 the more creative the responses</div>
                        </Form.Group>

                        {/* MAX_MESSAGES */}
                        <Form.Group className='settings-panel-content__form-item col-lg-6'>
                          <Form.Label>Max Chat History Messages:</Form.Label>
                          <Form.Control type="number" name="MAX_MESSAGES" value={state.settings.MAX_MESSAGES} onChange={handleChange} />
                          <div className="form-text">Set max messages to hold in chat history</div>
                        </Form.Group>

                        {/* Form update buttons */}
                        <Col className='settings-panel-content__form-buttons' xs={12}>
                          <Row className='justify-content-end'>
                            <Col xs={6} lg={3}>
                              <Button variant="secondary" className='d-block w-100' onClick={handleCancel} disabled={!state.isChanged}>Cancel</Button>
                            </Col>
                            <Col xs={6} lg={3}>
                              <Button variant="primary" className='settings-update-btn d-block w-100' onClick={handleSettingsSubmit} disabled={!state.isChanged}>Update</Button>
                            </Col>
                          </Row>
                        </Col>
                      </Form>
                    )}
                    {state.activeTab === 'audio' && (
                      <Form className='row'>

                        {/* AI_VOICE */}
                        <Form.Group className='settings-panel-content__form-item col-lg-6'>
                          <Form.Label>AI Voice:</Form.Label>
                          <Form.Control type="text" name="AI_VOICE" value={state.settings.AI_VOICE} onChange={handleChange} />
                          <div className="form-text">For ELabs standard client output</div>
                        </Form.Group>

                        {/* AI_VOICE_ID */}
                        <Form.Group className='settings-panel-content__form-item col-lg-6'>
                          <Form.Label>AI Voice ID:</Form.Label>
                          <Form.Control type="text" name="AI_VOICE_ID" value={state.settings.AI_VOICE_ID} onChange={handleChange} />
                          <div className="form-text">For ELabs streaming mode</div>
                        </Form.Group>

                        {/* LISTEN_KEYWORD_QUIT */}
                        <Form.Group className='settings-panel-content__form-item col-lg-6'>
                          <Form.Label>Listen Mode Quit Word:</Form.Label>
                          <Form.Control type="text" name="LISTEN_KEYWORD_QUIT" value={state.settings.LISTEN_KEYWORD_QUIT} onChange={handleChange} />
                          <div className="form-text">Use a 2 sylable word and in lowercase</div>
                        </Form.Group>

                        {/* LISTEN_PERIODIC_MESSAGE_TIMER */}
                        <Form.Group className='settings-panel-content__form-item col-lg-6'>
                          <Form.Label>Send Periodic Message:</Form.Label>
                          <Form.Control type="number" name="LISTEN_PERIODIC_MESSAGE_TIMER" value={state.settings.LISTEN_PERIODIC_MESSAGE_TIMER} onChange={handleChange} />
                          <div className="form-text">Time in seconds to send a periodic message</div>
                        </Form.Group>

                        {/* USE_ELABS */}
                        <Form.Group>
                          <Form.Check 
                            type="switch"
                            id="USE_ELABS"
                            label="Use ELabs"
                            name="USE_ELABS"
                            checked={state.settings.USE_ELABS}
                            onChange={handleChange}
                          />
                        </Form.Group>

                        {/* ELABS_STREAM */}
                        <Form.Group>
                          <Form.Check 
                            type="switch"
                            id="ELABS_STREAM"
                            label="ELabs Stream"
                            name="ELABS_STREAM"
                            checked={state.settings.ELABS_STREAM}
                            onChange={handleChange}
                          />
                        </Form.Group>

                        {/* Form update buttons */}
                        <Col className='settings-panel-content__form-buttons' xs={12}>
                          <Row className='justify-content-end'>
                            <Col xs={6} lg={3}>
                              <Button variant="secondary" className='d-block w-100' onClick={handleCancel} disabled={!state.isChanged}>Cancel</Button>
                            </Col>
                            <Col xs={6} lg={3}>
                              <Button variant="primary" className='settings-update-btn d-block w-100' onClick={handleSettingsSubmit} disabled={!state.isChanged}>Update</Button>
                            </Col>
                          </Row>
                        </Col>
                      </Form>
                    )}
                    {state.activeTab === 'sentiment' && (
                      <Form className='row'>

                        {/* MAX_LEVEL */}
                        <Form.Group className='settings-panel-content__form-item col-lg-6'>
                          <Form.Label>Max Sentiment Level:</Form.Label>
                          <Form.Control type="number" name="MAX_LEVEL" value={state.settings.MAX_LEVEL} onChange={handleChange} />
                          <div className="form-text">Set max sentiment level</div>
                        </Form.Group>

                        {/* MIN_LEVEL */}
                        <Form.Group className='settings-panel-content__form-item col-lg-6'>
                          <Form.Label>Min Sentiment Level:</Form.Label>
                          <Form.Control type="number" name="MIN_LEVEL" value={state.settings.MIN_LEVEL} onChange={handleChange} />
                          <div className="form-text">Set min sentiment level</div>
                        </Form.Group>

                        {/* Positive Score */}
                        <Form.Group className='settings-panel-content__form-item col-md-4'>
                          <Form.Label>Positive Score Multiplier:</Form.Label>
                          <Form.Control 
                            type="number" 
                            name="positive" 
                            value={state.settings.SENTIMENT_SCORES ? state.settings.SENTIMENT_SCORES.positive : 0} 
                            onChange={e => {
                              const value = parseFloat(e.target.value);
                              const newSentimentScores = { ...state.settings.SENTIMENT_SCORES, positive: value };
                              const newSettings = { ...state.settings, SENTIMENT_SCORES: newSentimentScores };
                              dispatch({ type: 'SET_CHANGED', payload: newSettings });
                            }}
                          />
                          <div className="form-text">Affects scores classified as positive</div>
                        </Form.Group>
                    
                        {/* Neutral Score */}
                        <Form.Group className='settings-panel-content__form-item col-md-4'>
                          <Form.Label>Neutral Score Multiplier:</Form.Label>
                          <Form.Control 
                            type="number" 
                            name="neutral" 
                            value={state.settings.SENTIMENT_SCORES.neutral} 
                            onChange={e => {
                              const value = parseFloat(e.target.value);
                              const newSentimentScores = { ...state.settings.SENTIMENT_SCORES, neutral: value };
                              const newSettings = { ...state.settings, SENTIMENT_SCORES: newSentimentScores };
                              dispatch({ type: 'SET_CHANGED', payload: newSettings });
                            }}
                          />
                          <div className="form-text">Affects scores classified as neutral</div>
                        </Form.Group>

                        {/* Negative Score */}
                        <Form.Group className='settings-panel-content__form-item col-md-4'>
                          <Form.Label>Negative Score Multiplier:</Form.Label>
                          <Form.Control 
                            type="number" 
                            name="negative" 
                            value={state.settings.SENTIMENT_SCORES.negative} 
                            onChange={e => {
                              const value = parseFloat(e.target.value);
                              const newSentimentScores = { ...state.settings.SENTIMENT_SCORES, negative: value };
                              const newSettings = { ...state.settings, SENTIMENT_SCORES: newSentimentScores };
                              dispatch({ type: 'SET_CHANGED', payload: newSettings });
                            }}
                          />
                          <div className="form-text">Affects scores classified as negative</div>
                        </Form.Group>

                        {/* Form update buttons */}
                        <Col className='settings-panel-content__form-buttons' xs={12}>
                          <Row className='justify-content-end'>
                            <Col xs={6} lg={3}>
                              <Button variant="secondary" className='d-block w-100' onClick={handleCancel} disabled={!state.isChanged}>Cancel</Button>
                            </Col>
                            <Col xs={6} lg={3}>
                              <Button variant="primary" className='settings-update-btn d-block w-100' onClick={handleSettingsSubmit} disabled={!state.isChanged}>Update</Button>
                            </Col>
                          </Row>
                        </Col>
                      </Form>
                    )}
                    {state.activeTab === 'moderation' && (
                      <Form className='row'>

                        {/* MOD_REPLACE_PROFANITY */}
                        <Form.Group className='settings-panel-content__form-item col-lg-6'>
                          <Form.Label>Text To Replace Profanity:</Form.Label>
                          <Form.Control type="text" name="MOD_REPLACE_PROFANITY" value={state.settings.MOD_REPLACE_PROFANITY} onChange={handleChange} />
                          <div className="form-text">ie. Using "-", results in "What the ----!"</div>
                        </Form.Group>

                        {/* MOD_REPLACE_RESPONSE */}
                        <Form.Group className='settings-panel-content__form-item col-lg-6'>
                          <Form.Check 
                            type="switch"
                            id="MOD_REPLACE_RESPONSE"
                            label="Replace AI response?"
                            name="MOD_REPLACE_RESPONSE"
                            checked={state.settings.MOD_REPLACE_RESPONSE}
                            onChange={handleChange}
                          />
                          <div className="form-text">Set whether AI response is replaced when filtered</div>
                        </Form.Group>

                        {/* Form update buttons */}
                        <Col className='settings-panel-content__form-buttons' xs={12}>
                          <Row className='justify-content-end'>
                            <Col xs={6} lg={3}>
                              <Button variant="secondary" className='d-block w-100' onClick={handleCancel} disabled={!state.isChanged}>Cancel</Button>
                            </Col>
                            <Col xs={6} lg={3}>
                              <Button variant="primary" className='settings-update-btn d-block w-100' onClick={handleSettingsSubmit} disabled={!state.isChanged}>Update</Button>
                            </Col>
                          </Row>
                        </Col>
                      </Form>
                    )}
                    {state.activeTab === 'stream' && (
                      <Form className='row'>
                        {/* YouTube Video ID */}
                        <Form.Group className='settings-panel-content__form-item col-lg-6'>
                          <Form.Label>YouTube Video ID:</Form.Label>
                          <Form.Control
                            type="text"
                            value={videoID}
                            onChange={(e) => setVideoID(e.target.value)}
                            disabled={state.isStreaming}
                          />
                          <div className="form-text">Enter the YouTube Video ID for streaming.</div>
                        </Form.Group>
                  
                        {/* Toggle Streaming */}
                        <Form.Group className='settings-panel-content__form-item col-lg-6'>
                          <Button onClick={handleStreaming} disabled={!videoID}>
                            {state.isStreaming ? "Stop Streaming" : "Start Streaming"}
                          </Button>
                          {/* New Button for Manual Message Processing */}
                          <Button onClick={handleManualProcessMessage}>
                            Process Message Manually
                          </Button>
                        </Form.Group>
                      </Form>
                    )}
                    {state.activeTab === 'advanced' && (
                      <Form className='row'>

                        {/* OPENAI_MODEL */}
                        <Form.Group className='settings-panel-content__form-item col-lg-6'>
                          <Form.Label>OpenAI Model:</Form.Label>
                          <Form.Control as="select" name="OPENAI_MODEL" value={state.settings.OPENAI_MODEL} onChange={handleChange}>
                            {openaiModels.map((model, index) => (
                              <option key={index} value={model}>
                                {model}
                              </option>
                            ))}
                          </Form.Control>
                          <div className="form-text">OpenAI LLM engine</div>
                        </Form.Group>

                        {/* OPENAI_WHISPER_MODEL */}
                        <Form.Group className='settings-panel-content__form-item col-lg-6'>
                          <Form.Label>OpenAI Whisper Model:</Form.Label>
                          <Form.Control as="select" name="OPENAI_WHISPER_MODEL" value={state.settings.OPENAI_WHISPER_MODEL} onChange={handleChange}>
                            {openaiWhisperModels.map((model, index) => (
                              <option key={index} value={model}>
                                {model}
                              </option>
                            ))}
                          </Form.Control>
                          <div className="form-text">OpenAI transcription engine</div>
                        </Form.Group>

                        {/* OPENAI_EMBEDDING_MODEL */}
                        <Form.Group className='settings-panel-content__form-item col-lg-6'>
                          <Form.Label>OpenAI Embedding Model:</Form.Label>
                          <Form.Control as="select" name="OPENAI_EMBEDDING_MODEL" value={state.settings.OPENAI_EMBEDDING_MODEL} onChange={handleChange}>
                            {openaiEmbeddingModels.map((model, index) => (
                              <option key={index} value={model}>
                                {model}
                              </option>
                            ))}
                          </Form.Control>
                          <div className="form-text">OpenAI embedding engine</div>
                        </Form.Group>

                        {/* PINECONE_INDEX_NAME */}
                        <Form.Group className='settings-panel-content__form-item col-lg-6'>
                          <Form.Label>Pinecone Index Name:</Form.Label>
                          <Form.Control type="text" name="PINECONE_INDEX_NAME" value={state.settings.PINECONE_INDEX_NAME} onChange={handleChange} />
                          <div className="form-text">Index name holding vector database</div>
                        </Form.Group>

                        {/* ELABS_MODEL */}
                        <Form.Group className='settings-panel-content__form-item col-lg-6'>
                          <Form.Label>ELabs Model:</Form.Label>
                          <Form.Control as="select" name="ELABS_MODEL" value={state.settings.ELABS_MODEL} onChange={handleChange}>
                            {elabsModels.map((model, index) => (
                              <option key={index} value={model}>
                                {model}
                              </option>
                            ))}
                          </Form.Control>
                          <div className="form-text">ElevenLabs Text-To-Speech engine</div>
                        </Form.Group>

                        {/* Form update buttons */}
                        <Col className='settings-panel-content__form-buttons' xs={12}>
                          <Row className='justify-content-end'>
                            <Col xs={6} lg={3}>
                              <Button variant="secondary" className='d-block w-100' onClick={handleCancel} disabled={!state.isChanged}>Cancel</Button>
                            </Col>
                            <Col xs={6} lg={3}>
                              <Button variant="primary" className='settings-update-btn d-block w-100' onClick={handleSettingsSubmit} disabled={!state.isChanged}>Update</Button>
                            </Col>
                          </Row>
                        </Col>
                      </Form>
                    )}
                  </Col>
                </Row>
              </Col>
            </>
          ) : (
            <p className='text-light'>Loading settings...</p>
          )}
        </Row>
      </Col>

      {/* Chat Interface */}
      <Col md={6} lg={4} className="chat-panel">
        <div className='chat-interface d-flex flex-column justify-content-between'>
          <div className='chat-panel__top-header'>
            <Row className="chat-panel__top">
              <Col xs={12}>
                <div className="d-inline-block me-3">
                  <p className="text-light fs-7 fw-semibold mb-1">Select input device</p>
                </div>
                <div className="d-inline-block">
                  <Dropdown onSelect={handleDeviceChange}>
                    <Dropdown.Toggle variant='secondary' id="dropdown-basic">
                      <i className="fas fa-microphone"></i>
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
            <Row className="chat-panel__header align-items-center">
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
                <Button variant="danger" onClick={handleEndClick}>End</Button>
              </Col>
            </Row>
          </div>

          {/* Display chat log */}
          <div className='chat-log'>
            {state.chatLog.map((entry, index) => (
              <div key={index} className={`chat-entry ${entry.role} ${entry.message_from}`}>
                <div className='chat-entry__bubble'>
                  <p>{entry.content}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Device selection dropdown */}
          <div className="chat-sub-footer justify-content-center" xs={12}>
            {/* Audio listen controls */}
            <Row className="audio-controls">
              <Col xs={12}>
                <Button variant="primary" className='listen-btn' onClick={handleListening} disabled={state.isRecording} aria-label="Listening mode button">
                  <i className="fas fa-broadcast-tower me-2"></i>
                  {state.isListening ? "Listening..." : "Start Listen Mode"}
                </Button>
              </Col>
            </Row>
          </div>

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
      </Col>
    </>
  );
}

export default ChatInterface;
