package com.rahhal.entity;

import jakarta.persistence.DiscriminatorValue;
import jakarta.persistence.Entity;
import lombok.*;
import lombok.experimental.SuperBuilder;

@Entity
@DiscriminatorValue("TOURIST")
@Getter
@Setter
@NoArgsConstructor
@SuperBuilder
public class Tourist extends User {
    // Add any tourist-specific fields here
}
