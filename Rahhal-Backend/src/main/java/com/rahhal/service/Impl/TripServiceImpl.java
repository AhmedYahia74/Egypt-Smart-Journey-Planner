package com.rahhal.service.Impl;

import com.rahhal.dto.EmbeddingDTO;
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
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;


@Service
public class TripServiceImpl implements TripService {
    private final TripRepository tripRepository;
    private final UserRepository userRepository;
    private final CompanyRepository companyRepository;
    private final TripMapper tripMapper;

    TripServiceImpl(TripRepository tripRepository, UserRepository userRepository, CompanyRepository companyRepository, TripMapper tripMapper) {
        this.tripRepository = tripRepository;
        this.userRepository = userRepository;
        this.companyRepository = companyRepository;
        this.tripMapper = tripMapper;
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

        WebClient webClient = WebClient.builder()
                .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .build();

        EmbeddingDTO embeddingDTO = EmbeddingDTO.builder()
                .embeddingData(tripDto.getDescription())
                .build();

        var response=webClient.post()
                .uri("http://localhost:8001/api/embeddings/text")
                .bodyValue(embeddingDTO)
                .retrieve()
                .bodyToMono(Map.class)
                .block();

        List<Double> embeddingRaw = (List<Double>) response.get("embedding");

        List<Float> embedding = embeddingRaw.stream()
                .map(Double::floatValue)
                .collect(Collectors.toList());

        trip.setEmbedding(embedding);


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

        Trip trip=tripRepository.findById(tripId)
                .orElseThrow(() -> new EntityNotFoundException("Trip not found"));

        if(trip.getActive())
        {
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
}

