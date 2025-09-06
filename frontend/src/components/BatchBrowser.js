import React, { useState, useEffect } from 'react';
import apiService from '../services/api';

const BatchBrowser = () => {
    const [batches, setBatches] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [downloading, setDownloading] = useState({});

    useEffect(() => {
        loadBatches();
    }, []);

    const loadBatches = async () => {
        try {
            setLoading(true);
            const batchList = await apiService.getBatches();
            setBatches(batchList);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to load batches');
        } finally {
            setLoading(false);
        }
    };

    const downloadBatch = async (batchId, fileName) => {
        try {
            setDownloading(prev => ({ ...prev, [batchId]: true }));

            const blob = await apiService.downloadFile(batchId);

            // Create download link
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = fileName || `batch_${batchId.substring(0, 8)}.dat`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);

        } catch (err) {
            setError(err.response?.data?.detail || 'Download failed');
        } finally {
            setDownloading(prev => ({ ...prev, [batchId]: false }));
        }
    };

    if (loading) {
        return (
            <div className="card">
                <div className="loading">Loading batches...</div>
            </div>
        );
    }

    return (
        <div className="card">
            <div className="flex flex-between">
                <h2>Browse Batches</h2>
                <button className="btn btn-secondary" onClick={loadBatches}>
                    Refresh
                </button>
            </div>

            {error && (
                <div className="alert alert-error">
                    <strong>Error:</strong> {error}
                </div>
            )}

            {batches.length === 0 ? (
                <div className="alert alert-info">
                    No batches found. This may be due to:
                    <ul className="mt-2 mb-0">
                        <li>No files have been uploaded yet</li>
                        <li>Uploaded data has expired (TTL timeout)</li>
                        <li>GolemDB query limitations</li>
                    </ul>
                    <div className="mt-2">
                        <strong>Tip:</strong> Upload a file with a simple annotation (like "TEST123") and search for it in the Search tab.
                    </div>
                </div>
            ) : (
                <div style={{ overflowX: 'auto' }}>
                    <table className="table">
                        <thead>
                            <tr>
                                <th>Batch ID</th>
                                <th>File Name</th>
                                <th>Annotation</th>
                                <th>Chunks</th>
                                <th>Created</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {batches.map((batch) => (
                                <tr key={batch.batch_id}>
                                    <td>
                                        <code className="text-small">
                                            {batch.batch_id.substring(0, 8)}...
                                        </code>
                                    </td>
                                    <td>{batch.file_name || 'Unknown'}</td>
                                    <td>
                                        <span className="badge">{batch.annotation}</span>
                                    </td>
                                    <td>{batch.total_chunks}</td>
                                    <td className="text-small text-muted">
                                        {batch.created_at !== 'Unknown'
                                            ? new Date(batch.created_at).toLocaleDateString()
                                            : 'Unknown'
                                        }
                                    </td>
                                    <td>
                                        <button
                                            className="btn"
                                            onClick={() => downloadBatch(batch.batch_id, batch.file_name)}
                                            disabled={downloading[batch.batch_id]}
                                            style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}
                                        >
                                            {downloading[batch.batch_id] ? 'Downloading...' : 'Download'}
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

export default BatchBrowser;