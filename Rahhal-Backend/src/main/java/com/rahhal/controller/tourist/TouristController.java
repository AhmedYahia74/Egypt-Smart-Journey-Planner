package com.rahhal.controller.tourist;

import com.rahhal.dto.ChatsDTO;
import com.rahhal.dto.ReviewDTO;
import com.rahhal.entity.Conversation;
import com.rahhal.repository.ConversationRepository;
import com.rahhal.repository.UserRepository;
import com.rahhal.service.ChatService;
import com.rahhal.service.ReviewService;
import jakarta.validation.Valid;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.List;

@RestController
@RequestMapping("/api/tourist")
@PreAuthorize("hasRole('ROLE_TOURIST')")
@Slf4j
public class TouristController {

    private final ReviewService reviewService;
    private final ChatService chatService;
    private final UserRepository userRepository;
    private final ConversationRepository conversationRepository;
    public TouristController(ReviewService touristService, ChatService chatService, UserRepository userRepository, ConversationRepository conversationRepository) {
        this.reviewService = touristService;
        this.chatService = chatService;
        this.userRepository = userRepository;
        this.conversationRepository = conversationRepository;
    }

    @PostMapping("/reviews")
    public ResponseEntity<Void> addReview(@Valid @RequestBody ReviewDTO dto) {
        reviewService.addReview(dto);
        return ResponseEntity.status(HttpStatus.CREATED).build();
    }


    @DeleteMapping("/reviews/{reviewId}")
    public ResponseEntity<Void> deleteReview(@PathVariable int reviewId) {
        reviewService.deleteReview(reviewId);
        return ResponseEntity.status(HttpStatus.NO_CONTENT).build();
    }

    @GetMapping("/chats/{userId}")
    public ResponseEntity<List<ChatsDTO>> getChatHistory(@PathVariable int userId) {
        List<ChatsDTO> chats = chatService.getAllChats(userId);
        log.info("Retrieved {} chats for user {}", chats.size(), userId);
        if (chats.isEmpty()) {
            return ResponseEntity.noContent().build();
        }
        return ResponseEntity.ok(chats);
    }

    @GetMapping("/chats/{conversationId}/{userId}")
    public ResponseEntity<List<String>> getChatMessages(@PathVariable int conversationId, @PathVariable int userId) {
        return ResponseEntity.ok(chatService.getChatMessages(conversationId, userId));
    }

    @GetMapping("/new-chats/{userId}")
    public ResponseEntity<Integer> getConversationId(@PathVariable int userId) {
        Conversation conversation = Conversation.builder()
                .title(LocalDate.now().format(DateTimeFormatter.ofPattern("dd-MM-yyyy")))
                .tourist(userRepository.findById(userId)
                        .orElseThrow(() -> new RuntimeException("User not found")))
                .build();
        conversationRepository.save(conversation);
        log.info("New conversation created with ID: {}", conversation.getConversationId());
        return ResponseEntity.ok(conversation.getConversationId());
    }


}
