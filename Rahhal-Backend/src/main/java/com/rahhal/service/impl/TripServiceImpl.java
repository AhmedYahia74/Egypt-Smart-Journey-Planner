package com.rahhal.service.impl;

import com.rahhal.dto.BookingRequestDTO;
import com.rahhal.dto.TripDto;
import com.rahhal.entity.Company;
import com.rahhal.entity.Tourist;
import com.rahhal.entity.Trip;
import com.rahhal.exception.EntityNotFoundException;
import com.rahhal.exception.TripAlreadyActivatedException;
import com.rahhal.exception.TripModificationNotAllowedException;
import com.rahhal.mapper.TripMapper;
import com.rahhal.repository.CompanyRepository;
import com.rahhal.repository.TouristRepository;
import com.rahhal.repository.TripRepository;
import com.rahhal.repository.UserRepository;
import com.rahhal.service.StripeService;
import com.rahhal.service.TripService;
import com.stripe.exception.StripeException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;


@Service
public class TripServiceImpl implements TripService {
    private final TripRepository tripRepository;
    private final UserRepository userRepository;
    private final CompanyRepository companyRepository;
    private final TripMapper tripMapper;
    private final TouristRepository touristRepository;
    private final StripeService stripeService;

    TripServiceImpl(TripRepository tripRepository, UserRepository userRepository, CompanyRepository companyRepository, TripMapper tripMapper, TouristRepository touristRepository, StripeService stripeService) {
        this.tripRepository = tripRepository;
        this.userRepository = userRepository;
        this.companyRepository = companyRepository;
        this.tripMapper = tripMapper;
        this.touristRepository = touristRepository;
        this.stripeService = stripeService;
    }
    public UserDetails getCurrentUserDetails() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication != null && authentication.getPrincipal() instanceof UserDetails) {
            return (UserDetails) authentication.getPrincipal();
        }
        throw new AccessDeniedException("Unauthorized access");
    }


    @Override
    public void createTrip(TripDto tripDto ) {
        int userId = userRepository.findByEmail(getCurrentUserDetails().getUsername())
                .orElseThrow(() -> new EntityNotFoundException("Company not found"))
                .getUserId();

        Company company = companyRepository
                .findById(userId).orElseThrow(() -> new EntityNotFoundException("Company not found"));

        Trip trip = tripMapper.mapToEntity(tripDto, company);

        tripRepository.save(trip);
    }


    @Override
    public TripDto updateTrip(int tripId, TripDto tripDto) {
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

        tripMapper.updateEntity(tripDto, trip);

        tripRepository.save(trip);
        return tripMapper.mapToDto(trip);
    }

    @Override
    public void deleteTrip(int tripId) {
        Trip trip=tripRepository.findById(tripId)
                .orElseThrow(() -> new EntityNotFoundException("Trip not found"));

        int userId = companyRepository.findByEmail(getCurrentUserDetails().getUsername())
                .orElseThrow(() -> new EntityNotFoundException("Company not found"))
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

    @Override
    public List<TripDto> viewTripsForCurrentCompany() {
        int userId=userRepository.findByEmail(getCurrentUserDetails().getUsername())
                .orElseThrow(() -> new EntityNotFoundException("User not found"))
                .getUserId();

        Company company = companyRepository.findById(userId)
                .orElseThrow(() -> new EntityNotFoundException("User not found"));

        return tripRepository.findTripByCompany(company);
    }

    @Override
    public List<TripDto> viewAllActiveTrips() {
        return tripRepository.findByActiveTrue();
    }

    @Override
    @Transactional
    public String bookTrip(BookingRequestDTO bookingRequest) throws StripeException {
        Trip trip = tripRepository.findById(bookingRequest.getTripId())
                .orElseThrow(() -> new EntityNotFoundException("Trip not found"));

        if (!isTripAvailable(trip, bookingRequest.getNumberOfTickets())) {
            throw new EntityNotFoundException("Not enough available seats for this trip");
        }

        Tourist tourist = touristRepository.findByEmail(getCurrentUserDetails().getUsername())
                .orElseThrow(() -> new EntityNotFoundException("Tourist not found"));

        bookingRequest.setTrip(trip);
        bookingRequest.setTourist(tourist);

        trip.setAvailableSeats(trip.getAvailableSeats() - bookingRequest.getNumberOfTickets());
        trip.setBooked(true);
        tripRepository.save(trip);

        return stripeService.createSession(bookingRequest);
    }

    @Override
    public List<TripDto> viewAllInactiveTrips() {
        return tripRepository.findByActiveFalse();
    }

    @Override
    public List<TripDto> viewInactiveTripsForCompany(int companyId) {
        return tripRepository.findByActiveFalseAndCompany_UserId(companyId);
    }

    @Override
    public void activeTrip(int tripId) {

        Trip trip = tripRepository.findById(tripId)
                .orElseThrow(() -> new EntityNotFoundException("Trip not found"));

        if (trip.getActive()) {
            throw new TripAlreadyActivatedException("Trip is already activated");
        }
        trip.setActive(true);
        tripRepository.save(trip);
    }

    @Override
    public void deleteInactiveTrip(int tripId) {
        Trip trip=tripRepository.findById(tripId)
                .orElseThrow(()->new EntityNotFoundException("Trip not found"));

        if (trip.getActive())
            throw new TripModificationNotAllowedException("Can't delete this trip is activated");

        tripRepository.delete(trip);

    }

    boolean isTripAvailable(Trip trip, int numberOfTickets) {
        return (trip.getActive() && trip.getAvailableSeats() >= numberOfTickets);
    }
}

