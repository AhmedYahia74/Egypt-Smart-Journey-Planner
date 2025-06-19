package com.rahhal.service;

import com.rahhal.dto.ChatsDTO;

import java.util.List;

public interface ChatService {

    List<ChatsDTO> getAllChats(int userId);

    List<String> getChatMessages(int conversationId, int userId);
}
