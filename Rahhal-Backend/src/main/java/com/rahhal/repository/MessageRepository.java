package com.rahhal.repository;

import com.rahhal.entity.Message;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface MessageRepository extends JpaRepository<Message, Integer> {
    @Query("SELECT m.content FROM Message m WHERE m.conversation.conversationId = :conversationId")
    List<String> findMessagesByConversationId(@Param("conversationId") Integer conversationId);
}
