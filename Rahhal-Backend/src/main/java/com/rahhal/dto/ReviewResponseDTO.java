package com.rahhal.dto;

import lombok.Builder;
import lombok.Data;

@Data @Builder
public class ReviewResponseDTO {

    private String touristName;
    private String comment;
    private int rating;

}
