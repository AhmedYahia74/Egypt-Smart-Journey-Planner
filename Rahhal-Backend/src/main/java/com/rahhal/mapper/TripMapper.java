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
                .date(tripDto.getDate().atStartOfDay())
                .availableSeats(tripDto.getAvailableSeats())
                .build();
    }
}
