package com.rahhal.controller.tourist;

import com.rahhal.dto.ReviewDTO;
import com.rahhal.service.ReviewService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/tourist")
@PreAuthorize("hasRole('ROLE_TOURIST')")
public class TouristController {

    private final ReviewService reviewService;

    public TouristController(ReviewService touristService) {
        this.reviewService = touristService;
    }

    @PostMapping("/reviews")
    public ResponseEntity<Void> addReview(@Valid @RequestBody ReviewDTO dto)
    {
        reviewService.addReview(dto);
        return ResponseEntity.status(HttpStatus.CREATED).build();
    }


    @DeleteMapping("/reviews/{reviewId}")
    public ResponseEntity<Void> deleteReview(@PathVariable int reviewId)
    {
        reviewService.deleteReview(reviewId);
        return ResponseEntity.status(HttpStatus.NO_CONTENT).build();
    }

}
