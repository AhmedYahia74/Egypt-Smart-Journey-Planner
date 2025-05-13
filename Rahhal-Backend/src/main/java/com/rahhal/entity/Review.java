package com.rahhal.entity;
import jakarta.persistence.*;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "reviews")
@NoArgsConstructor @AllArgsConstructor
@Setter @Getter
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
