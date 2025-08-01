package com.rahhal.controller.tourist;

import com.rahhal.entity.Conversation;
import com.rahhal.entity.Tourist;
import com.rahhal.repository.ConversationRepository;
import com.rahhal.repository.MessageRepository;
import com.rahhal.service.impl.FastAPIWebSocketClient;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.messaging.handler.annotation.DestinationVariable;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Controller;

import java.net.URI;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;


@Controller
@RequiredArgsConstructor
@Slf4j
public class ChatBotController {
    private final SimpMessagingTemplate messagingTemplate;
    // Map to store connections: key = "userId:conversationId"
    private final Map<String, FastAPIWebSocketClient> clientMap = new ConcurrentHashMap<>();
    private final Map<String, Boolean> connectionStatus = new ConcurrentHashMap<>();
    private final ConversationRepository conversationRepository;
    private final MessageRepository messageRepository;
    @MessageMapping("/chatbot/send/{userId}/{conversationId}")
    public void handleMessage(@DestinationVariable String userId,
                            @DestinationVariable String conversationId,
                            String message) {


        String connectionKey = userId + ":" + conversationId;
        
        try {
            log.info("Received message from user: {} in conversation: {}: {}", userId, conversationId, message);

            FastAPIWebSocketClient client = clientMap.computeIfAbsent(connectionKey, key -> {
                try {
                    URI fastApiUri = new URI("ws://localhost:8000/ws/" + conversationId);
                    FastAPIWebSocketClient newClient = new FastAPIWebSocketClient(fastApiUri, userId, conversationId, messagingTemplate, conversationRepository, messageRepository);
                    boolean connected = newClient.connectBlocking();
                    connectionStatus.put(key, connected);
                    if (!connected) {
                        throw new RuntimeException("Failed to connect to FastAPI");
                    }
                    log.info("Successfully connected to FastAPI for user: {} conversation: {}", userId, conversationId);
                    return newClient;
                } catch (Exception e) {
                    log.error("Error creating FastAPI client for user: {} conversation: {}", userId, conversationId, e);
                    throw new RuntimeException("Failed to create FastAPI client: " + e.getMessage());
                }
            });

            // 3. Send message using existing connection
            if (connectionStatus.getOrDefault(connectionKey, false) && client.isOpen()) {
                client.send(message);
                log.info("Message sent successfully for user: {} conversation: {}", userId, conversationId);
            } else {
                // Try to reconnect if connection is lost
                boolean reconnected = client.reconnectBlocking();
                connectionStatus.put(connectionKey, reconnected);
                if (reconnected) {
                    client.send(message);
                    log.info("Reconnected and message sent successfully for user: {} conversation: {}", userId, conversationId);
                } else {
                    throw new RuntimeException("Failed to reconnect to FastAPI");
                }
            }

        } catch (Exception e) {
            log.error("Error handling message for user: {} conversation: {}", userId, conversationId, e);
            messagingTemplate.convertAndSendToUser(
                    userId,
                    "/queue/conversation/" + conversationId,
                    "Error: " + e.getMessage()
            );
        }
    }

}
