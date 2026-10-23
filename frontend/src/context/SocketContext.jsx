import React, { createContext, useContext, useState, useEffect } from 'react';
import { io } from 'socket.io-client';
import { useAuth } from './AuthContext';

const SocketContext = createContext(null);

export const SocketProvider = ({ children }) => {
  const { token } = useAuth();
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // VITE_SOCKET_URL is required when frontend and backend are separate Render services.
    let socketUrl = import.meta.env.VITE_SOCKET_URL || (
      import.meta.env.DEV ? 'http://127.0.0.1:8000' : window.location.origin
    );
    if (!import.meta.env.DEV && socketUrl.startsWith('http://')) {
      console.error('Insecure VITE_SOCKET_URL in production; upgrading it to HTTPS.');
      socketUrl = socketUrl.replace(/^http:\/\//, 'https://');
    }
    const newSocket = io(socketUrl, {
      autoConnect: false,
      transports: ['websocket', 'polling'],
      auth: { token }
    });

    setSocket(newSocket);

    newSocket.on('connect', () => {
      setConnected(true);
      console.log('Socket.IO connected:', newSocket.id);
    });

    newSocket.on('disconnect', () => {
      setConnected(false);
      console.log('Socket.IO disconnected');
    });

    return () => {
      newSocket.close();
    };
  }, [token]);

  const connectSocket = () => {
    if (socket && !socket.connected) {
      socket.connect();
    }
  };

  const disconnectSocket = () => {
    if (socket && socket.connected) {
      socket.disconnect();
    }
  };

  const value = {
    socket,
    connected,
    connectSocket,
    disconnectSocket
  };

  return (
    <SocketContext.Provider value={value}>
      {children}
    </SocketContext.Provider>
  );
};

export const useSocket = () => {
  const context = useContext(SocketContext);
  if (!context) {
    throw new Error('useSocket must be used within a SocketProvider');
  }
  return context;
};
