package com.rahhal.controller;

import com.rahhal.dto.TripDto;
import com.rahhal.entity.Trip;
import com.rahhal.security.JwtService;
import com.rahhal.service.TripService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;


@RestController
@RequestMapping("/api/trip")
public class TripController {
    private final TripService tripService;

    public TripController(TripService tripService) {
        this.tripService = tripService;
    }

    @PostMapping("/create")
    @PreAuthorize("hasRole('ROLE_COMPANY')")
    public ResponseEntity<Void> createTrip(@Valid @RequestBody TripDto tripDto) {
        try {
            tripService.createTrip(tripDto);
        } catch (Exception e) {
            System.out.println(e.getMessage());
        }
        return ResponseEntity.ok().build();
    }
}
