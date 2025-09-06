import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import apiService from '../services/api';
import MetaMaskWallet from './MetaMaskWallet';
import PaymentHandler from './PaymentHandler';

const FileUpload = () => {
    const [uploading, setUploading] = useState(false);
    const [uploadResult, setUploadResult] = useState(null);
    const [error, setError] = useState(null);
    const [annotation, setAnnotation] = useState('WEB_UPLOAD');
    const [btl, setBtl] = useState(3600); // Default 1 hour
    const [walletAddress, setWalletAddress] = useState(null);
    const [selectedFile, setSelectedFile] = useState(null);

    const onDrop = useCallback((acceptedFiles) => {
        if (acceptedFiles.length === 0) return;
        setSelectedFile(acceptedFiles[0]);
        setError(null);
        setUploadResult(null);
    }, []);

    const handleUploadWithPayment = async () => {
        if (!selectedFile || !walletAddress) return;

        setUploading(true);
        setError(null);
        setUploadResult(null);

        try {
            const result = await apiService.uploadFile(selectedFile, annotation, btl);
            setUploadResult(result);
            setSelectedFile(null); // Clear selected file after successful upload
        } catch (err) {
            setError(err.response?.data?.detail || 'Upload failed');
        } finally {
            setUploading(false);
        }
    };

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        multiple: false,
        maxSize: 100 * 1024 * 1024, // 100MB
    });

    const paymentHandler = PaymentHandler({
        walletAddress,
        onPaymentSuccess: (paymentData) => {
            console.log('Payment successful:', paymentData);
            handleUploadWithPayment();
        },
        onPaymentError: (errorMsg) => {
            setError(`Payment failed: ${errorMsg}`);
            setUploading(false);
        }
    });

    return (
        <div className="card">
            <h2>Upload File</h2>

            <MetaMaskWallet onWalletChange={setWalletAddress} />

            <div className="form-group">
                <label htmlFor="annotation">Annotation</label>
                <input
                    id="annotation"
                    type="text"
                    className="form-control"
                    value={annotation}
                    onChange={(e) => setAnnotation(e.target.value)}
                    placeholder="Enter annotation for your file (e.g., MY_FILE_TEST)"
                />
                <div className="text-small text-muted mt-2">
                    Use simple text without special characters for better search compatibility
                </div>
            </div>

            <div className="form-group">
                <label htmlFor="btl">Data Expiration Time</label>
                <select
                    id="btl"
                    className="form-control"
                    value={btl}
                    onChange={(e) => setBtl(parseInt(e.target.value))}
                >
                    <option value={300}>5 minutes</option>
                    <option value={1800}>30 minutes</option>
                    <option value={3600}>1 hour</option>
                    <option value={7200}>2 hours</option>
                    <option value={21600}>6 hours</option>
                    <option value={86400}>24 hours</option>
                    <option value={604800}>7 days</option>
                </select>
                <div className="text-small text-muted mt-2">
                    How long the data will be stored in GolemDB before expiring
                </div>
            </div>

            <div
                {...getRootProps()}
                className={`dropzone ${isDragActive ? 'dropzone-active' : ''} ${uploading ? 'dropzone-disabled' : ''}`}
                style={{
                    border: '2px dashed #ddd',
                    borderRadius: '8px',
                    padding: '3rem',
                    textAlign: 'center',
                    cursor: uploading ? 'not-allowed' : 'pointer',
                    backgroundColor: isDragActive ? '#f0f8ff' : selectedFile ? '#e8f5e8' : '#fafafa',
                    transition: 'all 0.2s',
                }}
            >
                <input {...getInputProps()} disabled={uploading} />
                {uploading ? (
                    <div>
                        <p>Uploading...</p>
                        <div className="loading">Please wait while your file is being uploaded to GolemDB</div>
                    </div>
                ) : selectedFile ? (
                    <div>
                        <p>✓ Selected: {selectedFile.name}</p>
                        <p className="text-muted text-small">Size: {(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                        <p className="text-small">Click "Pay & Upload" below to proceed</p>
                    </div>
                ) : isDragActive ? (
                    <p>Drop the file here</p>
                ) : (
                    <div>
                        <p>Drag and drop a file here, or click to select</p>
                        <p className="text-muted text-small">Maximum file size: 100MB</p>
                    </div>
                )}
            </div>

            {selectedFile && walletAddress && (
                <div style={{ marginTop: '1rem', textAlign: 'center' }}>
                    <paymentHandler.PaymentButton
                        operationType="upload"
                        className="btn"
                        style={{
                            backgroundColor: '#28a745',
                            color: 'white',
                            border: 'none',
                            padding: '0.75rem 1.5rem',
                            fontSize: '1rem',
                            marginRight: '0.5rem'
                        }}
                    >
                        Pay {paymentHandler.paymentAmounts.upload} ETH & Upload
                    </paymentHandler.PaymentButton>

                    <button
                        className="btn"
                        onClick={() => setSelectedFile(null)}
                        style={{
                            backgroundColor: '#6c757d',
                            color: 'white',
                            border: 'none',
                            padding: '0.75rem 1.5rem',
                            fontSize: '1rem'
                        }}
                    >
                        Cancel
                    </button>
                </div>
            )}

            {selectedFile && !walletAddress && (
                <div className="alert alert-warning mt-2">
                    Please connect your MetaMask wallet to upload files
                </div>
            )}

            {error && (
                <div className="alert alert-error mt-2">
                    <strong>Error:</strong> {error}
                </div>
            )}

            {uploadResult && (
                <div className="alert alert-success mt-2">
                    <h4>Upload Successful</h4>
                    <p><strong>Batch ID:</strong> {uploadResult.batch_id}</p>
                    <p><strong>Total Chunks:</strong> {uploadResult.total_chunks}</p>
                    <p><strong>Message:</strong> {uploadResult.message}</p>
                    <details className="mt-2">
                        <summary>Entity Keys ({uploadResult.entity_keys.length})</summary>
                        <div className="text-small" style={{ marginTop: '0.5rem', fontFamily: 'monospace' }}>
                            {uploadResult.entity_keys.map((key, index) => (
                                <div key={index}>{key}</div>
                            ))}
                        </div>
                    </details>
                </div>
            )}
        </div>
    );
};

export default FileUpload;