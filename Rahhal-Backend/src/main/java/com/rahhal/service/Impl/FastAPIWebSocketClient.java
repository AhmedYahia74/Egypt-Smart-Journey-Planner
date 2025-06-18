package com.rahhal.service.Impl;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.rahhal.entity.Message;
import com.rahhal.repository.ConversationRepository;
import com.rahhal.repository.MessageRepository;
import lombok.extern.slf4j.Slf4j;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Component;

import java.net.URI;
import java.util.Map;

@Slf4j
public class FastAPIWebSocketClient extends WebSocketClient {
    private final String userId;
    private final String conversationId;
    private final SimpMessagingTemplate messagingTemplate;

    private final ConversationRepository conversationRepository;
    private final MessageRepository messageRepository;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public FastAPIWebSocketClient(URI serverUri, String userId, String conversationId, SimpMessagingTemplate messagingTemplate, ConversationRepository conversationRepository, MessageRepository messageRepository) {
        super(serverUri);
        this.userId = userId;
        this.conversationId = conversationId;
        this.messagingTemplate = messagingTemplate;
        this.conversationRepository = conversationRepository;
        this.messageRepository = messageRepository;
    }

    @Override
    public void onOpen(ServerHandshake serverHandshake) {
        log.info("WebSocket connection opened for user: {} in conversation: {}", userId, conversationId);
    }
    private void saveMessage(String message) {
        Message msg = Message.builder()
                .content(message)
                .conversation(conversationRepository.findById(Integer.parseInt(conversationId))
                        .orElseThrow(() -> new RuntimeException("Conversation not found")))
                .build();
        messageRepository.save(msg);
    }
    @Override
    public void onMessage(String message) {
        saveMessage(message);
        log.info("Received message from FastAPI for user: {} in conversation: {}: {}", userId, conversationId, message);
        try {
            // Try to parse as JSON first

            // Forward the message with its original format
            messagingTemplate.convertAndSendToUser(
                    userId,
                    "/queue/conversation/" + conversationId,
                    message,
                    Map.of(
                        "source", "fastapi",
                        "timestamp", String.valueOf(System.currentTimeMillis())
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

