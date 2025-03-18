package com.rahhal.service;

import com.rahhal.dto.TripDto;
import com.rahhal.entity.Trip;
import com.rahhal.entity.User;
import com.rahhal.enums.UserRole;
import com.rahhal.exception.EntityNotFoundException;
import com.rahhal.repository.TripRepository;
import com.rahhal.repository.UserRepository;
import com.rahhal.security.JwtService;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
public class TripServiceImpl implements TripService{
    private final TripRepository tripRepository;
    private final UserRepository userRepository;

    TripServiceImpl(TripRepository tripRepository, UserRepository userRepository) {
        this.tripRepository = tripRepository;
        this.userRepository = userRepository;
    }
    public UserDetails getCurrentUserDetails() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication != null && authentication.getPrincipal() instanceof UserDetails) {
            return (UserDetails) authentication.getPrincipal();
        }
        throw new RuntimeException("Unauthorized access");
    }


    @Override
    public Trip createTrip(TripDto tripDto ){
        int userId = userRepository.findByEmail(getCurrentUserDetails().getUsername())
                .orElseThrow(() -> new EntityNotFoundException("User not found"))
                .getUserId();

        User company = userRepository.findById(userId)
                .orElseThrow(() -> new EntityNotFoundException("User not found"));

        if (!company.getRole().equals(UserRole.COMPANY)) {
            throw new RuntimeException("User is not a company");
        }

        Trip trip = Trip.builder()
                .company(company)
                .title(tripDto.getTitle())
                .description(tripDto.getDescription())
                .state(tripDto.getState())
                .price(tripDto.getPrice())
                .date(tripDto.getDate().atStartOfDay())
                .availableSeats(tripDto.getAvailableSeats())
                .active(tripDto.getActive())
                .build();

        return tripRepository.save(trip);
    }
}
