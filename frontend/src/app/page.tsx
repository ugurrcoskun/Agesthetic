'use client';

import React, { useState, useEffect, useRef } from 'react';
import styles from './page.module.css';
import { ConnectButton } from '@rainbow-me/rainbowkit';
import { useAccount, useSendTransaction, useWaitForTransactionReceipt } from 'wagmi';
import { parseEther } from 'viem';

const RECIPIENT_ADDRESS = '0x48ea78ab2002B33C29e83f3be3addcf1daC83544';

// --- Text Scramble Utility ---
class TextScramble {
  el: HTMLElement;
  chars: string;
  queue: any[];
  frameRequest: number;
  frame: number;
  resolve: any;

  constructor(el: HTMLElement) {
    this.el = el;
    this.chars = '!<>-_\\\\/[]{}—=+*^?#________';
    this.queue = [];
    this.frameRequest = 0;
    this.frame = 0;
    this.update = this.update.bind(this);
  }

  setText(newText: string) {
    const oldText = this.el.innerText;
    const length = Math.max(oldText.length, newText.length);
    const promise = new Promise((resolve) => (this.resolve = resolve));
    this.queue = [];
    for (let i = 0; i < length; i++) {
      const from = oldText[i] || '';
      const to = newText[i] || '';
      const start = Math.floor(Math.random() * 40);
      const end = start + Math.floor(Math.random() * 40);
      this.queue.push({ from, to, start, end });
    }
    cancelAnimationFrame(this.frameRequest);
    this.frame = 0;
    this.update();
    return promise;
  }

  update() {
    let output = '';
    let complete = 0;
    for (let i = 0, n = this.queue.length; i < n; i++) {
      let { from, to, start, end, char } = this.queue[i];
      if (this.frame >= end) {
        complete++;
        output += to;
      } else if (this.frame >= start) {
        if (!char || Math.random() < 0.28) {
          char = this.randomChar();
          this.queue[i].char = char;
        }
        output += `<span style="color:var(--text-ghost); opacity:0.7">${char}</span>`;
      } else {
        output += from;
      }
    }
    this.el.innerHTML = output;
    if (complete === this.queue.length) {
      this.resolve();
    } else {
      this.frameRequest = requestAnimationFrame(this.update);
      this.frame++;
    }
  }

  randomChar() {
    return this.chars[Math.floor(Math.random() * this.chars.length)];
  }
}

// --- Scrambled Text Component ---
function ScrambleText({ text }: { text: string }) {
  const elRef = useRef<HTMLDivElement>(null);
  const scramblerRef = useRef<TextScramble | null>(null);

  useEffect(() => {
    if (elRef.current && text) {
      if (!scramblerRef.current) {
        scramblerRef.current = new TextScramble(elRef.current);
      }
      scramblerRef.current.setText(text);
    }
  }, [text]);

  return <div ref={elRef} className={styles.termBody} />;
}

// --- Types ---
interface TerminalBlock {
  id: string;
  header: string;
  isErr: boolean;
  isDM?: boolean;
  contentStr?: string;
  parsedDMs?: any[];
}

