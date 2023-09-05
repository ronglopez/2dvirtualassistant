import React, { useState } from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import './styles/index.css';
import './styles/App.css';
import ChatInterface from './components/ChatInterface';

function App() {
  const [showModal, setShowModal] = useState(true);

  const handleCloseModal = () => {
    setShowModal(false);
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

      {/* Modal Overlay */}
      <div className={`overlay ${showModal ? 'show' : ''}`}></div>

      {/* Main body */}
      <div className="row justify-content-center">
        <div className="col-md-12">
          <ChatInterface chatStarted={!showModal} /> {/* Pass the chatStarted prop here */}
        </div>
      </div>
    </div>
  );
}

export default App;
