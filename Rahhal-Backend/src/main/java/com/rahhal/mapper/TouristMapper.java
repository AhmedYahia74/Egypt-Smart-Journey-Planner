package com.rahhal.mapper;

import com.rahhal.dto.TouristDto;
import com.rahhal.entity.Tourist;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

@Component
public class TouristMapper {
    private final PasswordEncoder passwordEncoder;

    public TouristMapper(PasswordEncoder passwordEncoder) {
        this.passwordEncoder = passwordEncoder;
    }

    public Tourist mapToEntity(TouristDto touristDto) {
        Tourist tourist = new Tourist();
        tourist.setEmail(touristDto.getEmail());
        tourist.setPassword(passwordEncoder.encode(touristDto.getPassword()));
        tourist.setName(touristDto.getName());
        return tourist;
    }
}
