package com.rahhal.service.Impl;


import lombok.extern.slf4j.Slf4j;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;
import org.springframework.messaging.simp.SimpMessagingTemplate;

import java.net.URI;

@Slf4j
public class FastAPIWebSocketClient extends WebSocketClient {
    private final String userId;
    private final String conversationId;
    private final SimpMessagingTemplate messagingTemplate;

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
        messagingTemplate.convertAndSendToUser(
                userId,
                "/queue/conversation/" + conversationId,
                message
        );
    }

    @Override
    public void onClose(int i, String s, boolean b) {
        log.info("WebSocket connection closed for user: {} in conversation: {}. Code: {}, Reason: {}, Remote: {}",
                userId, conversationId, i, s, b);
    }

    @Override
    public void onError(Exception e) {
        System.out.println(e.getMessage());
    }
}

