package com.rahhal.entity;
import com.rahhal.dto.CompanyProfileDTO;
import jakarta.persistence.*;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.*;

@Entity
@Table(name = "reviews")
@NoArgsConstructor @AllArgsConstructor
@Setter @Getter
@Builder
public class Review {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private int reviewId;

    private String comment;

    @Min(1) @Max(5)
    private int rating;

    @ManyToOne
    @JoinColumn(name = "tourist_id")
    private User tourist;

    @ManyToOne
    @JoinColumn(name = "company_id")
    private CompanyProfile company;

}
