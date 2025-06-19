package com.rahhal.dto;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class ReviewDTO {

        private String companyName;
        private String touristName;
        private String comment;
        private int rating;

}
