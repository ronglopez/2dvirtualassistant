// HISTORY STATE
// Import necessary libraries
import React, { useEffect, useReducer, useRef, useState } from 'react';
import axios from 'axios';
import io from 'socket.io-client';
import { Button, Form, Col, Row, Nav, Toast } from 'react-bootstrap';

// Define Initial State
const initialState = {
  settings: {
    SENTIMENT_SCORES: {}
  },
  isLoaded: false,
  isChanged: false,
  originalSettings: {},
  activeTab: 'main',
  isStreaming: false,
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
    default:
      return state;
  }
};

const SettingsPanel = ({ setIsStreaming, isStreaming }) => {
  const [state, dispatch] = useReducer(reducer, initialState);
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
  const handleSubmit = async () => {
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

  // Handle the streaming state
  useEffect(() => {
    isStreamingRef.current = state.isStreaming;
  }, [state.isStreaming]);

  // Handle the streaming loop
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

  // Frontend UI
  return (
    <div className="settings-panel-content">

      {/* Success Toast */}
      <Toast className='text-bg-success position-fixed start-50 translate-middle' onClose={() => setShowSuccessToast(false)} show={showSuccessToast} delay={3000} autohide>
        <Toast.Body>{toastMessage}</Toast.Body>
      </Toast>

      {/* Failure Toast */}
      <Toast className='text-bg-danger position-fixed start-50 translate-middle' onClose={() => setShowFailureToast(false)} show={showFailureToast} delay={3000} autohide>
        <Toast.Body>{toastMessage}</Toast.Body>
      </Toast>

      <h2 className='text-star mb-4'>Settings</h2>
      {state.isLoaded ? (
        <>
          {/* Tabs */}
          <Row className='settings-panel-content__tabs'>
            <Col xs={12}>
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
          </Row>

          {/* Tab Contents */}
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
                  <Col xs={12}>
                    <Row className='justify-content-end'>
                      <Col xs={6} lg={3}>
                        <Button variant="secondary" className='d-block w-100' onClick={handleCancel} disabled={!state.isChanged}>Cancel</Button>
                      </Col>
                      <Col xs={6} lg={3}>
                        <Button variant="primary" className='settings-update-btn d-block w-100' onClick={handleSubmit} disabled={!state.isChanged}>Update</Button>
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
                  <Col xs={12}>
                    <Row className='justify-content-end'>
                      <Col xs={6} lg={3}>
                        <Button variant="secondary" className='d-block w-100' onClick={handleCancel} disabled={!state.isChanged}>Cancel</Button>
                      </Col>
                      <Col xs={6} lg={3}>
                        <Button variant="primary" className='settings-update-btn d-block w-100' onClick={handleSubmit} disabled={!state.isChanged}>Update</Button>
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
                  <Col xs={12}>
                    <Row className='justify-content-end'>
                      <Col xs={6} lg={3}>
                        <Button variant="secondary" className='d-block w-100' onClick={handleCancel} disabled={!state.isChanged}>Cancel</Button>
                      </Col>
                      <Col xs={6} lg={3}>
                        <Button variant="primary" className='settings-update-btn d-block w-100' onClick={handleSubmit} disabled={!state.isChanged}>Update</Button>
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
                  <Col xs={12}>
                    <Row className='justify-content-end'>
                      <Col xs={6} lg={3}>
                        <Button variant="secondary" className='d-block w-100' onClick={handleCancel} disabled={!state.isChanged}>Cancel</Button>
                      </Col>
                      <Col xs={6} lg={3}>
                        <Button variant="primary" className='settings-update-btn d-block w-100' onClick={handleSubmit} disabled={!state.isChanged}>Update</Button>
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
                  <Col xs={12}>
                    <Row className='justify-content-end'>
                      <Col xs={6} lg={3}>
                        <Button variant="secondary" className='d-block w-100' onClick={handleCancel} disabled={!state.isChanged}>Cancel</Button>
                      </Col>
                      <Col xs={6} lg={3}>
                        <Button variant="primary" className='settings-update-btn d-block w-100' onClick={handleSubmit} disabled={!state.isChanged}>Update</Button>
                      </Col>
                    </Row>
                  </Col>
                </Form>
              )}
            </Col>
          </Row>
        </>
      ) : (
        <p className='text-light'>Loading settings...</p>
      )}
    </div>
  );
};

export default SettingsPanel;
