package com.rahhal.mapper;

import com.rahhal.dto.ReviewDTO;
import com.rahhal.entity.CompanyProfile;
import com.rahhal.entity.Review;
import com.rahhal.entity.User;
import org.springframework.stereotype.Component;

@Component
public class ReviewMapper {

    public Review toEntity(ReviewDTO reviewDTO, User tourist, CompanyProfile company) {
        return Review.builder()
                .comment(reviewDTO.getComment())
                .rating(reviewDTO.getRating())
                .tourist(tourist)
                .company(company)
                .build();
    }

    public ReviewDTO toDTO(Review review) {
        return ReviewDTO.builder()
                .companyName(review.getCompany().getName())
                .comment(review.getComment())
                .rating(review.getRating())
                .build();
    }
}
