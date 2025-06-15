package com.rahhal.service.Impl;

import com.rahhal.dto.TripDto;
import com.rahhal.entity.Company;
import com.rahhal.entity.Trip;
import com.rahhal.entity.User;
import com.rahhal.exception.CompanyHasNoInactiveTripsExeption;
import com.rahhal.exception.EntityNotFoundException;
import com.rahhal.exception.TripAlreadyActivatedException;
import com.rahhal.exception.TripModificationNotAllowedException;
import com.rahhal.mapper.TripMapper;
import com.rahhal.repository.CompanyRepository;
import com.rahhal.repository.TripRepository;
import com.rahhal.repository.UserRepository;
import com.rahhal.service.TripService;
import com.rahhal.service.EmailService;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;
import org.springframework.security.access.AccessDeniedException;

import java.util.List;


@Service
public class TripServiceImpl implements TripService {
    private final TripRepository tripRepository;
    private final UserRepository userRepository;
    private final CompanyRepository companyRepository;
    private final TripMapper tripMapper;
    private final EmailService emailService;

    TripServiceImpl(TripRepository tripRepository, UserRepository userRepository, CompanyRepository companyRepository, TripMapper tripMapper, EmailService emailService) {
        this.tripRepository = tripRepository;
        this.userRepository = userRepository;
        this.companyRepository = companyRepository;
        this.tripMapper = tripMapper;
        this.emailService = emailService;
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
    public List<TripDto> viewTrip() {
        int userId=userRepository.findByEmail(getCurrentUserDetails().getUsername())
                .orElseThrow(() -> new EntityNotFoundException("User not found"))
                .getUserId();


        Company company = companyRepository.findById(userId)
                .orElseThrow(() -> new EntityNotFoundException("User not found"));


        List<TripDto> trips=tripRepository.findTripByCompany(company);
        return trips;
    }

    @Override
    public List<TripDto> viewAllInactiveTrips() {
        List<TripDto>trips = tripRepository.findByActiveFalse();
        return trips;
    }

    @Override
    public List<TripDto> viewInactiveTripsForCompany(int companyId) {
        List<TripDto> trips=tripRepository.findByActiveFalseAndCompany_UserId(companyId);
        if(trips.size()==0)
        {
            throw new CompanyHasNoInactiveTripsExeption("Company Has No Inactive Trips");
        }
        return trips;
    }

    @Override
    public void activeTrip(int tripId) {

        Trip trip = tripRepository.findById(tripId)
                .orElseThrow(() -> new EntityNotFoundException("Trip not found"));

        if(trip.getActive())
        {
            throw new TripAlreadyActivatedException("Trip is already activated");
        }

        trip.setActive(true);
        tripRepository.save(trip);

        String subject = "Trip Successfully Approved and Active on Rahhal";
        String body = String.format("""
            <div style="font-family: Arial, sans-serif; font-size: 18px; line-height: 1.5; color: #000000;">
                <p>Dear <strong>%s</strong>,</p>
                
                <p>Your trip [ <strong>%s</strong> ] has been successfully activated by the admin.</p>
                <p>The trip is now visible to tourists and available for booking.</p>
                
                <p>Best regards,<br>
                <strong>Rahhal Team</strong></p>
            </div>
            """,
            trip.getCompany().getName(),
            trip.getTitle());

        emailService.sendEmail(trip.getCompany().getEmail(), subject, body);
    }

    @Override
    public void deleteInactiveTrip(int tripId) {
        Trip trip=tripRepository.findById(tripId)
                .orElseThrow(()->new EntityNotFoundException("Trip not found"));

        if (trip.getActive())
            throw new TripModificationNotAllowedException("Can't delete this trip is activated");

        tripRepository.delete(trip);

    }
}

