package com.rahhal.entity;

import jakarta.persistence.*;
import lombok.*;
import lombok.experimental.SuperBuilder;

import java.time.LocalDateTime;

@Entity
@Getter @Setter
@SuperBuilder
@AllArgsConstructor @NoArgsConstructor
@DiscriminatorValue("COMPANY")
public class Company extends User {

    @Column(name = "subscription_expire_date")
    private LocalDateTime subscriptionExpireDate;

    private String description;

    @OneToOne(mappedBy = "company", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    private CompanyProfile companyProfile;
}
