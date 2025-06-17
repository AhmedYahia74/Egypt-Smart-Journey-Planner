package com.rahhal.service.Impl;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;
import org.springframework.messaging.simp.SimpMessagingTemplate;

import java.net.URI;
import java.util.Map;

@Slf4j
public class FastAPIWebSocketClient extends WebSocketClient {
    private final String userId;
    private final String conversationId;
    private final SimpMessagingTemplate messagingTemplate;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public FastAPIWebSocketClient(URI serverUri, String userId, String conversationId, SimpMessagingTemplate messagingTemplate) {
        super(serverUri);
        this.userId = userId;
        this.conversationId = conversationId;
        this.messagingTemplate = messagingTemplate;
    }

    @Override
    public void onOpen(ServerHandshake serverHandshake) {
        log.info("WebSocket connection opened for user: {} in conversation: {}", userId, conversationId);
    }

    @Override
    public void onMessage(String message) {
        log.info("Received message from FastAPI for user: {} in conversation: {}: {}", userId, conversationId, message);
        try {
            // Try to parse as JSON first
            Object messageContent;
            try {
                messageContent = objectMapper.readValue(message, Object.class);
            } catch (Exception e) {
                // If not JSON, use as string
                messageContent = message;
            }

            // Forward the message with its original format
            messagingTemplate.convertAndSendToUser(
                    userId,
                    "/queue/conversation/" + conversationId,
                    messageContent,
                    Map.of(
                        "source", "fastapi",
                        "timestamp", String.valueOf(System.currentTimeMillis()),
                        "isJson", String.valueOf(messageContent instanceof Map)
                    )
            );
            log.info("Forwarded message to user: {} in conversation: {}", userId, conversationId);
        } catch (Exception e) {
            log.error("Error processing message from FastAPI: {}", e.getMessage());
        }
    }

    @Override
    public void onClose(int i, String s, boolean b) {
        log.info("WebSocket connection closed for user: {} in conversation: {}. Code: {}, Reason: {}, Remote: {}",
                userId, conversationId, i, s, b);
    }

    @Override
    public void onError(Exception e) {
        log.error("WebSocket error for user: {} in conversation: {}: {}", userId, conversationId, e.getMessage());
    }
}

