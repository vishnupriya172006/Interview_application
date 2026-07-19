import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { api } from '../context/AuthContext';
import { 
  Camera, 
  Mic, 
  ShieldAlert, 
  CheckCircle, 
  Wifi, 
  AlertCircle,
  VideoOff,
  MicOff
} from 'lucide-react';

const MeetingCheck = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const roomId = searchParams.get('room');
  
  const [meeting, setMeeting] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Permissions & Pre-flight checks state
  const [cameraPerm, setCameraPerm] = useState('checking'); // checking, granted, denied
  const [micPerm, setMicPerm] = useState('checking');
  const [latency, setLatency] = useState('checking');
  
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  // 1. Validate meeting room first
  useEffect(() => {
    const validate = async () => {
      if (!roomId) {
        setError('Missing meeting room ID. Please open the correct link received in your email.');
        setLoading(false);
        return;
      }
      try {
        const response = await api.get(`/interviews/validate/${roomId}`);
        setMeeting(response.data);
        startDeviceChecks();
      } catch (err) {
        setError(err.response?.data?.detail || 'This interview room is invalid, cancelled, or already completed.');
        setLoading(false);
      }
    };
    validate();
    
    return () => {
      // Release camera stream on clean up
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, [roomId]);

  // 2. Perform camera & microphone check
  const startDeviceChecks = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      streamRef.current = stream;
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      
      setCameraPerm('granted');
      setMicPerm('granted');
      
      // Simulate network latency check
      const start = Date.now();
      await api.get('/'); // Hit root to measure latency
      setLatency(`${Date.now() - start} ms`);
      
    } catch (err) {
      console.error('Device access denied:', err);
      // Check individual permissions if possible
      try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const hasVideo = devices.some(d => d.kind === 'videoinput');
        const hasAudio = devices.some(d => d.kind === 'audioinput');
        
        setCameraPerm(hasVideo ? 'denied' : 'not_found');
        setMicPerm(hasAudio ? 'denied' : 'not_found');
      } catch (e) {
        setCameraPerm('denied');
        setMicPerm('denied');
      }
      setLatency('Unknown');
    } finally {
      setLoading(false);
    }
  };

  const handleJoin = () => {
    // Stop local check streams before moving to main room
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    navigate(`/interview/${roomId}`);
  };

  return (
    <div className="min-h-screen bg-dark-950 bg-grid text-dark-50 flex items-center justify-center p-6">
      <div className="w-full max-w-3xl space-y-6">
        {/* Header */}
        <div className="flex items-center gap-3 justify-center mb-4">
          <ShieldAlert className="h-10 w-10 text-brand-500" />
          <h1 className="text-2xl font-bold">InterviewGuard System Check</h1>
        </div>

        {loading ? (
          <div className="glass p-8 rounded-2xl border border-dark-800 text-center space-y-4">
            <div className="h-8 w-8 border-4 border-t-transparent border-brand-500 rounded-full animate-spin mx-auto"></div>
            <p className="text-sm text-dark-300">Verifying session token and hardware access...</p>
          </div>
        ) : error ? (
          <div className="glass p-8 rounded-2xl border border-rose-500/20 text-center space-y-4 glow-rose">
            <AlertCircle className="h-12 w-12 text-rose-400 mx-auto" />
            <h3 className="text-lg font-bold">Verification Failed</h3>
            <p className="text-sm text-dark-300 max-w-md mx-auto">{error}</p>
            <button 
              onClick={() => navigate('/')}
              className="bg-dark-900 border border-dark-800 hover:bg-dark-800 px-6 py-2 rounded-lg text-sm transition-colors"
            >
              Back to Home
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Video Preview Box */}
            <div className="glass rounded-2xl overflow-hidden border border-dark-800 relative bg-dark-950/60 aspect-[4/3] flex items-center justify-center">
              {cameraPerm === 'granted' ? (
                <video 
                  ref={videoRef} 
                  autoPlay 
                  playsInline 
                  muted 
                  className="w-full h-full object-cover scale-x-[-1]"
                />
              ) : (
                <div className="text-center space-y-3 p-4">
                  <VideoOff className="h-12 w-12 text-rose-500 mx-auto" />
                  <p className="text-sm font-semibold">Webcam Stream Blocked</p>
                  <p className="text-xs text-dark-300 max-w-[200px]">Please enable camera permissions in your browser address bar.</p>
                </div>
              )}
              {/* Profile tag overlays */}
              <div className="absolute bottom-4 left-4 bg-dark-950/80 px-3 py-1.5 rounded-lg border border-dark-800 text-xs font-semibold">
                {meeting?.candidate_name} (Candidate)
              </div>
            </div>

            {/* Checklist Box */}
            <div className="glass p-6 rounded-2xl border border-dark-800 flex flex-col justify-between">
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-bold">Lobby Pre-Flight Check</h3>
                  <p className="text-xs text-dark-300">All checks must pass to join the secure interview.</p>
                </div>

                <div className="space-y-4">
                  {/* Camera item */}
                  <div className="flex items-center justify-between p-3 bg-dark-900/60 rounded-xl border border-dark-800 text-sm">
                    <div className="flex items-center gap-2.5">
                      <Camera className="h-5 w-5 text-dark-300" />
                      <span>Webcam Configuration</span>
                    </div>
                    {cameraPerm === 'granted' ? (
                      <span className="text-xs text-emerald-400 font-bold">READY</span>
                    ) : (
                      <span className="text-xs text-rose-500 font-bold">REQUIRED</span>
                    )}
                  </div>

                  {/* Microphone item */}
                  <div className="flex items-center justify-between p-3 bg-dark-900/60 rounded-xl border border-dark-800 text-sm">
                    <div className="flex items-center gap-2.5">
                      <Mic className="h-5 w-5 text-dark-300" />
                      <span>Microphone Capture</span>
                    </div>
                    {micPerm === 'granted' ? (
                      <span className="text-xs text-emerald-400 font-bold">READY</span>
                    ) : (
                      <span className="text-xs text-rose-500 font-bold">REQUIRED</span>
                    )}
                  </div>

                  {/* Network item */}
                  <div className="flex items-center justify-between p-3 bg-dark-900/60 rounded-xl border border-dark-800 text-sm">
                    <div className="flex items-center gap-2.5">
                      <Wifi className="h-5 w-5 text-dark-300" />
                      <span>Estimated Network Latency</span>
                    </div>
                    <span className="text-xs text-emerald-400 font-mono font-bold">{latency}</span>
                  </div>
                </div>
              </div>

              {/* Action buttons */}
              <div className="space-y-3 pt-6 border-t border-dark-800">
                <button
                  onClick={handleJoin}
                  disabled={cameraPerm !== 'granted' || micPerm !== 'granted'}
                  className="w-full bg-brand-600 hover:bg-brand-700 disabled:bg-brand-600/40 text-sm font-bold py-3 rounded-xl transition-all glow-indigo flex items-center justify-center gap-2 text-white"
                >
                  <CheckCircle className="h-5 w-5" />
                  Enter Meeting Room
                </button>
                <p className="text-[10px] text-center text-dark-300 leading-relaxed">
                  By joining, you agree to allow <b>InterviewGuard AI</b> to process security parameters including gaze offsets, liveness calculations, and phone visibility.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MeetingCheck;
