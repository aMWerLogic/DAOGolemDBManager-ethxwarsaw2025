import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';
import FileUpload from './components/FileUpload';
import BatchBrowser from './components/BatchBrowser';
import SearchInterface from './components/SearchInterface';

function App() {
    return (
        <Router>
            <div className="App">
                <header className="App-header">
                    <nav className="nav">
                        <div className="nav-brand">
                            <h1>DAO GolemDB</h1>
                        </div>
                        <div className="nav-links">
                            <Link to="/" className="nav-link">Upload</Link>
                            <Link to="/browse" className="nav-link">Browse</Link>
                            <Link to="/search" className="nav-link">Search</Link>
                        </div>
                    </nav>
                </header>

                <main className="main-content">
                    <Routes>
                        <Route path="/" element={<FileUpload />} />
                        <Route path="/browse" element={<BatchBrowser />} />
                        <Route path="/search" element={<SearchInterface />} />
                    </Routes>
                </main>
            </div>
        </Router>
    );
}

export default App;