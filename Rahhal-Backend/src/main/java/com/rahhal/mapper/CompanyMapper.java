package com.rahhal.mapper;

import com.rahhal.dto.CompanyDto;
import com.rahhal.entity.Company;
import org.springframework.stereotype.Component;

@Component
public class CompanyMapper {
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
