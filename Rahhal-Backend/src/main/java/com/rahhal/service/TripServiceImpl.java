package com.rahhal.service;

import com.rahhal.dto.TripDto;
import com.rahhal.entity.Trip;
import com.rahhal.entity.User;
import com.rahhal.exception.EntityNotFoundException;
import com.rahhal.exception.TripModificationNotAllowedException;
import com.rahhal.repository.TripRepository;
import com.rahhal.repository.UserRepository;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;
import org.springframework.security.access.AccessDeniedException;


@Service
public class TripServiceImpl implements TripService {
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
        throw new AccessDeniedException("Unauthorized access");
    }


    @Override
    public void createTrip(TripDto tripDto ){
        int userId = userRepository.findByEmail(getCurrentUserDetails().getUsername())
                .orElseThrow(() -> new EntityNotFoundException("User not found"))
                .getUserId();

        User company = userRepository.findById(userId)
                .orElseThrow(() -> new EntityNotFoundException("User not found"));

        Trip trip = Trip.builder()
                .company(company)
                .title(tripDto.getTitle())
                .description(tripDto.getDescription())
                .state(tripDto.getState())
                .price(tripDto.getPrice())
                .date(tripDto.getDate().atStartOfDay())
                .availableSeats(tripDto.getAvailableSeats())
                .build();

        tripRepository.save(trip);
    }


    @Override
    public Trip updateTrip(int tripId, TripDto tripDto) {
        int userId = userRepository.findByEmail(getCurrentUserDetails().getUsername())
                .orElseThrow(() -> new EntityNotFoundException("User not found"))
                .getUserId();

        Trip trip = tripRepository.findById(tripId)
                .orElseThrow(() -> new EntityNotFoundException("Trip not found"));


        if (trip.getCompany().getUserId() != userId) {
            throw new AccessDeniedException("Unauthorized to update this trip");
        }

        if(trip.isBooked())
        {
            throw new TripModificationNotAllowedException("Can't update the trip is booked");
        }

        trip.setTitle(tripDto.getTitle());
        trip.setDescription(tripDto.getDescription());
        trip.setState(tripDto.getState());
        trip.setPrice(tripDto.getPrice());
        trip.setDate(tripDto.getDate().atStartOfDay());
        trip.setAvailableSeats(tripDto.getAvailableSeats());

        return tripRepository.save(trip);
    }

    @Override
    public void deleteTrip(int tripId) {
        Trip trip=tripRepository.findById(tripId)
                .orElseThrow(() -> new EntityNotFoundException("Trip not found"));

        int userId = userRepository.findByEmail(getCurrentUserDetails().getUsername())
                .orElseThrow(() -> new EntityNotFoundException("User not found"))
                .getUserId();

        if (trip.getCompany().getUserId() != userId) {
            throw new AccessDeniedException("Unauthorized to update this trip");
        }

        if(trip.isBooked())
        {
            throw new TripModificationNotAllowedException("Can't delete the trip is booked");
        }

        tripRepository.delete(trip);
    }
}

