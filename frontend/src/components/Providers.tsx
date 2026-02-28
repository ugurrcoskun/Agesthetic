'use client';
import '@rainbow-me/rainbowkit/styles.css';
import {
    RainbowKitProvider,
    darkTheme,
    connectorsForWallets
} from '@rainbow-me/rainbowkit';
import { injectedWallet } from '@rainbow-me/rainbowkit/wallets';
import { WagmiProvider, createConfig, http } from 'wagmi';
import {
    QueryClientProvider,
    QueryClient,
} from '@tanstack/react-query';
import { defineChain } from 'viem';

const monadTestnet = defineChain({
    id: 10143,
    name: 'Monad Testnet',
    network: 'monad-testnet',
    nativeCurrency: {
        decimals: 18,
        name: 'Monad',
        symbol: 'MON',
    },
    rpcUrls: {
        default: { http: ['https://testnet-rpc.monad.xyz/'] },
        public: { http: ['https://testnet-rpc.monad.xyz/'] },
    },
    blockExplorers: {
        default: { name: 'Monad Explorer', url: 'https://testnet.monadexplorer.com' },
    },
    testnet: true,
});

const connectors = connectorsForWallets(
    [
        {
            groupName: 'Wallets',
            wallets: [injectedWallet],
        },
    ],
    {
        appName: 'IntroAgent',
        projectId: 'N/A',
    }
);

const config = createConfig({
    connectors,
    chains: [monadTestnet],
    transports: {
        [monadTestnet.id]: http(),
    },
    ssr: true,
});

const queryClient = new QueryClient();

export function Providers({ children }: { children: React.ReactNode }) {
    return (
        <WagmiProvider config={config}>
            <QueryClientProvider client={queryClient}>
                <RainbowKitProvider theme={darkTheme()}>
                    {children}
                </RainbowKitProvider>
            </QueryClientProvider>
        </WagmiProvider>
    );
}
