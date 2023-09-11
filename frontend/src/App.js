import React, { useState } from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import './styles/index.css';
import './styles/App.css';
import ChatInterface from './components/ChatInterface';
import SettingsPanel from './components/SettingsPanel';

function App() {
  const [showModal, setShowModal] = useState(true);
  const [showEndModal, setShowEndModal] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);

  const handleCloseModal = () => {
    setShowModal(false);
  };

  const handleEndClick = () => {
    setShowEndModal(true);
  };
  
  const handleEndCancelClick = () => {
    setShowEndModal(false);
  };
  
  const handleEndConfirmClick = () => {
    window.location.href = "https://ronglopez.com";
  };  

  return (
    <div className="App container-fluid">

      {/* Start modal */}
      <div className={`modal fade ${showModal ? 'show d-block' : 'd-none'}`} tabIndex="-1">
        <div className="modal-dialog">
          <div className="modal-content">
            <div className="modal-header">
              <h5 className="modal-title">Welcome to My Chat App</h5>
            </div>
            <div className="modal-body">
              <p>Get ready for an amazing chat experience.</p>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-primary" onClick={handleCloseModal}>
                Start Chatting
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* End modal */}
      <div className={`modal fade ${showEndModal ? 'show d-block' : 'd-none'}`} tabIndex="-1">
        <div className="modal-dialog">
          <div className="modal-content">
            <div className="modal-header">
              <h5 className="modal-title">End Chat</h5>
              <button type="button" className="close" aria-label="Close" onClick={handleEndCancelClick}>
                <span aria-hidden="true">&times;</span>
              </button>
            </div>
            <div className="modal-body">
              <p>Are you sure you want to end the chat?</p>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-secondary" onClick={handleEndCancelClick}>
                Cancel
              </button>
              <button type="button" className="btn btn-primary" onClick={handleEndConfirmClick}>
                Confirm
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Modal Overlay for both Start and End modals */}
      <div className={`overlay ${(showModal || showEndModal) ? 'show' : ''}`}></div>

      {/* Main body */}
      <div className="row">
        <div className="settings-panel col-md-6 col-lg-8">
          {/* Settings panel here */}
          <SettingsPanel setIsStreaming={setIsStreaming} isStreaming={isStreaming} />
        </div>
        <div className="chat-panel col-md-6 col-lg-4">
          {/* Pass the chatStarted prop here */}
          <ChatInterface 
            chatStarted={!showModal} 
            handleEndClick={handleEndClick} 
            setIsStreaming={setIsStreaming} isStreaming={isStreaming}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
