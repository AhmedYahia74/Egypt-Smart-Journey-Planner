package com.rahhal.mapper;

import com.rahhal.dto.TripDto;
import com.rahhal.entity.Trip;
import com.rahhal.entity.User;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;

@Component
public class TripMapper {
    public Trip mapToEntity(TripDto tripDto, User company) {
        return Trip.builder()
                .title(tripDto.getTitle())
                .description(tripDto.getDescription())
                .state(tripDto.getState())
                .price(tripDto.getPrice())
                .date(tripDto.getDate())
                .availableSeats(tripDto.getAvailableSeats())
                .duration(tripDto.getDuration())
                .company(company)
                .build();
    }

    public void updateEntity(TripDto tripDto, Trip existingTrip) {
        existingTrip.setTitle(tripDto.getTitle());
        existingTrip.setDescription(tripDto.getDescription());
        existingTrip.setState(tripDto.getState());
        existingTrip.setPrice(tripDto.getPrice());
        existingTrip.setDate(tripDto.getDate());
        existingTrip.setAvailableSeats(tripDto.getAvailableSeats());
        existingTrip.setDuration(tripDto.getDuration());
    }

}
