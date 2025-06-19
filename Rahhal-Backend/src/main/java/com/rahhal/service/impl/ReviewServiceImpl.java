package com.rahhal.service.impl;

import com.rahhal.dto.ReviewDTO;
import com.rahhal.entity.CompanyProfile;
import com.rahhal.entity.Review;
import com.rahhal.entity.User;
import com.rahhal.exception.EntityNotFoundException;
import com.rahhal.mapper.ReviewMapper;
import com.rahhal.repository.CompanyProfileRepository;
import com.rahhal.repository.CompanyRepository;
import com.rahhal.repository.ReviewRepository;
import com.rahhal.repository.UserRepository;
import com.rahhal.service.ReviewService;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;

@Service
public class ReviewServiceImpl implements ReviewService {

    private final ReviewRepository reviewRepository;
    private final UserRepository userRepository;
    private final CompanyProfileRepository companyProfileRepository;
    private final ReviewMapper reviewMapper;
    private final CompanyRepository companyRepository;

    public ReviewServiceImpl(ReviewRepository reviewRepository, UserRepository userRepository,
                             CompanyProfileRepository companyProfileRepository, ReviewMapper reviewMapper, CompanyRepository companyRepository) {
        this.reviewRepository = reviewRepository;
        this.userRepository = userRepository;
        this.companyProfileRepository = companyProfileRepository;
        this.reviewMapper = reviewMapper;
        this.companyRepository = companyRepository;
    }

    private UserDetails getCurrentUserDetails() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication != null && authentication.getPrincipal() instanceof UserDetails) {
            return (UserDetails) authentication.getPrincipal();
        }
        throw new AccessDeniedException("Unauthorized access");
    }

    @Override
    public void addReview(ReviewDTO reviewDTO) {
        User tourist = userRepository.findByEmail(getCurrentUserDetails().getUsername())
                .orElseThrow(() -> new EntityNotFoundException("Tourist not found"));

       CompanyProfile company =  companyProfileRepository.findByName(reviewDTO.getCompanyName())
               .orElseThrow(() -> new EntityNotFoundException("Company not found"));

        Review review = reviewMapper.mapToEntity(reviewDTO, tourist, company);
        reviewRepository.save(review);
    }


    @Override
    public void deleteReview(int reviewId) {
        Review review = reviewRepository.findById(reviewId)
                .orElseThrow(() -> new EntityNotFoundException("Review not found"));

        int userId = userRepository.findByEmail(getCurrentUserDetails().getUsername())
                .orElseThrow(() -> new EntityNotFoundException("Tourist not found"))
                .getUserId();

        if(review.getTourist().getUserId()!=userId)
        {throw new AccessDeniedException("You are not allowed to delete this review");}

        reviewRepository.delete(review);
    }

}
