package com.rahhal.repository;

import com.rahhal.dto.ChatsDTO;
import com.rahhal.entity.Conversation;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ConversationRepository extends JpaRepository<Conversation, Integer> {
    @Query("SELECT new com.rahhal.dto.ChatsDTO(c.conversationId, c.title) FROM Conversation c WHERE c.tourist.userId = :touristId")
    List<ChatsDTO> findAllConversationIdsAndTitlesByTouristId(@Param("touristId") Integer touristId);
}
