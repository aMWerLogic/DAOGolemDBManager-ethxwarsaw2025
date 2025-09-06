import { useState, useEffect } from 'react';
import apiService from '../services/api';

const SearchInterface = () => {
    const [searchType, setSearchType] = useState('annotation');
    const [searchKey, setSearchKey] = useState('');
    const [searchValue, setSearchValue] = useState('');
    const [minValue, setMinValue] = useState('');
    const [maxValue, setMaxValue] = useState('');
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [annotations, setAnnotations] = useState({});
    const [downloading, setDownloading] = useState({});

    useEffect(() => {
        loadAnnotations();
    }, []);

    const loadAnnotations = async () => {
        try {
            const annotationData = await apiService.getAllAnnotations();
            setAnnotations(annotationData);
        } catch (err) {
            console.error('Failed to load annotations:', err);
        }
    };

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!searchKey.trim()) return;

        setLoading(true);
        setError(null);
        setResults([]);

        try {
            let searchResults;

            if (searchType === 'annotation') {
                searchResults = await apiService.searchByAnnotation(
                    searchKey,
                    searchValue.trim() || null
                );
            } else if (searchType === 'numeric') {
                if (!minValue || !maxValue) {
                    throw new Error('Both min and max values are required for numeric search');
                }
                searchResults = await apiService.searchNumericRange(
                    searchKey,
                    parseInt(minValue),
                    parseInt(maxValue)
                );
            }

            setResults(searchResults || []);
        } catch (err) {
            console.error('Search error:', err);
            const errorMessage = err.response?.data?.detail || err.message || 'Search failed';
            setError(`Search failed: ${errorMessage}`);
        } finally {
            setLoading(false);
        }
    };

    const downloadBatch = async (batchId, fileName) => {
        console.log('Starting download for batch:', batchId, 'fileName:', fileName);
        try {
            setDownloading(prev => ({ ...prev, [batchId]: true }));

            console.log('Calling API download...');
            const blob = await apiService.downloadFile(batchId);
            console.log('Download successful, blob size:', blob.size);

            // Create download link
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = fileName || `batch_${batchId.substring(0, 8)}.dat`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);

            console.log('Download completed successfully');
        } catch (err) {
            console.error('Download error:', err);
            setError(err.response?.data?.detail || err.message || 'Download failed');
        } finally {
            setDownloading(prev => ({ ...prev, [batchId]: false }));
        }
    };

    return (
        <div className="card">
            <h2>Search Entities</h2>

            <form onSubmit={handleSearch}>
                <div className="form-group">
                    <label>Search Type</label>
                    <select
                        className="form-control"
                        value={searchType}
                        onChange={(e) => setSearchType(e.target.value)}
                    >
                        <option value="annotation">Annotation Search</option>
                        <option value="numeric">Numeric Range Search</option>
                    </select>
                </div>

                <div className="form-group">
                    <label>Annotation Key</label>
                    <input
                        type="text"
                        className="form-control"
                        value={searchKey}
                        onChange={(e) => setSearchKey(e.target.value)}
                        placeholder="e.g., data_dump, batch_id, file_name"
                        required
                    />
                    {Object.keys(annotations).length > 0 && (
                        <div className="text-small text-muted mt-2">
                            Available keys: {Object.keys(annotations).join(', ')}
                        </div>
                    )}
                </div>

                {searchType === 'annotation' ? (
                    <div className="form-group">
                        <label>Value (optional)</label>
                        <input
                            type="text"
                            className="form-control"
                            value={searchValue}
                            onChange={(e) => setSearchValue(e.target.value)}
                            placeholder="Leave empty to find all entities with this key"
                        />
                        <div className="text-small text-muted mt-2">
                            Search now works with UUID values and special characters!
                        </div>
                    </div>
                ) : (
                    <div className="flex gap-2">
                        <div className="form-group" style={{ flex: 1 }}>
                            <label>Min Value</label>
                            <input
                                type="number"
                                className="form-control"
                                value={minValue}
                                onChange={(e) => setMinValue(e.target.value)}
                                required
                            />
                        </div>
                        <div className="form-group" style={{ flex: 1 }}>
                            <label>Max Value</label>
                            <input
                                type="number"
                                className="form-control"
                                value={maxValue}
                                onChange={(e) => setMaxValue(e.target.value)}
                                required
                            />
                        </div>
                    </div>
                )}

                <button type="submit" className="btn" disabled={loading}>
                    {loading ? 'Searching...' : 'Search'}
                </button>
            </form>

            {error && (
                <div className="alert alert-error mt-2">
                    <strong>Error:</strong> {error}
                </div>
            )}

            {results.length > 0 && (
                <div className="mt-2">
                    <h3>Search Results ({results.length})</h3>
                    <div style={{ overflowX: 'auto' }}>
                        <table className="table">
                            <thead>
                                <tr>
                                    <th>Entity Key</th>
                                    <th>Annotations</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {results.map((result, index) => (
                                    <tr key={index}>
                                        <td>
                                            <code className="text-small">
                                                {result.entity_key}
                                            </code>
                                        </td>
                                        <td>
                                            {Object.keys(result.annotations).length > 0 ? (
                                                <details>
                                                    <summary>{Object.keys(result.annotations).length} annotations</summary>
                                                    <div className="text-small" style={{ marginTop: '0.5rem' }}>
                                                        {Object.entries(result.annotations).map(([key, value]) => (
                                                            <div key={key}>
                                                                <strong>{key}:</strong> {
                                                                    key === 'expiration_date' ? (
                                                                        <span style={{
                                                                            color: new Date(value) < new Date() ? '#dc3545' : '#28a745'
                                                                        }}>
                                                                            {new Date(value).toLocaleString()}
                                                                            {new Date(value) < new Date() && ' (EXPIRED)'}
                                                                        </span>
                                                                    ) : value
                                                                }
                                                            </div>
                                                        ))}
                                                    </div>
                                                </details>
                                            ) : (
                                                <span className="text-muted">No annotations visible</span>
                                            )}
                                        </td>
                                        <td>
                                            {result.annotations.batch_id ? (
                                                <button
                                                    className="btn"
                                                    onClick={() => downloadBatch(result.annotations.batch_id, result.annotations.file_name)}
                                                    disabled={downloading[result.annotations.batch_id]}
                                                    style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}
                                                >
                                                    {downloading[result.annotations.batch_id] ? 'Downloading...' : 'Download'}
                                                </button>
                                            ) : (
                                                <span className="text-muted text-small">No batch ID</span>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {!loading && results.length === 0 && searchKey && (
                <div className="alert alert-info mt-2">
                    No entities found matching your search criteria.
                    <br />
                    <small>Note: Data may expire after some time (TTL). Try uploading a new file if no results are found.</small>
                </div>
            )}
        </div>
    );
};

export default SearchInterface;