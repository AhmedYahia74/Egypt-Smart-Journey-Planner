package com.rahhal.dto;

import com.rahhal.entity.Review;
import lombok.Builder;
import lombok.Data;

import java.util.List;

@Data @Builder
public class CompanyProfileDTO {
    private String companyName;
    private String description;
    private List<ReviewResponseDTO> reviews;
}
