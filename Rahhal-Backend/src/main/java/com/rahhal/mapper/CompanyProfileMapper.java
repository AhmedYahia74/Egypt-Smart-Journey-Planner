package com.rahhal.mapper;

import com.rahhal.dto.CompanyDto;
import com.rahhal.dto.CompanyProfileDTO;
import com.rahhal.dto.ReviewDTO;
import com.rahhal.dto.ReviewResponseDTO;
import com.rahhal.entity.Company;
import com.rahhal.entity.CompanyProfile;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.stream.Collectors;

@Component
public class CompanyProfileMapper {

    private final ReviewMapper reviewMapper;

    public CompanyProfileMapper(ReviewMapper reviewMapper) {
        this.reviewMapper = reviewMapper;
    }

    public CompanyProfile mapToEntity(CompanyDto companyDto, Company company) {
        return CompanyProfile.builder()
                .name(companyDto.getName())
                .userId(company.getUserId())
                .description(companyDto.getDescription())
                .build();
    }

    public CompanyProfileDTO mapToDto(CompanyProfile companyProfile) {
        List<ReviewResponseDTO> reviewDTOs = companyProfile.getReviews()
                .stream()
                .map(review -> reviewMapper.mapToResponseDTO(review))  // Inject and use reviewMapper instance
                .collect(Collectors.toList());


        return CompanyProfileDTO.builder()
                .companyName(companyProfile.getName())
                .description(companyProfile.getDescription())
                .reviews(reviewDTOs)
                .build();
    }
}
