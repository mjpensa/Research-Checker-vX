'use client'

import { useEffect, useState, useCallback, useRef } from 'react'

interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
}

export function useWebSocket(pipelineId?: string) {
  const [messages, setMessages] = useState<WebSocketMessage[]>([])
  const [connected, setConnected] = useState(false)
  const socketRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    if (!pipelineId) return

    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'
    const url = `${wsUrl}/ws/pipelines/${pipelineId}`

    const connect = () => {
      try {
        const socket = new WebSocket(url)
        socketRef.current = socket

        socket.onopen = () => {
          console.log('WebSocket connected')
          setConnected(true)
        }

        socket.onclose = () => {
          console.log('WebSocket disconnected')
          setConnected(false)

          // Attempt to reconnect after 3 seconds
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect...')
            connect()
          }, 3000)
        }

        socket.onerror = (error) => {
          console.error('WebSocket error:', error)
        }

        socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)

            const message: WebSocketMessage = {
              type: data.type || 'message',
              data: data,
              timestamp: new Date().toISOString(),
            }

            setMessages((prev) => [...prev, message])
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error)
          }
        }
      } catch (error) {
        console.error('Failed to create WebSocket:', error)
      }
    }

    connect()

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (socketRef.current) {
        socketRef.current.close()
      }
    }
  }, [pipelineId])

  const sendMessage = useCallback((type: string, data: any) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type, ...data }))
    }
  }, [])

  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  return {
    messages,
    connected,
    sendMessage,
    clearMessages,
  }
}
