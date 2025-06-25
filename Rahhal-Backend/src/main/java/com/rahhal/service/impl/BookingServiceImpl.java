package com.rahhal.service.impl;

import com.rahhal.dto.BookingDto;
import com.rahhal.entity.Trip;
import com.rahhal.entity.User;
import com.rahhal.exception.EntityNotFoundException;
import com.rahhal.repository.BookingRepository;
import com.rahhal.repository.TripRepository;
import com.rahhal.repository.UserRepository;
import com.rahhal.service.BookingService;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class BookingServiceImpl implements BookingService {

    private final BookingRepository bookingRepository;
    private final TripRepository tripRepository;
    private final UserRepository userRepository;

    public BookingServiceImpl(BookingRepository bookingRepository,
                              TripRepository tripRepository, UserRepository userRepository) {
        this.bookingRepository = bookingRepository;
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
    private User getCurrentUser() {
        return userRepository.findByEmail(getCurrentUserDetails().getUsername())
                .orElseThrow(() -> new EntityNotFoundException("User not found"));
    }
    @Override
    public List<BookingDto> getBookings(int tripId) {
        int userId = getCurrentUser().getUserId();

        Trip trip = tripRepository.findById(tripId)
                .orElseThrow(() -> new EntityNotFoundException("Trip not found"));

        if (trip.getCompany().getUserId() != userId) {
            throw new AccessDeniedException("You don't have access to view bookings for this trip");
        }

        return bookingRepository.findByTrip(trip);
    }
}
