package com.rahhal.controller;

import com.rahhal.dto.ReviewDTO;
import com.rahhal.service.ReviewService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/tourist")
@PreAuthorize("hasRole('ROLE_TOURIST')")
public class TouristController {

    private final ReviewService touristService;

    public TouristController(ReviewService touristService) {
        this.touristService = touristService;
    }

    @PostMapping("/reviews")
    public ResponseEntity<String> addReview(@Valid @RequestBody ReviewDTO dto)
    {
        touristService.addReview(dto);
        return ResponseEntity.ok("Review submitted successfully.");
    }
}
