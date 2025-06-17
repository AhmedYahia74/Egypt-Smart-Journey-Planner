package com.rahhal.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;
import lombok.*;

import java.time.LocalDateTime;
import java.util.List;

@Entity
@Table(name = "trips")
@Data
@NoArgsConstructor @AllArgsConstructor
@Builder
public class Trip {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private int tripId;

    @ManyToOne
    @JoinColumn(name = "company_id", referencedColumnName = "userId", nullable = false)
    private Company company;

    @NotBlank
    @Column(nullable = false)
    private String title;

    @NotBlank
    @Column(nullable = false)
    private String description;

    @NotBlank
    @Column(nullable = false)
    private String state;

    @Positive
    @Column(nullable = false)
    private double price;

    @NotBlank
    private String duration;

    @Column(nullable = false)
    private LocalDateTime date;

    @Column(name = "available_seats", nullable = false)
    private int availableSeats;

    @Column(name = "is_active", nullable = false)
    private Boolean active;

    @Column(name = "is_booked",nullable = false)
    private boolean booked;

    @Column(name = "embedding", columnDefinition = "vector(384)")
    private List<Float> embedding;

    @PrePersist
    public void prePersist() {
        this.active = false;
        this.booked = false;
    }

}
