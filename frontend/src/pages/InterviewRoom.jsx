import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth, api } from '../context/AuthContext';
import { useSocket } from '../context/SocketContext';
import { 
  Mic, 
  MicOff, 
  Video as VideoIcon, 
  VideoOff, 
  PhoneOff, 
  ShieldAlert, 
  Eye,
  Smartphone,
  Cpu,
  Sparkles
} from 'lucide-react';

const InterviewRoom = () => {
  const { roomId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { socket, connected } = useSocket();

  // Role: If logged in, they are recruiter. If not, they are candidate.
  const isRecruiter = !!user;

  // Stream Refs
  const localVideoRef = useRef(null);
  const remoteVideoRef = useRef(null);
  const localStreamRef = useRef(null);
  const canvasRef = useRef(document.createElement('canvas'));
  const peerConnectionRef = useRef(null);
  const remotePeerSidRef = useRef(null);
  const pendingIceCandidatesRef = useRef([]);
  const offerInProgressRef = useRef(false);
  const restartOfferRef = useRef(null);
  const frameIntervalRef = useRef(null);

  // Call configuration state
  const [micMuted, setMicMuted] = useState(false);
  const [videoOff, setVideoOff] = useState(false);
  const [mediaConnectionState, setMediaConnectionState] = useState('new');

  // Live Integrity Telemetry State (For Recruiter Monitor)
  const [integrityScore, setIntegrityScore] = useState(null);
  const [deepfakeScore, setDeepfakeScore] = useState(null);
  const [deepfakeAnalysisStatus, setDeepfakeAnalysisStatus] = useState('unavailable');
  const [livenessStatus, setLivenessStatus] = useState(null);
  const [livenessAnalysisStatus, setLivenessAnalysisStatus] = useState('unavailable');
  const [gazeAnalysisStatus, setGazeAnalysisStatus] = useState('unavailable');
  const [gazeDirection, setGazeDirection] = useState(null);
  const [lookingAway, setLookingAway] = useState(null);
  const [phoneAnalysisStatus, setPhoneAnalysisStatus] = useState('unavailable');
  const [phoneDetected, setPhoneDetected] = useState(null);
  const [phoneCount, setPhoneCount] = useState(0);
  const [bbox, setBbox] = useState(null); // [x, y, w, h] of face or phone
  
  // Real-time timeline alerts
  const [alerts, setAlerts] = useState([]);
  // Real-time integrity score logs for chart feed

  // WebRTC ICE Configuration
  const rtcConfig = {
    iceServers: [
      { urls: 'stun:stun.l.google.com:19302' },
      ...(import.meta.env.VITE_TURN_URL
        ? [{
            urls: import.meta.env.VITE_TURN_URL.split(',').map(url => url.trim()).filter(Boolean),
            username: import.meta.env.VITE_TURN_USERNAME,
            credential: import.meta.env.VITE_TURN_CREDENTIAL
          }]
        : [])
    ]
  };

  // 1. Connect Socket.IO once its provider has created the socket.
  useEffect(() => {
    if (!socket) return;
    if (!socket.connected) socket.connect();
    
    return () => {
      // Clean up intervals and streams
      if (frameIntervalRef.current) clearInterval(frameIntervalRef.current);
      if (localStreamRef.current) {
        localStreamRef.current.getTracks().forEach(track => track.stop());
      }
      if (peerConnectionRef.current) peerConnectionRef.current.close();
      socket.disconnect();
    };
  }, [socket]);

  // 2. Setup audio/video permissions and WebRTC signaling hooks
  useEffect(() => {
    if (!socket) return;
    const remoteVideoElement = remoteVideoRef.current;
    let disposed = false;
    let roomJoined = false;

    const applyPendingIceCandidates = async (pc, peerSid) => {
      const pending = pendingIceCandidatesRef.current;
      const candidatesForPeer = pending.filter(({ sender }) => sender === peerSid);
      pendingIceCandidatesRef.current = pending.filter(({ sender }) => sender !== peerSid);
      for (const { candidate } of candidatesForPeer) {
        try {
          await pc.addIceCandidate(candidate);
        } catch (err) {
          console.error('Unable to apply a buffered ICE candidate.');
        }
      }
    };

    const joinRoom = () => {
      if (!disposed && !roomJoined && localStreamRef.current) {
        socket.emit('join_room', { room: roomId, role: isRecruiter ? 'recruiter' : 'candidate' });
        roomJoined = true;
      }
    };

    const sendRecruiterOffer = async (sid, forceRestart = false) => {
      if (!isRecruiter || offerInProgressRef.current) return;
      const existingPeerConnection = peerConnectionRef.current;
      if (!forceRestart &&
        existingPeerConnection &&
        remotePeerSidRef.current === sid &&
        existingPeerConnection.signalingState !== 'closed' &&
        existingPeerConnection.connectionState !== 'failed'
      ) {
        return;
      }

      offerInProgressRef.current = true;
      try {
        const pc = createPeerConnection(sid);
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        socket.emit('rtc_offer', { room: roomId, sdp: pc.localDescription });
      } catch (err) {
        console.error('Unable to create the interview offer.');
      } finally {
        offerInProgressRef.current = false;
      }
    };
    restartOfferRef.current = (sid) => sendRecruiterOffer(sid, true);

    const handleDisconnect = () => {
      roomJoined = false;
      if (peerConnectionRef.current) peerConnectionRef.current.close();
      peerConnectionRef.current = null;
      remotePeerSidRef.current = null;
      pendingIceCandidatesRef.current = [];
      offerInProgressRef.current = false;
      setMediaConnectionState('new');
      if (remoteVideoElement) remoteVideoElement.srcObject = null;
    };

    const handlePeerLeft = ({ sid }) => {
      if (sid !== remotePeerSidRef.current) return;
      if (peerConnectionRef.current) peerConnectionRef.current.close();
      peerConnectionRef.current = null;
      remotePeerSidRef.current = null;
      pendingIceCandidatesRef.current = [];
      offerInProgressRef.current = false;
      setMediaConnectionState('new');
      if (remoteVideoElement) remoteVideoElement.srcObject = null;
    };

    const startSession = async () => {
      try {
        // Request webcam access
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        if (disposed) {
          stream.getTracks().forEach(track => track.stop());
          return;
        }
        localStreamRef.current = stream;
        if (localVideoRef.current) {
          localVideoRef.current.srcObject = stream;
        }

        // Trigger continuous canvas frame capture if Candidate
        if (!isRecruiter) {
          startFrameCapture();
        }
        joinRoom();
      } catch (err) {
        console.error('Lobby camera or microphone access failed.');
      }
    };

    socket.on('connect', joinRoom);

    // Listen for peer join alerts to initiate WebRTC Peer Connection
    socket.on('user_joined', ({ sid, role }) => {
      console.log(`Peer joined: ${sid} with role ${role}`);
      if (role === 'candidate') sendRecruiterOffer(sid);
    });

    socket.on('room_peers', (peers) => {
      const candidate = peers.find(peer => peer.role === 'candidate');
      if (candidate) sendRecruiterOffer(candidate.sid);
    });

    socket.on('rtc_ice_restart', ({ sender }) => {
      if (isRecruiter) sendRecruiterOffer(sender, true);
    });

    // WebRTC Signaling listeners
    socket.on('rtc_offer', async ({ sdp, sender }) => {
      if (!isRecruiter) {
        // Candidate receives offer and answers
        try {
          const pc = createPeerConnection(sender);
          await pc.setRemoteDescription(new RTCSessionDescription(sdp));
          await applyPendingIceCandidates(pc, sender);
          const answer = await pc.createAnswer();
          await pc.setLocalDescription(answer);
          socket.emit('rtc_answer', { room: roomId, sdp: pc.localDescription });
        } catch (err) {
          console.error('Unable to answer the interview offer.');
        }
      }
    });

    socket.on('rtc_answer', async ({ sdp }) => {
      if (peerConnectionRef.current) {
        try {
          const pc = peerConnectionRef.current;
          await pc.setRemoteDescription(new RTCSessionDescription(sdp));
          await applyPendingIceCandidates(pc, remotePeerSidRef.current);
        } catch (err) {
          console.error('Unable to apply the interview answer.');
        }
      }
    });

    socket.on('rtc_ice_candidate', async ({ candidate, sender }) => {
      if (candidate && sender) {
        const iceCandidate = new RTCIceCandidate(candidate);
        const pc = peerConnectionRef.current;
        if (!pc || !remotePeerSidRef.current) {
          pendingIceCandidatesRef.current.push({ sender, candidate: iceCandidate });
          return;
        }
        if (sender !== remotePeerSidRef.current) return;
        if (!pc.remoteDescription) {
          pendingIceCandidatesRef.current.push({ sender, candidate: iceCandidate });
          return;
        }
        try {
          await pc.addIceCandidate(iceCandidate);
        } catch (err) {
          console.error('Unable to add a remote ICE candidate.');
        }
      }
    });

    // Telemetry updates (Recruiter view)
    socket.on('metrics_update', (data) => {
      if (isRecruiter) {
        setIntegrityScore(data.integrity_score);
        setDeepfakeScore(data.deepfake_score);
        setDeepfakeAnalysisStatus(data.deepfake_status);
        setLivenessStatus(data.liveness_status);
        setLivenessAnalysisStatus(data.liveness_analysis_status);
        setGazeAnalysisStatus(data.gaze_analysis_status);
        setGazeDirection(data.gaze_direction);
        setLookingAway(data.looking_away);
        setPhoneDetected(data.phone_detected);
        setPhoneAnalysisStatus(data.phone_analysis_status);
        setPhoneCount(data.phone_count);
        setBbox(data.bbox);
        
        // Parse alerts if anomaly occurs
        if (data.phone_detected) {
          addAlert('Phone Detected', 'high', 'Smartphone visible in camera frame.');
        }
        if (data.deepfake_score !== null && data.deepfake_score > 0.6) {
          addAlert('Deepfake model score elevated', 'high', `Uncalibrated model output: ${(data.deepfake_score * 100).toFixed(1)}%. Requires human review.`);
        }
        if (data.looking_away) {
          addAlert('Gaze Deviation', 'medium', `Eye gaze offset: ${data.gaze_direction}`);
        }
        if (data.liveness_status === false) {
          addAlert('Liveness Verification Anomaly', 'high', 'Failed pattern challenge responses.');
        }
      }
    });

    socket.on('disconnect', handleDisconnect);
    socket.on('user_left', handlePeerLeft);
    startSession();
    if (socket.connected) joinRoom();

    return () => {
      disposed = true;
      restartOfferRef.current = null;
      if (frameIntervalRef.current) clearInterval(frameIntervalRef.current);
      frameIntervalRef.current = null;
      if (peerConnectionRef.current) peerConnectionRef.current.close();
      peerConnectionRef.current = null;
      remotePeerSidRef.current = null;
      pendingIceCandidatesRef.current = [];
      if (localStreamRef.current) {
        localStreamRef.current.getTracks().forEach(track => track.stop());
        localStreamRef.current = null;
      }
      if (remoteVideoElement) remoteVideoElement.srcObject = null;
      socket.off('connect', joinRoom);
      socket.off('disconnect', handleDisconnect);
      socket.off('user_left', handlePeerLeft);
      socket.off('user_joined');
      socket.off('room_peers');
      socket.off('rtc_offer');
      socket.off('rtc_answer');
      socket.off('rtc_ice_candidate');
      socket.off('rtc_ice_restart');
      socket.off('metrics_update');
    };
  // The handlers below close over helpers for this socket and room lifecycle.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [socket, roomId, isRecruiter]);

  // 3. WebRTC Peer Connection builder
  const createPeerConnection = (peerSid) => {
    if (peerConnectionRef.current && peerConnectionRef.current.signalingState !== 'closed') {
      peerConnectionRef.current.close();
    }
    const pc = new RTCPeerConnection(rtcConfig);
    peerConnectionRef.current = pc;
    remotePeerSidRef.current = peerSid;
    setMediaConnectionState(pc.connectionState);

    pc.onconnectionstatechange = () => {
      setMediaConnectionState(pc.connectionState);
      console.info('WebRTC connection state:', pc.connectionState);
    };
    pc.oniceconnectionstatechange = () => {
      console.info('WebRTC ICE state:', pc.iceConnectionState);
      if (pc.iceConnectionState === 'failed') {
        console.error('WebRTC ICE failed. Check TURN configuration and firewall reachability.');
        if (isRecruiter && remotePeerSidRef.current) {
          restartOfferRef.current?.(remotePeerSidRef.current);
        } else {
          socket?.emit('rtc_ice_restart', { room: roomId });
        }
      }
    };
    pc.onicecandidateerror = (event) => {
      console.warn('WebRTC ICE candidate gathering error:', event.errorCode);
    };

    // Attach local media tracks
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach(track => {
        pc.addTrack(track, localStreamRef.current);
      });
    }

    // ICE gathering hook
    pc.onicecandidate = (event) => {
      if (event.candidate && socket) {
        socket.emit('rtc_ice_candidate', { room: roomId, candidate: event.candidate });
      }
    };

    // Mount remote feed
    pc.ontrack = (event) => {
      console.log('Remote track received');
      if (remoteVideoRef.current) {
        remoteVideoRef.current.srcObject = event.streams[0];
        remoteVideoRef.current.play().catch(() => {
          console.error('Unable to autoplay the remote interview feed.');
        });
      }
    };
    return pc;
  };

  // 4. Candidate canvas frame extraction (Emitted at 5 FPS)
  const startFrameCapture = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    frameIntervalRef.current = setInterval(() => {
      const video = localVideoRef.current;
      if (video && video.readyState === video.HAVE_ENOUGH_DATA && socket && socket.connected) {
        // Set dimensions (downscale to 320x240 for high performance bandwidth saving)
        canvas.width = 320;
        canvas.height = 240;
        
        // Draw frame
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // Convert to base64
        const dataUrl = canvas.toDataURL('image/jpeg', 0.5); // 50% jpeg quality
        
        // Emit frame
        socket.emit('stream_frame', { room: roomId, frame: dataUrl });
      }
    }, 200); // 200ms = 5 FPS
  };

  const addAlert = (type, severity, desc) => {
    const timestamp = new Date().toLocaleTimeString();
    setAlerts(prev => [
      { id: Date.now(), timestamp, type, severity, desc },
      ...prev.slice(0, 9) // Limit to last 10 alerts
    ]);
  };

  const toggleMic = () => {
    if (localStreamRef.current) {
      const track = localStreamRef.current.getAudioTracks()[0];
      if (track) {
        track.enabled = !track.enabled;
        setMicMuted(!track.enabled);
      }
    }
  };

  const toggleVideo = () => {
    if (localStreamRef.current) {
      const track = localStreamRef.current.getVideoTracks()[0];
      if (track) {
        track.enabled = !track.enabled;
        setVideoOff(!track.enabled);
      }
    }
  };

  const handleEndInterview = async () => {
    try {
      // Tell backend to calculate final score and generate PDF report
      await api.post(`/interviews/end/${roomId}`, null, isRecruiter ? {} : { headers: { 'X-Meeting-Code': roomId } });
    } catch (err) {
      console.error('Error finalising the interview.');
    }
    
    // Stop local video tracks
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach(track => track.stop());
    }
    
    navigate(isRecruiter ? '/dashboard' : '/');
  };

  return (
    <div className="h-screen w-screen overflow-hidden bg-dark-950 text-dark-50 flex flex-col justify-between p-4 space-y-4">
      {/* Top Header */}
      <header className="flex h-12 shrink-0 items-center justify-between px-4 bg-dark-900 border border-dark-800 rounded-xl">
        <div className="flex items-center gap-2">
          <ShieldAlert className="h-5 w-5 text-brand-500" />
          <span className="text-sm font-extrabold tracking-tight">InterviewGuard Live Room</span>
          <span className="text-xs px-2 py-0.5 bg-dark-800 border border-dark-700 rounded-full font-mono text-dark-300">
            ID: {roomId}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className={`h-2.5 w-2.5 rounded-full ${connected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`}></span>
          <span className="text-xs font-semibold text-dark-300">
            Signaling {connected ? 'Connected' : 'Disconnected'}
          </span>
          <span className={`h-2.5 w-2.5 rounded-full ${mediaConnectionState === 'connected' ? 'bg-emerald-500' : mediaConnectionState === 'failed' ? 'bg-rose-500' : 'bg-amber-400'}`}></span>
          <span className="text-xs font-semibold text-dark-300">
            Media {mediaConnectionState === 'new' ? 'Waiting' : mediaConnectionState}
          </span>
        </div>
      </header>

      {/* Main workspace */}
      <div className="flex-1 flex flex-col lg:flex-row gap-4 min-h-0 overflow-hidden">
        {/* Videos block */}
        <div className="flex-1 flex flex-col md:flex-row gap-4 min-h-0 min-w-0">
          {/* Main remote participant feed */}
          <div className="flex-1 rounded-2xl border border-dark-800 bg-dark-900 relative overflow-hidden flex items-center justify-center">
            <video
              ref={remoteVideoRef}
              autoPlay
              playsInline
              className="w-full h-full object-cover scale-x-[-1]"
            />
            
            {/* Draw Overlay Bounding Box (Recruiter Side Only) */}
            {isRecruiter && bbox && (
              <div 
                className="absolute border-2 border-brand-500 bg-brand-500/10 pointer-events-none rounded-lg"
                style={{
                  // The backend coordinates are for 320x240 capture window. Map to percent offsets
                  left: `${(bbox[0] / 320) * 100}%`,
                  top: `${(bbox[1] / 240) * 100}%`,
                  width: `${(bbox[2] / 320) * 100}%`,
                  height: `${(bbox[3] / 240) * 100}%`,
                  transition: 'all 0.1s ease-out'
                }}
              >
                {/* Alert Tag on top of Bounding box */}
                <div className="absolute -top-6 left-0 bg-brand-600 text-[10px] font-bold text-white px-2 py-0.5 rounded border border-brand-500 shadow-md">
                  {phoneDetected ? 'Device Trigger' : 'Analyzed Face'}
                </div>
              </div>
            )}

            <div className="absolute bottom-4 left-4 bg-dark-950/80 px-3 py-1.5 rounded-lg border border-dark-800 text-xs font-bold flex items-center gap-2">
              <span className="h-1.5 w-1.5 bg-brand-500 rounded-full animate-ping"></span>
              {isRecruiter ? 'Candidate Feed' : 'Recruiter Feed'}
            </div>
          </div>

          {/* Self Preview Feed (Small side box) */}
          <div className="w-full md:w-60 h-44 md:h-auto md:aspect-[3/4] shrink-0 rounded-2xl border border-dark-800 bg-dark-900 overflow-hidden relative flex items-center justify-center">
            <video
              ref={localVideoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover scale-x-[-1]"
            />
            <div className="absolute bottom-4 left-4 bg-dark-950/80 px-3 py-1.5 rounded-lg border border-dark-800 text-xs font-bold">
              My Preview
            </div>
          </div>
        </div>

        {/* AI Telemetry Panel (Recruiter Workspace Side - Mock placeholder for candidate) */}
        {isRecruiter ? (
          <div className="w-full lg:w-96 shrink-0 flex flex-col gap-4 min-h-0 overflow-y-auto pr-1">
            {/* Integrity circular score block */}
            <div className="glass p-6 rounded-2xl border border-dark-800 flex items-center gap-6 relative overflow-hidden">
              <div className="relative h-20 w-20 flex items-center justify-center shrink-0">
                {/* Circular ring path */}
                <svg className="absolute w-full h-full -rotate-90">
                  <circle cx="40" cy="40" r="34" className="stroke-dark-800 fill-none" strokeWidth="6" />
                  <circle 
                    cx="40" 
                    cy="40" 
                    r="34" 
                    className="fill-none transition-all duration-300" 
                    strokeWidth="6" 
                    strokeDasharray={2 * Math.PI * 34}
                    strokeDashoffset={2 * Math.PI * 34 * (1 - (integrityScore ?? 0) / 100)}
                    stroke={integrityScore == null ? '#6B7280' : (integrityScore >= 85 ? '#10B981' : (integrityScore >= 60 ? '#F59E0B' : '#EF4444'))}
                  />
                </svg>
                <span className="text-lg font-extrabold">{integrityScore == null ? '—' : integrityScore.toFixed(0)}</span>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-semibold text-dark-300 uppercase tracking-wider">Integrity score index</p>
                <h4 className="text-lg font-bold">
                  {integrityScore == null ? 'Analysis unavailable' : (integrityScore >= 85 ? 'Low Risk Factor' : (integrityScore >= 60 ? 'Medium Risk Alert' : 'High Risk Level'))}
                </h4>
                <p className="text-xs text-dark-300">Automated flags are observations for human review, not proof of misconduct.</p>
              </div>
            </div>

            {/* AI Core detail gauges */}
            <div className="glass p-5 rounded-2xl border border-dark-800 space-y-4">
              <h3 className="text-sm font-bold border-b border-dark-800/80 pb-2">Subsystem Telemetry</h3>
              
              {/* Deepfake */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="flex items-center gap-1"><Cpu className="h-3.5 w-3.5" /> Deepfake model score</span>
                  <span className="font-mono">{deepfakeScore == null ? deepfakeAnalysisStatus : deepfakeScore.toFixed(2)}</span>
                </div>
                <div className="h-2 w-full bg-dark-800 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-indigo-500 transition-all duration-200" 
                    style={{ width: `${(deepfakeScore ?? 0) * 100}%` }}
                  />
                </div>
              </div>

              {/* Eye gaze */}
              <div className="flex items-center justify-between text-xs p-2 bg-dark-900/60 rounded-lg border border-dark-800">
                <span className="flex items-center gap-1"><Eye className="h-3.5 w-3.5" /> Eye Gaze Vector</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                  lookingAway ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                }`}>
                  {gazeAnalysisStatus !== 'analyzed' ? gazeAnalysisStatus : (lookingAway ? `AWAY (${gazeDirection?.toUpperCase()})` : 'CENTER')}
                </span>
              </div>

              {/* YOLO phone */}
              <div className="flex items-center justify-between text-xs p-2 bg-dark-900/60 rounded-lg border border-dark-800">
                <span className="flex items-center gap-1"><Smartphone className="h-3.5 w-3.5" /> Device visibility</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                  phoneDetected ? 'bg-rose-500/15 text-rose-400 border border-rose-500/20 animate-pulse' : phoneAnalysisStatus === 'analyzed' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                }`}>
                  {phoneDetected ? `${phoneCount} PHONE(S) DETECTED` : phoneAnalysisStatus === 'analyzed' ? 'NO PHONE OBSERVED' : phoneAnalysisStatus}
                </span>
              </div>

              {/* Liveness challenge */}
              <div className="flex items-center justify-between text-xs p-2 bg-dark-900/60 rounded-lg border border-dark-800">
                <span className="flex items-center gap-1"><Sparkles className="h-3.5 w-3.5" /> Liveness status</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                  livenessStatus === true ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : livenessStatus === false ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                }`}>
                  {livenessStatus === true ? 'NO ANOMALY OBSERVED' : livenessStatus === false ? 'ANOMALY OBSERVED' : livenessAnalysisStatus}
                </span>
              </div>
            </div>

            {/* Alert timeline logs */}
            <div className="glass p-5 rounded-2xl border border-dark-800 flex-1 flex flex-col min-h-0">
              <h3 className="text-sm font-bold border-b border-dark-800/80 pb-2 mb-3">Live Security Alerts</h3>
              <div className="flex-1 overflow-y-auto space-y-2 pr-1">
                {alerts.length === 0 ? (
                  <p className="text-xs text-dark-300 text-center py-4">No security anomalies detected yet.</p>
                ) : (
                  alerts.map(a => (
                    <div 
                      key={a.id} 
                      className={`p-2.5 rounded-xl border text-xs space-y-1 ${
                        a.severity === 'high' 
                          ? 'bg-rose-500/5 border-rose-500/15 text-rose-400' 
                          : 'bg-amber-500/5 border-amber-500/15 text-amber-400'
                      }`}
                    >
                      <div className="flex justify-between font-bold">
                        <span>{a.type}</span>
                        <span className="font-mono text-[10px] opacity-80">{a.timestamp}</span>
                      </div>
                      <p className="opacity-90 leading-relaxed text-[11px]">{a.desc}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        ) : (
          // Candidate visual side helper
          <div className="w-full lg:w-96 shrink-0 glass p-6 rounded-2xl border border-dark-800 flex flex-col justify-between">
            <div className="space-y-4">
              <h3 className="text-lg font-bold">Secure Interview Session</h3>
              <p className="text-xs text-dark-300 leading-relaxed">
                You are currently in a live security-monitored interview room.
              </p>
              
              <div className="p-4 rounded-xl bg-dark-900 border border-dark-800 space-y-3 text-xs text-dark-100">
                <p className="font-bold flex items-center gap-1 text-brand-400">🛡️ InterviewGuard Compliance</p>
                <ul className="list-disc pl-4 space-y-1.5 opacity-90">
                  <li>Please remain centered in front of your camera.</li>
                  <li>Avoid looking away or checking mobile devices.</li>
                  <li>Ensure the room remains well-lit and quiet.</li>
                </ul>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-brand-500/5 border border-brand-500/15 flex items-center gap-3">
              <Sparkles className="h-6 w-6 text-brand-400 animate-spin" />
              <p className="text-[11px] text-dark-300 leading-normal">
                Supported analyzers store observations when available. Missing evidence remains unavailable, and automated flags require human review.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Control panel buttons */}
      <footer className="h-16 shrink-0 bg-dark-900 border border-dark-800 rounded-xl flex items-center justify-between px-6">
        <div className="flex items-center gap-3">
          <button 
            onClick={toggleMic}
            className={`p-3 rounded-lg border transition-all ${
              micMuted 
                ? 'bg-rose-500/10 border-rose-500/20 text-rose-400' 
                : 'bg-dark-800 border-dark-700 hover:bg-dark-700 text-dark-100'
            }`}
          >
            {micMuted ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
          </button>
          <button 
            onClick={toggleVideo}
            className={`p-3 rounded-lg border transition-all ${
              videoOff 
                ? 'bg-rose-500/10 border-rose-500/20 text-rose-400' 
                : 'bg-dark-800 border-dark-700 hover:bg-dark-700 text-dark-100'
            }`}
          >
            {videoOff ? <VideoOff className="h-5 w-5" /> : <VideoIcon className="h-5 w-5" />}
          </button>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleEndInterview}
            className="flex items-center gap-2 bg-rose-600 hover:bg-rose-700 text-sm font-bold px-6 py-3 rounded-xl transition-all text-white glow-rose"
          >
            <PhoneOff className="h-5 w-5" />
            End Session
          </button>
        </div>
      </footer>
    </div>
  );
};

export default InterviewRoom;
