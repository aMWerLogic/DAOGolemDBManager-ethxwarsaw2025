import React, { useState, useEffect } from 'react';

const MetaMaskWallet = ({ onWalletChange }) => {
    const [account, setAccount] = useState(null);
    const [balance, setBalance] = useState(null);
    const [isConnecting, setIsConnecting] = useState(false);
    const [error, setError] = useState(null);
    const [networkStatus, setNetworkStatus] = useState(null);

    // ETH Warsaw Holesky network configuration
    const ETHWARSAW_NETWORK = {
        chainId: '0xe0087f829', // 60138453033 in hex
        chainName: 'ETH Warsaw Holesky',
        rpcUrls: ['https://ethwarsaw.holesky.golemdb.io/rpc'],
        nativeCurrency: {
            name: 'ETH',
            symbol: 'ETH',
            decimals: 18
        },
        blockExplorerUrls: ['https://ethwarsaw.holesky.golemdb.io/explorer'] // If available
    };

    useEffect(() => {
        checkConnection();

        // Listen for account changes
        if (window.ethereum) {
            window.ethereum.on('accountsChanged', handleAccountsChanged);
            window.ethereum.on('chainChanged', handleChainChanged);
        }

        return () => {
            if (window.ethereum) {
                window.ethereum.removeListener('accountsChanged', handleAccountsChanged);
                window.ethereum.removeListener('chainChanged', handleChainChanged);
            }
        };
    }, []);

    const checkConnection = async () => {
        if (typeof window.ethereum !== 'undefined') {
            try {
                const accounts = await window.ethereum.request({ method: 'eth_accounts' });
                await checkNetwork();

                if (accounts.length > 0) {
                    setAccount(accounts[0]);
                    await getBalance(accounts[0]);
                    onWalletChange?.(accounts[0]);
                }
            } catch (err) {
                console.error('Error checking connection:', err);
            }
        }
    };

    const checkNetwork = async () => {
        try {
            const chainId = await window.ethereum.request({ method: 'eth_chainId' });
            console.log('Current chain ID:', chainId, 'Expected:', ETHWARSAW_NETWORK.chainId);

            if (chainId === ETHWARSAW_NETWORK.chainId) {
                setNetworkStatus('correct');
            } else {
                setNetworkStatus('wrong');
            }
        } catch (err) {
            console.error('Error checking network:', err);
            setNetworkStatus('unknown');
        }
    };

    const switchToEthWarsawNetwork = async () => {
        try {
            console.log('Attempting to switch to network:', ETHWARSAW_NETWORK);

            // Try to switch to the network
            await window.ethereum.request({
                method: 'wallet_switchEthereumChain',
                params: [{ chainId: ETHWARSAW_NETWORK.chainId }],
            });
            setNetworkStatus('correct');
            setError(null);
        } catch (switchError) {
            console.log('Switch error:', switchError);

            // If the network doesn't exist, add it
            if (switchError.code === 4902) {
                try {
                    console.log('Adding new network:', ETHWARSAW_NETWORK);
                    await window.ethereum.request({
                        method: 'wallet_addEthereumChain',
                        params: [ETHWARSAW_NETWORK],
                    });
                    setNetworkStatus('correct');
                    setError(null);
                } catch (addError) {
                    console.error('Error adding network:', addError);
                    setError(`Failed to add ETH Warsaw Holesky network: ${addError.message}`);
                }
            } else {
                console.error('Error switching network:', switchError);
                setError(`Failed to switch to ETH Warsaw Holesky network: ${switchError.message}`);
            }
        }
    };

    const connectWallet = async () => {
        if (typeof window.ethereum === 'undefined') {
            setError('MetaMask is not installed. Please install MetaMask to continue.');
            return;
        }

        setIsConnecting(true);
        setError(null);

        try {
            // First check and switch network if needed
            await checkNetwork();
            if (networkStatus !== 'correct') {
                await switchToEthWarsawNetwork();
            }

            const accounts = await window.ethereum.request({
                method: 'eth_requestAccounts'
            });

            if (accounts.length > 0) {
                setAccount(accounts[0]);
                await getBalance(accounts[0]);
                onWalletChange?.(accounts[0]);
            }
        } catch (err) {
            if (err.code === 4001) {
                setError('Please connect to MetaMask.');
            } else {
                setError('An error occurred while connecting to MetaMask.');
            }
            console.error('Error connecting wallet:', err);
        } finally {
            setIsConnecting(false);
        }
    };

    const disconnectWallet = () => {
        setAccount(null);
        setBalance(null);
        setError(null);
        onWalletChange?.(null);
    };

    const getBalance = async (address) => {
        try {
            const balance = await window.ethereum.request({
                method: 'eth_getBalance',
                params: [address, 'latest']
            });

            // Convert from wei to ETH
            const balanceInEth = parseInt(balance, 16) / Math.pow(10, 18);
            setBalance(balanceInEth.toFixed(6));
        } catch (err) {
            console.error('Error getting balance:', err);
        }
    };

    const handleAccountsChanged = (accounts) => {
        if (accounts.length === 0) {
            disconnectWallet();
        } else {
            setAccount(accounts[0]);
            getBalance(accounts[0]);
            onWalletChange?.(accounts[0]);
        }
    };

    const handleChainChanged = (chainId) => {
        console.log('Chain changed to:', chainId);
        checkNetwork();
        if (account) {
            getBalance(account);
        }
    };

    const formatAddress = (address) => {
        if (!address) return '';
        return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
    };

    return (
        <div className="wallet-container" style={{
            padding: '1rem',
            border: '1px solid #ddd',
            borderRadius: '8px',
            backgroundColor: '#f9f9f9',
            marginBottom: '1rem'
        }}>
            <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem' }}>MetaMask Wallet</h3>

            {error && (
                <div className="alert alert-error" style={{ marginBottom: '1rem' }}>
                    {error}
                </div>
            )}

            {networkStatus === 'wrong' && (
                <div className="alert alert-warning" style={{ marginBottom: '1rem' }}>
                    <div>Wrong network detected. Please switch to ETH Warsaw Holesky.</div>
                    <button
                        className="btn"
                        onClick={switchToEthWarsawNetwork}
                        style={{
                            backgroundColor: '#ffc107',
                            color: '#000',
                            border: 'none',
                            marginTop: '0.5rem',
                            fontSize: '0.875rem',
                            padding: '0.5rem 1rem'
                        }}
                    >
                        Switch to ETH Warsaw Holesky
                    </button>
                </div>
            )}

            {networkStatus === 'correct' && (
                <div className="alert alert-success" style={{ marginBottom: '1rem' }}>
                    ✓ Connected to ETH Warsaw Holesky network
                    {balance && parseFloat(balance) < 0.001 && (
                        <div style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: '#856404' }}>
                            <strong>⚠️ Low balance detected!</strong><br />
                            You have {balance} ETH. You may need test ETH from a faucet to perform transactions.
                            <br />
                            <small>Contact the ETH Warsaw team for testnet tokens if needed.</small>
                        </div>
                    )}
                </div>
            )}

            {!account ? (
                <div>
                    <p className="text-muted" style={{ marginBottom: '1rem' }}>
                        Connect your MetaMask wallet to upload and download files
                    </p>
                    <button
                        className="btn"
                        onClick={connectWallet}
                        disabled={isConnecting}
                        style={{
                            backgroundColor: '#f6851b',
                            color: 'white',
                            border: 'none'
                        }}
                    >
                        {isConnecting ? 'Connecting...' : 'Connect MetaMask'}
                    </button>
                </div>
            ) : (
                <div>
                    <div style={{ marginBottom: '0.5rem' }}>
                        <strong>Connected:</strong> {formatAddress(account)}
                        <button
                            onClick={() => navigator.clipboard.writeText(account)}
                            style={{
                                marginLeft: '0.5rem',
                                padding: '0.25rem 0.5rem',
                                fontSize: '0.75rem',
                                backgroundColor: '#6c757d',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer'
                            }}
                            title="Copy full address"
                        >
                            Copy
                        </button>
                    </div>
                    {balance && (
                        <div style={{ marginBottom: '1rem' }}>
                            <strong>Balance:</strong> {balance} ETH
                        </div>
                    )}
                    <button
                        className="btn"
                        onClick={disconnectWallet}
                        style={{
                            backgroundColor: '#dc3545',
                            color: 'white',
                            border: 'none',
                            fontSize: '0.875rem',
                            padding: '0.5rem 1rem'
                        }}
                    >
                        Disconnect
                    </button>
                </div>
            )}
        </div>
    );
};

export default MetaMaskWallet;