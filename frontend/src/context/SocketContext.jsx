import React, { createContext, useContext, useState, useEffect } from 'react';
import { io } from 'socket.io-client';

const SocketContext = createContext(null);

export const SocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // Same-origin by default: works locally and after Railway deployment.
    const socketUrl = import.meta.env.VITE_SOCKET_URL || (
      import.meta.env.DEV ? 'http://127.0.0.1:8000' : window.location.origin
    );
    const newSocket = io(socketUrl, {
      autoConnect: false,
      transports: ['websocket', 'polling']
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
  }, []);

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
