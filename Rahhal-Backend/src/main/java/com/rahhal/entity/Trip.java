package com.rahhal.entity;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

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
    private User company;

    @Column(nullable = false)
    private String title;

    @Column(nullable = false)
    private String description;

    @Column(nullable = false)
    private String state;

    @Column(nullable = false)
    private double price;

    @Column(nullable = false)
    private LocalDateTime date;

    @Column(name = "available_seats", nullable = false)
    private int availableSeats;

    @Column(name = "is_active", nullable = false)
    private Boolean active;
}
