package com.rahhal.service.Impl;

import com.rahhal.dto.ChatsDTO;
import com.rahhal.repository.ConversationRepository;
import com.rahhal.repository.MessageRepository;
import com.rahhal.service.ChatService;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class ChatServiceImpl implements ChatService {
    private final ConversationRepository conversationRepository;
    private final MessageRepository messageRepository;
    public ChatServiceImpl(ConversationRepository conversationRepository, MessageRepository messageRepository) {
        this.conversationRepository = conversationRepository;
        this.messageRepository = messageRepository;
    }

    @Override
    public List<ChatsDTO> getAllChats(int userId) {
        return conversationRepository.findAllConversationIdsAndTitlesByTouristId(userId);
    }

    @Override
    public List<String> getChatMessages(int conversationId, int userId) {
        return messageRepository.findMessagesByConversationId(conversationId);
    }


}
