package com.rahhal.mapper;

import com.rahhal.dto.CompanyDto;
import com.rahhal.entity.Company;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

@Component
public class CompanyMapper {
    private final PasswordEncoder passwordEncoder;

    public CompanyMapper(PasswordEncoder passwordEncoder) {this.passwordEncoder = passwordEncoder;}

    public Company mapToEntity(CompanyDto companyDto)
    {
        return Company.builder()
                .name(companyDto.getName())
                .email(companyDto.getEmail())
                .password(companyDto.getPassword())
                .subscriptionExpireDate(companyDto.getSubscriptionExpired())
                .description(companyDto.getDescription())
                .build();
    }

}
