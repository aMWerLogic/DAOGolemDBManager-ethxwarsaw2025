import { useState } from 'react';

const PaymentHandler = ({ walletAddress, onPaymentSuccess, onPaymentError }) => {
    const [isProcessing, setIsProcessing] = useState(false);
    const [lastTransaction, setLastTransaction] = useState(null);

    // Payment amounts in ETH (reduced for testnet)
    const PAYMENT_AMOUNTS = {
        upload: '0.0001',     // 0.0001 ETH for upload
        download: '0.00005',  // 0.00005 ETH for download
    };

    // For testing - skip payment if in development mode or explicitly disabled
    const SKIP_PAYMENT = process.env.REACT_APP_SKIP_PAYMENTS === 'true' ||
        process.env.NODE_ENV === 'development' ||
        window.location.hostname === 'localhost';

    const processPayment = async (operationType, additionalData = {}) => {
        if (!walletAddress) {
            onPaymentError?.('Please connect your MetaMask wallet first');
            return false;
        }

        if (typeof window.ethereum === 'undefined') {
            onPaymentError?.('MetaMask is not installed');
            return false;
        }

        setIsProcessing(true);

        try {
            const amount = PAYMENT_AMOUNTS[operationType];
            if (!amount) {
                throw new Error(`Unknown operation type: ${operationType}`);
            }

            // Skip payment in development mode
            if (SKIP_PAYMENT) {
                console.log('Skipping payment in development mode');
                await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate delay

                onPaymentSuccess?.({
                    transactionHash: 'dev-mode-' + Date.now(),
                    operationType,
                    amount,
                    ...additionalData
                });

                return true;
            }

            // Check if we're on the correct network
            const chainId = await window.ethereum.request({ method: 'eth_chainId' });
            const expectedChainId = '0xe0087f829'; // ETH Warsaw Holesky (60138453033)

            console.log('Current chain ID:', chainId, 'Expected:', expectedChainId);

            if (chainId !== expectedChainId) {
                throw new Error('Please switch to ETH Warsaw Holesky network first');
            }

            // Check balance before transaction
            const balance = await window.ethereum.request({
                method: 'eth_getBalance',
                params: [walletAddress, 'latest']
            });

            const balanceInEth = parseInt(balance, 16) / Math.pow(10, 18);
            const requiredAmount = parseFloat(amount);

            console.log('Wallet balance:', balanceInEth, 'ETH, Required:', requiredAmount, 'ETH');

            if (balanceInEth < requiredAmount) {
                throw new Error(`Insufficient balance. You have ${balanceInEth.toFixed(6)} ETH but need ${requiredAmount} ETH`);
            }

            // Convert ETH to Wei (hex) - simplified calculation
            const amountInWei = parseFloat(amount) * Math.pow(10, 18);
            const amountHex = '0x' + Math.floor(amountInWei).toString(16);

            // GolemDB treasury address for ETH Warsaw Holesky (backend address)
            const treasuryAddress = '0xEFeBB8310a011868A14297150084Cf92Bc658F1e';

            // Simplified transaction parameters - let MetaMask handle gas estimation
            const transactionParameters = {
                to: treasuryAddress,
                from: walletAddress,
                value: amountHex,
                // Remove gas and gasPrice to let MetaMask estimate
            };

            console.log('Transaction parameters:', transactionParameters);

            // Try to estimate gas first
            try {
                const gasEstimate = await window.ethereum.request({
                    method: 'eth_estimateGas',
                    params: [transactionParameters]
                });
                console.log('Gas estimate:', gasEstimate);
                transactionParameters.gas = gasEstimate;
            } catch (gasError) {
                console.warn('Gas estimation failed:', gasError);
                // Continue without gas estimation
            }

            // Request transaction
            const txHash = await window.ethereum.request({
                method: 'eth_sendTransaction',
                params: [transactionParameters],
            });

            console.log('Transaction sent:', txHash);
            setLastTransaction({ hash: txHash, type: operationType, amount });

            // Wait for transaction confirmation (simplified)
            await waitForTransaction(txHash);

            onPaymentSuccess?.({
                transactionHash: txHash,
                operationType,
                amount,
                ...additionalData
            });

            return true;

        } catch (error) {
            console.error('Payment error:', error);

            let errorMessage = 'Payment failed';

            if (error.code === 4001) {
                errorMessage = 'Transaction was rejected by user';
            } else if (error.code === -32603) {
                errorMessage = 'Internal JSON-RPC error. Please check your network connection and try again.';
            } else if (error.code === -32000) {
                errorMessage = 'Insufficient funds for gas or transaction value';
            } else if (error.message) {
                if (error.message.includes('insufficient funds')) {
                    errorMessage = 'Insufficient funds. Please add more ETH to your wallet.';
                } else if (error.message.includes('gas')) {
                    errorMessage = 'Gas estimation failed. Please try again with a lower amount.';
                } else if (error.message.includes('nonce')) {
                    errorMessage = 'Transaction nonce error. Please reset your MetaMask account.';
                } else {
                    errorMessage = error.message;
                }
            }

            onPaymentError?.(errorMessage);
            return false;
        } finally {
            setIsProcessing(false);
        }
    };

    const waitForTransaction = async (txHash) => {
        // Simple polling for transaction receipt
        // In production, you might want to use a more sophisticated approach
        let attempts = 0;
        const maxAttempts = 30; // 30 seconds timeout

        while (attempts < maxAttempts) {
            try {
                const receipt = await window.ethereum.request({
                    method: 'eth_getTransactionReceipt',
                    params: [txHash]
                });

                if (receipt && receipt.status) {
                    console.log('Transaction confirmed:', receipt);
                    return receipt;
                }
            } catch (error) {
                console.log('Waiting for transaction confirmation...');
            }

            await new Promise(resolve => setTimeout(resolve, 1000));
            attempts++;
        }

        throw new Error('Transaction confirmation timeout');
    };

    const PaymentButton = ({ operationType, children, disabled = false, ...props }) => (
        <div>
            <button
                {...props}
                disabled={disabled || isProcessing || !walletAddress}
                onClick={() => processPayment(operationType)}
                style={{
                    ...props.style,
                    opacity: (disabled || isProcessing || !walletAddress) ? 0.6 : 1,
                    cursor: (disabled || isProcessing || !walletAddress) ? 'not-allowed' : 'pointer'
                }}
            >
                {isProcessing ? 'Processing Payment...' : children}
            </button>
            {SKIP_PAYMENT && (
                <div style={{ fontSize: '0.75rem', color: '#6c757d', marginTop: '0.25rem' }}>
                    Development mode - payment will be simulated
                </div>
            )}
        </div>
    );

    return {
        processPayment,
        isProcessing,
        lastTransaction,
        PaymentButton,
        paymentAmounts: PAYMENT_AMOUNTS
    };
};

export default PaymentHandler;