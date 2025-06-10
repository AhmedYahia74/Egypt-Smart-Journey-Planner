package com.rahhal.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Entity
@Table(name = "company_profiles")
@Data
@NoArgsConstructor @AllArgsConstructor
@Builder
public class CompanyProfile{
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private int companyId;

    private String name;

    private String description;

    @OneToOne
    @JoinColumn(name = "user_id", nullable = false, unique = true)
    private Company company;

    private String stripeAccountId;

    @OneToMany(mappedBy = "company")
    List<Review> reviews;

}