export default function Home() {
  const [targetName, setTargetName] = useState('');
  const [purpose, setPurpose] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const [network, setNetwork] = useState<any[]>([]);
  const [terminalBlocks, setTerminalBlocks] = useState<TerminalBlock[]>([]);

  const termEndRef = useRef<HTMLDivElement>(null);

  // HUD State
  const [hudState, setHudState] = useState({
    researcher: 'Awaiting Link',
    matchmaker: 'Awaiting Link',
    copywriter: 'Awaiting Link'
  });

  const [hudClass, setHudClass] = useState({
    researcher: styles.hudNode,
    matchmaker: styles.hudNode,
    copywriter: styles.hudNode
  });

  // --- Web3 State ---
  const { isConnected } = useAccount();
  const { data: hash, sendTransaction, error: txError } = useSendTransaction();
  const { isLoading: isConfirming, isSuccess: isConfirmed } = useWaitForTransactionReceipt({
    hash,
  });

  const [isPendingPayment, setIsPendingPayment] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalDMs, setModalDMs] = useState<any[]>([]);

  useEffect(() => {
    fetchNetwork();
  }, []);

  useEffect(() => {
    termEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [terminalBlocks]);

  useEffect(() => {
    if (isConfirmed && isPendingPayment) {
      setIsPendingPayment(false);
      addTerminalBlock('PAYMENT', `Transfer Confirmed. TX: ${hash}`, false);
      runAgents();
    }
  }, [isConfirmed, isPendingPayment, hash]);

  useEffect(() => {
    if (txError && isPendingPayment) {
      setIsPendingPayment(false);
      setIsLoading(false);
      addTerminalBlock('PAYMENT_ERR', `Transaction failed: ${txError.message}`, true);
    }
  }, [txError, isPendingPayment]);

  const fetchNetwork = async () => {
    try {
      const res = await fetch('/api/attendees');
      const data = await res.json();
      setNetwork(data);
    } catch (e) {
      console.error(e);
    }
  };

  const addTerminalBlock = (header: string, bodyStr: string, isErr = false, isDM = false) => {
    const newBlock: TerminalBlock = {
      id: Math.random().toString(36).substr(2, 9),
      header,
      isErr,
      isDM,
      contentStr: bodyStr,
    };

    if (isDM) {
      try {
        let cleanStr = bodyStr.replace(/```json/g, "").replace(/```/g, "").trim();
        const parseResult = JSON.parse(cleanStr);
        newBlock.parsedDMs = parseResult.dms || [];
        setModalDMs(parseResult.dms || []);
        setIsModalOpen(true);
      } catch (e) {
        console.error("Failed to parse DMs JSON", e);
      }
    }

    setTerminalBlocks(prev => [...prev, newBlock]);
  };

  const handleCopy = (text: string, e: React.MouseEvent<HTMLButtonElement>) => {
    navigator.clipboard.writeText(text);
    const btn = e.currentTarget;
    const oldText = btn.textContent;
    btn.textContent = 'Data Copied';
    btn.style.background = 'var(--cyan-glow)';
    btn.style.color = '#000';
    btn.style.borderColor = 'var(--cyan-glow)';
    setTimeout(() => {
      btn.textContent = oldText;
      btn.style.background = 'transparent';
      btn.style.color = 'var(--pink-neon)';
      btn.style.borderColor = 'var(--pink-neon)';
    }, 2000);
  };

  const initiateSequence = () => {
    if (!targetName || !purpose) {
      addTerminalBlock('ERR_REQUIRED_PARAMS_MISSING', 'Validation failed. Need Target and Mission.', true);
      return;
    }

    if (!isConnected) {
      addTerminalBlock('AUTH_ERR', 'Wallet connection required.', true);
      return;
    }

    addTerminalBlock('SYS_AUTH', `Initiating Transfer to ${RECIPIENT_ADDRESS}... Amount: 0.01 MONAD`, false);
    setIsLoading(true);
    setIsPendingPayment(true);

    sendTransaction({
      to: RECIPIENT_ADDRESS as `0x${string}`,
      value: parseEther('0.01'),
    });
  };

  const runAgents = () => {
    setIsLoading(true);
    setTerminalBlocks(prev => [...prev, {
      id: 'init',
      header: 'SYS_INIT',
      isErr: false,
      contentStr: 'Establishing secure connection to Agesthetic Core...'
    }]);

    setHudState({ researcher: 'Awaiting Link', matchmaker: 'Awaiting Link', copywriter: 'Awaiting Link' });
    setHudClass({ researcher: styles.hudNode, matchmaker: styles.hudNode, copywriter: styles.hudNode });

    const url = `/api/run?target_name=${encodeURIComponent(targetName)}&purpose=${encodeURIComponent(purpose)}`;
    const evtSource = new EventSource(url);

    evtSource.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'agent_start':
          setHudClass(prev => ({ ...prev, [data.agent]: `${styles.hudNode} ${styles.active}` }));
          setHudState(prev => ({ ...prev, [data.agent]: 'Processing Data...' }));
          addTerminalBlock(`NODE_${data.agent.toUpperCase()}`, data.message);
          break;

        case 'agent_done':
          setHudClass(prev => ({ ...prev, [data.agent]: `${styles.hudNode} ${styles.done}` }));
          setHudState(prev => ({ ...prev, [data.agent]: 'Task Complete' }));

          let isDM = data.agent === 'copywriter';
          let payloadResult = data.result;

          if (isDM && (!payloadResult || !payloadResult.includes('{'))) {
            payloadResult = JSON.stringify({
              "dms": [
                { "label": "Primary (Warm & Genuine)", "text": `Hey ${targetName}! Would love to connect regarding ${purpose}.` },
                { "label": "Professional", "text": `Dear ${targetName}, reaching out to discuss ${purpose}.` },
                { "label": "Casual", "text": `Yo ${targetName}! Let's chat about ${purpose}.` }
              ],
              "personalization_points": ["Mock data loaded due to API limit"],
              "recipient": targetName
            });
          }

          addTerminalBlock(`N_${data.agent.toUpperCase()}_RES`, payloadResult, false, isDM);
          break;

        case 'complete':
          evtSource.close();
          setIsLoading(false);
          addTerminalBlock('SYS_HALT', data.message);
          break;

        case 'error':
          evtSource.close();
          setIsLoading(false);
          addTerminalBlock('FATAL_ERR', data.message, true);
          break;
      }
    };

    evtSource.onerror = () => {
      evtSource.close();
      setIsLoading(false);
      addTerminalBlock('CONN_LOST', 'Connection to server terminated.', true);
    };
  };

  return (
    <>
      <div className="vignette"></div>

      <div className={styles.cyberContainer}>
        <main className={styles.primaryCol}>
          <header className={styles.sysHeader}>
            <div className={`${styles.decorAngle} ${styles.decorTl}`}></div>
            <div className={`${styles.decorAngle} ${styles.decorBr}`}></div>
            <div className={styles.sysInfo}>
              <div className="glitch-wrapper">
                <h1 className="glitch" data-text="AGESTHETIC">AGESTHETIC</h1>
              </div>
            </div>
            <div style={{ position: 'absolute', top: '20px', right: '20px', zIndex: 100 }}>
              <ConnectButton showBalance={false} />
            </div>
          </header>

          <section className={styles.cyberPanel}>
            <div className={styles.panelHeader}>Target Info</div>

            <div className={styles.cyberInputGroup}>
              <label>Name</label>
              <input
                type="text"
                value={targetName}
                onChange={(e) => setTargetName(e.target.value)}
                className={styles.cyberInput}
                placeholder="e.g. Kerem Turgutlu"
                autoComplete="off"
              />
            </div>

            <div className={styles.cyberInputGroup}>
              <label>Purpose</label>
              <textarea
                value={purpose}
                onChange={(e) => setPurpose(e.target.value)}
                className={styles.cyberInput}
                placeholder="Initiate handshake protocol..."></textarea>
            </div>

            {(!isConnected) ? (
              <div style={{ marginBottom: '15px' }}>
                <ConnectButton.Custom>
                  {({ account, chain, openConnectModal, mounted }) => {
                    const ready = mounted;
                    const connected = ready && account && chain;
                    return (
                      <div {...(!ready && { 'aria-hidden': true, style: { opacity: 0, pointerEvents: 'none', userSelect: 'none' } })}>
                        {!connected && (
                          <button onClick={openConnectModal} type="button" className={styles.cyberBtn}>
                            Connect Wallet to Execute
                          </button>
                        )}
                      </div>
                    );
                  }}
                </ConnectButton.Custom>
              </div>
            ) : (
              <button
                disabled={isLoading || isConfirming}
                className={`${styles.cyberBtn} ${(isLoading || isConfirming) ? styles.loading : ''}`}
                onClick={initiateSequence}
              >
                {(isLoading || isConfirming) && <span className={styles.spinner}></span>}
                Execute Analysis
              </button>
            )}
          </section>

          <section className={styles.cyberPanel}>
            <div className={styles.panelHeader}>Analysis Log</div>
            <div className={styles.terminalOutput}>
              {terminalBlocks.length === 0 && (
                <div style={{ color: '#666' }}>Waiting for execution command...</div>
              )}

              {terminalBlocks.map((block) => (
                <div key={block.id} className={styles.terminalBlock}>
                  <div className={styles.termHeader} style={{ color: block.isErr ? 'var(--pink-neon)' : '' }}>
                    {block.header}
                  </div>

                  {block.isDM && block.parsedDMs ? (
                    block.parsedDMs.map((dm: any, i: number) => (
                      <div key={i} className={styles.dmDraftContainer}>
                        <div style={{
                          position: 'absolute', top: '-10px', right: '20px',
                          background: 'var(--bg)', color: 'var(--cyan-glow)',
                          padding: '0 10px', fontSize: '0.7rem', fontWeight: 700,
                          textTransform: 'uppercase'
                        }}>
                          {dm.label || 'SECURE_PAYLOAD'}
                        </div>
                        <ScrambleText text={dm.text} />
                        <div className={styles.termAction}>
                          <button className={styles.btnTermCopy} onClick={(e) => handleCopy(dm.text, e)}>
                            Extract Payload
                          </button>
                        </div>
                      </div>
                    ))
                  ) : (
                    <ScrambleText text={block.contentStr || ''} />
                  )}
                </div>
              ))}
              <div ref={termEndRef} />
            </div>
          </section>
        </main>

        <aside className={styles.sidebarCol}>
          <section className={styles.cyberPanel} style={{ padding: '20px' }}>
            <div className={styles.panelHeader} style={{ fontSize: '1rem' }}>System Nodes</div>

            <div className={styles.hudPipeline}>
              <div className={hudClass.researcher}>
                <div className={styles.hudNodeId}>01</div>
                <div className={styles.hudNodeData}>
                  <div className={styles.hudNodeName}>Researcher</div>
                  <div className={styles.hudNodeStatus}>{hudState.researcher}</div>
                </div>
              </div>

              <div className={hudClass.matchmaker}>
                <div className={styles.hudNodeId}>02</div>
                <div className={styles.hudNodeData}>
                  <div className={styles.hudNodeName}>Matchmaker</div>
                  <div className={styles.hudNodeStatus}>{hudState.matchmaker}</div>
                </div>
              </div>

              <div className={hudClass.copywriter}>
                <div className={styles.hudNodeId}>03</div>
                <div className={styles.hudNodeData}>
                  <div className={styles.hudNodeName}>Copywriter</div>
                  <div className={styles.hudNodeStatus}>{hudState.copywriter}</div>
                </div>
              </div>
            </div>
          </section>

          <section className={styles.cyberPanel} style={{ padding: '20px' }}>
            <div className={styles.panelHeader} style={{ fontSize: '1rem', marginBottom: '10px' }}>Network Graph</div>
            <div style={{ fontFamily: 'var(--font-code)', fontSize: '0.8rem', color: '#666', marginBottom: '15px' }}>
              Available Connections <span style={{ color: 'var(--cyan-glow)', float: 'right' }}>[{network.length}]</span>
            </div>

            <div className={styles.dataGrid}>
              {network.map((p: any, i: number) => {
                const initials = p.name.split(' ').map((n: string) => n[0]).join('').substring(0, 2);
                return (
                  <div
                    key={i}
                    className={styles.dataRow}
                    onClick={() => {
                      setTargetName(p.name);
                      document.querySelector('textarea')?.focus();
                    }}
                  >
                    <div className={styles.dataAvatar}>{initials}</div>
                    <div className={styles.dataInfo}>
                      <div className={styles.dataName}>{p.name}</div>
                      <div className={styles.dataMeta}>{p.x_handle} | {p.title?.split('@')[0] || ''}</div>
                    </div>
                    <div className={`${styles.dataSignal} ${styles[p.connection_strength]}`}>
                      {p.connection_strength}
                    </div>
                  </div>
                )
              })}
            </div>
          </section>
        </aside>
      </div>

      {isModalOpen && (
        <div className={styles.modalOverlay}>
          <div className={styles.modalContent}>
            <button className={styles.modalClose} onClick={() => setIsModalOpen(false)}>X CLOSE</button>
            <div className={styles.panelHeader} style={{ marginBottom: '30px' }}>Generated Execution Payload</div>
            {modalDMs.map((dm: any, i: number) => (
              <div key={i} className={styles.dmDraftContainer} style={{ marginBottom: '25px', padding: '30px 20px 20px' }}>
                <div style={{
                  position: 'absolute', top: '-10px', right: '20px',
                  background: 'var(--bg)', color: 'var(--cyan-glow)',
                  padding: '0 10px', fontSize: '0.8rem', fontWeight: 700,
                  textTransform: 'uppercase', border: '1px solid var(--pink-neon)'
                }}>
                  {dm.label || 'SECURE_PAYLOAD'}
                </div>
                <div className={styles.termBody} style={{ fontSize: '1rem', marginBottom: '10px' }}>{dm.text}</div>
                <div className={styles.termAction}>
                  <button className={styles.btnTermCopy} onClick={(e) => handleCopy(dm.text, e)}>
                    COPY TO CLIPBOARD
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
